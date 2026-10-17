"""Per-model memory profile for the production ScamShield models.

Measurement only. No model, weight, threshold, or fusion setting is changed.

Method, chosen to match the candidate benchmark recorded in docs/LICENSES.md:
one fresh Python process per model, RSS from psutil, and the Windows high-water
working set (`peak_wset`). Values are MiB rounded to one decimal.

Load path: the lazy singleton used in production, that is
`scamshield.models.transformer.score` and `scamshield.models.lstm.score`, both of
which call the module `_get_model()` builder on their first use. Because the
first production call performs load and inference together, "after load" is
ambiguous, so two stage sets are reported per model:

- staged: `_get_model()` is called and measured on its own (no inference yet),
  then the first `score()` call is measured separately.
- first-call: nothing is preloaded. One `score()` call does load plus inference,
  which is the production first-request path.

A combined mode is reported as well, because the API process holds both models at
once. One fresh process imports both modules, loads each model in turn, and
records peak after the first inference of each. The shared transformers import is
paid once there, so the combined figure must not be taken as the sum of the two
separate peaks.

Stage readings come from the same process, and `peak_wset` is a per-process high
water mark that never decreases. Differences between consecutive `peak_wset`
readings are therefore the useful figure: growth attributable to load, then
growth attributable to the first inference.

Inputs are fixed synthetic strings built from repeated placeholder words. No real
message text is used, printed, or stored.

Usage:
    python scripts/profile_model_memory.py
    python scripts/profile_model_memory.py --model transformer
    python scripts/profile_model_memory.py --model both

Requires psutil, which is a development-only dependency:
    pip install -r requirements-dev.txt
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import sys
import time

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
MARKER = "PROFILE_JSON: "
MIB = 1024 * 1024
MODELS = ("transformer", "lstm")
SINGLE_MODES = ("staged", "first-call")
COMBINED_MODE = "combined"
COMBINED_LABEL = "both"
INSTALL_HINT = (
    "psutil is required for this profile and is a development-only dependency: "
    "pip install -r requirements-dev.txt"
)
WORD_COUNTS = (40, 100)
TOTAL_INFERENCES = 50
WARMUP_RUNS = 1
TIMED_RUNS = 3

try:
    import psutil
except ImportError:
    psutil = None


def synthetic_text(word_count: int) -> str:
    """Fixed synthetic input. Placeholder words only, no message content."""
    return " ".join(["message"] * word_count)


def snapshot(process) -> dict:
    info = process.memory_info()
    peak = getattr(info, "peak_wset", None)
    return {
        "rss_mib": round(info.rss / MIB, 1),
        "peak_wset_mib": None if peak is None else round(peak / MIB, 1),
    }


def describe_source(module, model_name: str) -> dict:
    if model_name == "transformer":
        local = module._MODEL_PATH
        return {
            "directory": local,
            "directory_present": os.path.exists(local),
            "fallback": "Digvijay05/SCAMBERT",
            "tokenizer_and_weights": "local snapshot when present, Hub id otherwise",
        }
    local = module._MODEL_DIR
    return {
        "directory": local,
        "directory_present": os.path.exists(local),
        "config_present": os.path.exists(os.path.join(local, "config.json")),
        "weights_present": os.path.exists(
            os.path.join(local, "BiLSTMClassifier.safetensors")
        ),
        "tokenizer_source": (
            "local snapshot"
            if os.path.exists(os.path.join(local, "tokenizer_config.json"))
            else "bert-base-uncased"
        ),
    }


def environment_block(torch, transformers) -> dict:
    return {
        "python": platform.python_version(),
        "torch": torch.__version__,
        "transformers": transformers.__version__,
        "torch_num_threads": torch.get_num_threads(),
        "grad_mode": "torch.no_grad inside score()",
    }


def run_child(model_name: str, mode: str) -> dict:
    if psutil is None:
        print(INSTALL_HINT, file=sys.stderr)
        return None

    if REPO_ROOT not in sys.path:
        sys.path.insert(0, REPO_ROOT)

    import torch
    import transformers

    if model_name == COMBINED_LABEL:
        return run_combined_child(torch, transformers)
    return run_single_child(model_name, mode, torch, transformers)


def run_single_child(model_name: str, mode: str, torch, transformers) -> dict:
    if model_name == "transformer":
        from scamshield.models import transformer as module
    else:
        from scamshield.models import lstm as module

    process = psutil.Process()
    texts = {words: synthetic_text(words) for words in WORD_COUNTS}
    first_words = WORD_COUNTS[0]

    result = {
        "model": model_name,
        "mode": mode,
        "load_path": (
            f"scamshield.models.{model_name}.score -> "
            f"{model_name}._get_model lazy singleton"
        ),
        "source": describe_source(module, model_name),
        "environment": environment_block(torch, transformers),
        "stages": {"baseline_after_imports": snapshot(process)},
    }

    if mode == "staged":
        module._get_model()
        result["stages"]["after_singleton_built"] = snapshot(process)
        probability = module.score(texts[first_words])
        result["stages"]["after_first_inference"] = snapshot(process)
    else:
        probability = module.score(texts[first_words])
        result["stages"]["after_first_call_load_and_inference"] = snapshot(process)

    result["first_probability"] = round(float(probability), 6)
    result["first_input_words"] = first_words

    if mode == "staged":
        for words in WORD_COUNTS:
            text = texts[words]
            for _ in range(WARMUP_RUNS):
                module.score(text)
            timings = []
            for _ in range(TIMED_RUNS):
                started = time.perf_counter()
                module.score(text)
                timings.append((time.perf_counter() - started) * 1000.0)
            result[f"latency_{words}w_median_ms"] = round(statistics.median(timings), 2)

    for _ in range(TOTAL_INFERENCES - 1):
        module.score(texts[first_words])

    import gc

    gc.collect()
    result["stages"][f"after_{TOTAL_INFERENCES}_inferences"] = snapshot(process)
    return result


def run_combined_child(torch, transformers) -> dict:
    from scamshield.models import lstm, transformer

    process = psutil.Process()
    text = synthetic_text(WORD_COUNTS[0])
    modules = (("transformer", transformer), ("lstm", lstm))

    result = {
        "model": COMBINED_LABEL,
        "mode": COMBINED_MODE,
        "load_path": (
            "scamshield.models.transformer.score and "
            "scamshield.models.lstm.score, each through its own "
            "_get_model lazy singleton, in one process"
        ),
        "load_order": "transformer first, then lstm",
        "source": {
            name: describe_source(module, name) for name, module in modules
        },
        "environment": environment_block(torch, transformers),
        "stages": {"baseline_after_imports": snapshot(process)},
        "first_probability": {},
        "first_input_words": WORD_COUNTS[0],
    }

    for name, module in modules:
        probability = module.score(text)
        result["stages"][f"after_{name}_first_inference"] = snapshot(process)
        result["first_probability"][name] = round(float(probability), 6)

    for _, module in modules:
        for _ in range(TOTAL_INFERENCES - 1):
            module.score(text)

    import gc

    gc.collect()
    result["stages"][f"after_{TOTAL_INFERENCES}_inferences_each"] = snapshot(process)
    return result


def child_env() -> dict:
    env = dict(os.environ)
    env["PYTHONPATH"] = REPO_ROOT + os.pathsep + env.get("PYTHONPATH", "")
    env["TOKENIZERS_PARALLELISM"] = "false"
    env.setdefault("PYTHONIOENCODING", "utf-8")
    return env


def run_child_process(model_name: str, mode: str) -> dict:
    command = [
        sys.executable,
        os.path.abspath(__file__),
        "--child",
        model_name,
        "--child-mode",
        mode,
    ]
    completed = subprocess.run(
        command, capture_output=True, text=True, env=child_env(), cwd=REPO_ROOT
    )
    if completed.returncode != 0:
        print(
            f"{model_name}/{mode} child failed with code {completed.returncode}",
            file=sys.stderr,
        )
        print(completed.stderr.strip()[-2000:], file=sys.stderr)
        return None

    for line in completed.stdout.splitlines():
        if line.startswith(MARKER):
            return json.loads(line[len(MARKER):])

    print(
        f"{model_name}/{mode} child produced no result line", file=sys.stderr
    )
    print(completed.stdout.strip()[-2000:], file=sys.stderr)
    return None


def report_stage(stages: dict, key: str, previous: str = None) -> str:
    stage = stages.get(key)
    if stage is None:
        return "n/a"
    if previous is None:
        return f"rss {stage['rss_mib']} / peak {stage['peak_wset_mib']}"
    before = stages[previous]
    rss_growth = round(stage["rss_mib"] - before["rss_mib"], 1)
    peak_growth = round(stage["peak_wset_mib"] - before["peak_wset_mib"], 1)
    return (
        f"rss {stage['rss_mib']} (+{rss_growth}) / "
        f"peak {stage['peak_wset_mib']} (+{peak_growth})"
    )


def print_report(results: list) -> None:
    for entry in results:
        stages = entry["stages"]
        env = entry["environment"]
        combined = entry["mode"] == COMBINED_MODE
        print("")
        print(f"=== {entry['model']} / {entry['mode']} ===")
        print(f"load path: {entry['load_path']}")
        if combined:
            print(f"load order: {entry['load_order']}")
        print(f"source: {entry['source']}")
        print(
            f"runtime: python {env['python']}, torch {env['torch']}, "
            f"transformers {env['transformers']}, "
            f"threads {env['torch_num_threads']}, {env['grad_mode']}"
        )
        print(
            "baseline after imports: "
            + report_stage(stages, "baseline_after_imports")
        )
        if combined:
            print(
                "after transformer first inference: "
                + report_stage(
                    stages, "after_transformer_first_inference", "baseline_after_imports"
                )
            )
            print(
                "after lstm first inference: "
                + report_stage(
                    stages, "after_lstm_first_inference", "after_transformer_first_inference"
                )
            )
        elif entry["mode"] == "staged":
            print(
                "after singleton built: "
                + report_stage(stages, "after_singleton_built", "baseline_after_imports")
            )
            print(
                "after first inference: "
                + report_stage(stages, "after_first_inference", "after_singleton_built")
            )
        else:
            print(
                "after first call (load and inference together): "
                + report_stage(
                    stages,
                    "after_first_call_load_and_inference",
                    "baseline_after_imports",
                )
            )
        if combined:
            print(
                f"after {TOTAL_INFERENCES} inferences of each: "
                + report_stage(
                    stages,
                    f"after_{TOTAL_INFERENCES}_inferences_each",
                    "after_lstm_first_inference",
                )
            )
        else:
            print(
                f"after {TOTAL_INFERENCES} inferences: "
                + report_stage(
                    stages,
                    f"after_{TOTAL_INFERENCES}_inferences",
                    "after_first_inference"
                    if entry["mode"] == "staged"
                    else "after_first_call_load_and_inference",
                )
            )
        if combined:
            joined = ", ".join(
                f"{name} {value}"
                for name, value in entry["first_probability"].items()
            )
            print(f"first P(scam) on the {entry['first_input_words']}-word synthetic input: {joined}")
        else:
            print(
                f"first P(scam) on the {entry['first_input_words']}-word synthetic input: "
                f"{entry['first_probability']}"
            )
        for words in WORD_COUNTS:
            key = f"latency_{words}w_median_ms"
            if key in entry:
                print(f"{words}-word median latency: {entry[key]} ms")


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Profile production model memory, one fresh process per model, "
            "plus a combined process that holds both."
        )
    )
    parser.add_argument(
        "--model",
        choices=MODELS + (COMBINED_LABEL,),
        help="Profile one model only, or 'both' for the combined process.",
    )
    parser.add_argument(
        "--child",
        choices=MODELS + (COMBINED_LABEL,),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--child-mode",
        choices=SINGLE_MODES + (COMBINED_MODE,),
        help=argparse.SUPPRESS,
    )
    arguments = parser.parse_args()

    if arguments.child:
        payload = run_child(arguments.child, arguments.child_mode)
        if payload is None:
            return 2
        print(MARKER + json.dumps(payload))
        return 0

    if psutil is None:
        print(INSTALL_HINT, file=sys.stderr)
        return 2

    results = []
    if arguments.model == COMBINED_LABEL:
        payload = run_child_process(COMBINED_LABEL, COMBINED_MODE)
        if payload is None:
            return 1
        results.append(payload)
    else:
        for model_name in (arguments.model,) if arguments.model else MODELS:
            for mode in SINGLE_MODES:
                payload = run_child_process(model_name, mode)
                if payload is None:
                    return 1
                results.append(payload)
        payload = run_child_process(COMBINED_LABEL, COMBINED_MODE)
        if payload is None:
            return 1
        results.append(payload)

    print_report(results)
    print("")
    print("Note: peak_wset is a per-process high water mark and never decreases.")
    print("The combined process pays the transformers import once, so its figure")
    print("is not the sum of the two separate per-model figures.")
    print("Values are process RSS and peak working set in MiB.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
