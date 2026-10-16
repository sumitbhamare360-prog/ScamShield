"""Run the fixed synthetic check set and write privacy-safe evaluation results."""

import csv
import subprocess
from collections import Counter
from datetime import date
from pathlib import Path
import sys
from typing import Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scamshield import config, pipeline, preprocess
from scamshield.schemas import Message


CHECK_SET = ROOT / "data" / "eval" / "check_set.csv"
RESULTS = ROOT / "eval" / "results.md"
CONFIGURATIONS = ("transformer", "lstm", "rules", "full system")


def _read_rows() -> List[Dict[str, str]]:
    with CHECK_SET.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    if len(rows) != 40:
        raise ValueError(f"Expected 40 evaluation rows; found {len(rows)}.")
    return rows


def _score_for(configuration: str, verdict) -> Optional[float]:
    if configuration == "full system":
        return float(verdict.score)
    check = verdict.checks.get(configuration)
    if check is None or check.status != "ok" or check.score is None:
        return None
    return float(check.score)


def _metrics(rows: List[Dict[str, str]], predictions: List[Optional[float]]) -> Dict[str, object]:
    positive_threshold = next(
        lower for lower, _upper, label in config.BANDS if label == "Likely Scam"
    )
    suspicious_lower, suspicious_upper = next(
        (lower, upper)
        for lower, upper, label in config.BANDS
        if label == "Suspicious"
    )

    true_positive = false_positive = true_negative = false_negative = 0
    suspicious_rows = []
    unavailable_rows = []
    false_positive_rows = []
    false_negative_rows = []

    for row_number, (row, score) in enumerate(zip(rows, predictions), start=1):
        actual_scam = row["label"] == "scam"
        if score is None:
            unavailable_rows.append(row_number)
            predicted_scam = False
        elif suspicious_lower <= score < suspicious_upper:
            suspicious_rows.append(row_number)
            continue
        else:
            predicted_scam = score >= positive_threshold

        if actual_scam and predicted_scam:
            true_positive += 1
        elif not actual_scam and predicted_scam:
            false_positive += 1
            false_positive_rows.append(row_number)
        elif actual_scam:
            false_negative += 1
            false_negative_rows.append(row_number)
        else:
            true_negative += 1

    included = true_positive + false_positive + true_negative + false_negative
    accuracy = (true_positive + true_negative) / included if included else 0.0
    precision = true_positive / (true_positive + false_positive) if true_positive + false_positive else 0.0
    recall = true_positive / (true_positive + false_negative) if true_positive + false_negative else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "suspicious_rows": suspicious_rows,
        "unavailable_rows": unavailable_rows,
        "false_positive_rows": false_positive_rows,
        "false_negative_rows": false_negative_rows,
        "included": included,
    }


def _masked_row_text(row: Dict[str, str]) -> str:
    message = Message(text=row["text"], channel=row["channel"])
    return preprocess.extract(message).masked_text


def _row_list(title: str, row_numbers: List[int], rows: List[Dict[str, str]]) -> List[str]:
    if not row_numbers:
        return [f"- {title}: none"]
    return [f"- {title}:"] + [
        f"  - Row {number}: {_masked_row_text(rows[number - 1])}"
        for number in row_numbers
    ]


def _git_revision() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def main() -> None:
    rows = _read_rows()
    label_counts = Counter(row["label"] for row in rows)
    if label_counts != {"scam": 20, "safe": 20}:
        raise ValueError("The check set must contain exactly 20 scam and 20 safe rows.")
    if any(row["source"] != "synthetic" for row in rows):
        raise ValueError("Every check-set source must be synthetic.")

    predictions = {name: [] for name in CONFIGURATIONS}
    for row in rows:
        message = Message(text=row["text"], channel=row["channel"])
        verdict = pipeline.analyze(message, use_reputation=False, blocklist=set())
        for configuration in CONFIGURATIONS:
            predictions[configuration].append(_score_for(configuration, verdict))

    summaries = {name: _metrics(rows, predictions[name]) for name in CONFIGURATIONS}
    results_lines = [
        "Synthetic check set of 40 messages. For sanity checking only. Not a published accuracy claim.",
        "",
        f"Date: {date.today().isoformat()}",
        f"Evaluation code revision (HEAD before this results commit): `{_git_revision()}`",
        f"Rows: {label_counts['scam']} scam, {label_counts['safe']} safe; all sources synthetic.",
        "",
        "Metrics exclude Suspicious scores from binary classification. Missing scores count as not positive and are listed separately.",
        "",
        "| Configuration | Accuracy | Precision | Recall | F1 | Included rows |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for name in CONFIGURATIONS:
        result = summaries[name]
        results_lines.append(
            f"| {name} | {result['accuracy']:.3f} | {result['precision']:.3f} | "
            f"{result['recall']:.3f} | {result['f1']:.3f} | {result['included']} |"
        )

    results_lines.extend(["", "Suspicious result counts:"])
    for name in CONFIGURATIONS:
        result = summaries[name]
        results_lines.append(
            f"- {name}: {len(result['suspicious_rows'])} rows "
            f"({', '.join(map(str, result['suspicious_rows'])) or 'none'})."
        )
    results_lines.extend(["", "Unavailable score counts:"])
    for name in CONFIGURATIONS:
        result = summaries[name]
        results_lines.append(
            f"- {name}: {len(result['unavailable_rows'])} rows "
            f"({', '.join(map(str, result['unavailable_rows'])) or 'none'})."
        )

    for name in CONFIGURATIONS:
        results_lines.extend(["", f"### {name}"])
        results_lines.extend(_row_list("False positives", summaries[name]["false_positive_rows"], rows))
        results_lines.extend(_row_list("False negatives", summaries[name]["false_negative_rows"], rows))

    results_lines.extend(["", "Scoring weights used:"])
    results_lines.extend(f"- {name}: {weight:.2f}" for name, weight in config.WEIGHTS.items())
    results_lines.extend([
        "",
        "Scoring weights were not tuned on this set. Results are development sanity checks only.",
        "",
        "Check-set row text is synthetic. False-positive and false-negative examples above use preprocessed masked text only.",
    ])
    RESULTS.write_text("\n".join(results_lines) + "\n", encoding="utf-8")

    print("Evaluation completed for 40 synthetic rows.")
    for name in CONFIGURATIONS:
        result = summaries[name]
        print(
            f"{name}: accuracy={result['accuracy']:.3f}, precision={result['precision']:.3f}, "
            f"recall={result['recall']:.3f}, f1={result['f1']:.3f}, "
            f"suspicious={len(result['suspicious_rows'])}, unavailable={len(result['unavailable_rows'])}"
        )
    print(f"Results written to {RESULTS.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
