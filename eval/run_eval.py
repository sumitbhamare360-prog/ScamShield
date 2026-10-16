"""Run the fixed synthetic check set and write privacy-safe evaluation results."""

import argparse
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
CATEGORY_LABELS = (
    "Likely Safe",
    "Suspicious",
    "Likely Scam",
    "High-Risk Scam",
    "Uncertain: verify manually",
)


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


def _thresholds() -> tuple[float, float, float]:
    positive_threshold = next(
        lower for lower, _upper, label in config.BANDS if label == "Likely Scam"
    )
    suspicious_lower, suspicious_upper = next(
        (lower, upper)
        for lower, upper, label in config.BANDS
        if label == "Suspicious"
    )
    return positive_threshold, suspicious_lower, suspicious_upper


def _metrics(
    rows: List[Dict[str, str]],
    predictions: List[Optional[float]],
    positive_threshold: float,
) -> Dict[str, object]:
    _scam_threshold, suspicious_lower, suspicious_upper = _thresholds()

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
        else:
            if suspicious_lower <= score < suspicious_upper:
                suspicious_rows.append(row_number)
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


def _uncertain_metrics(
    rows: List[Dict[str, str]],
    predictions: List[Optional[float]],
    categories: List[str],
    positive_threshold: float,
) -> Dict[str, object]:
    uncertain_indices = [
        index for index, category in enumerate(categories)
        if category == "Uncertain: verify manually"
    ]
    included_indices = [
        index for index, category in enumerate(categories)
        if category != "Uncertain: verify manually"
    ]
    summary = _metrics(
        [rows[index] for index in included_indices],
        [predictions[index] for index in included_indices],
        positive_threshold,
    )
    summary["uncertain_rows"] = len(uncertain_indices)
    summary["uncertain_scam_rows"] = sum(rows[index]["label"] == "scam" for index in uncertain_indices)
    summary["uncertain_safe_rows"] = sum(rows[index]["label"] == "safe" for index in uncertain_indices)
    return summary


def _is_suspicious(score: Optional[float]) -> bool:
    _scam_threshold, suspicious_lower, suspicious_upper = _thresholds()
    return score is not None and suspicious_lower <= score < suspicious_upper


def _full_system_error_lines(
    title: str,
    row_numbers: List[int],
    rows: List[Dict[str, str]],
    predictions: List[Optional[float]],
) -> List[str]:
    if not row_numbers:
        return [f"- {title}: none"]
    suspicious_errors = sum(_is_suspicious(predictions[number - 1]) for number in row_numbers)
    lines = [
        f"- {title}: {len(row_numbers)} rows; {suspicious_errors} were Suspicious before reclassification."
    ]
    for number in row_numbers:
        status = "Suspicious before reclassification" if _is_suspicious(predictions[number - 1]) else "not Suspicious"
        lines.append(f"  - Row {number} ({status}): {_masked_row_text(rows[number - 1])}")
    return lines


def _masked_row_text(row: Dict[str, str]) -> str:
    message = Message(text=row["text"], channel=row["channel"])
    return preprocess.extract(message).masked_text


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


def _analyze_row(row: Dict[str, str]):
    message = Message(text=row["text"], channel=row["channel"])
    return pipeline.analyze(message, use_reputation=False, blocklist=set())


def _probability(verdict, name: str) -> Optional[float]:
    check = verdict.checks.get(name)
    if check is None or check.status != "ok" or check.score is None:
        return None
    return float(check.score) / 100.0


def _show_row(rows: List[Dict[str, str]], row_number: int) -> None:
    if row_number < 1 or row_number > len(rows):
        raise ValueError(f"Row number must be between 1 and {len(rows)}.")
    row = rows[row_number - 1]
    verdict = _analyze_row(row)
    rules_check = verdict.checks.get("rules")
    rule_ids = [evidence.rule_id for evidence in rules_check.evidence] if rules_check else []
    print(f"Row: {row_number}")
    print(f"Masked text: {preprocess.extract(Message(text=row['text'], channel=row['channel'])).masked_text}")
    print(f"Verdict category: {verdict.category}")
    print(f"Numeric score: {verdict.score}")
    print(f"Uncertain: {verdict.uncertain}")
    print(f"Transformer probability: {_probability(verdict, 'transformer')}")
    print(f"LSTM probability: {_probability(verdict, 'lstm')}")
    print(f"Rule IDs fired: {', '.join(rule_ids) if rule_ids else 'none'}")


def main(show_row: Optional[int] = None) -> None:
    rows = _read_rows()
    label_counts = Counter(row["label"] for row in rows)
    if label_counts != {"scam": 20, "safe": 20}:
        raise ValueError("The check set must contain exactly 20 scam and 20 safe rows.")
    if any(row["source"] != "synthetic" for row in rows):
        raise ValueError("Every check-set source must be synthetic.")

    if show_row is not None:
        _show_row(rows, show_row)
        return

    predictions = {name: [] for name in CONFIGURATIONS}
    row_categories = []
    row_scores = []
    row_uncertain = []
    for row in rows:
        verdict = _analyze_row(row)
        row_categories.append(verdict.category)
        row_scores.append(verdict.score)
        row_uncertain.append(verdict.uncertain)
        for configuration in CONFIGURATIONS:
            predictions[configuration].append(_score_for(configuration, verdict))

    scam_threshold, suspicious_lower, suspicious_upper = _thresholds()
    scenarios = (
        ("Suspicious as not scam", scam_threshold),
        ("Suspicious as scam", suspicious_lower),
    )
    summaries = {
        scenario: {
            name: _metrics(rows, predictions[name], threshold)
            for name in CONFIGURATIONS
        }
        for scenario, threshold in scenarios
    }
    uncertain_summary = _uncertain_metrics(
        rows,
        predictions["full system"],
        row_categories,
        scam_threshold,
    )
    category_counts = Counter(row_categories)
    results_lines = [
        "Synthetic check set of 40 messages. For sanity checking only. Not a published accuracy claim.",
        "",
        f"Date: {date.today().isoformat()}",
        f"Evaluation code revision (HEAD before this results commit): `{_git_revision()}`",
        f"Rows: {label_counts['scam']} scam, {label_counts['safe']} safe; all sources synthetic.",
        "",
        f"All metrics use all 40 rows. Missing scores count as not scam and are listed separately. Suspicious band: {suspicious_lower:g} to below {suspicious_upper:g}; scam-positive boundary: {scam_threshold:g}.",
        "Suspicious in the first two tables is a numeric score band; a user-facing verdict category may instead be Uncertain.",
    ]
    for scenario, _threshold in scenarios:
        results_lines.extend([
            "",
            f"### {scenario}",
            "",
            "| Configuration | Accuracy | Precision | Recall | F1 | Rows |",
            "|---|---:|---:|---:|---:|---:|",
        ])
        for name in CONFIGURATIONS:
            result = summaries[scenario][name]
            results_lines.append(
                f"| {name} | {result['accuracy']:.3f} | {result['precision']:.3f} | "
                f"{result['recall']:.3f} | {result['f1']:.3f} | {result['included']} |"
            )

    results_lines.extend([
        "",
        "### Full system: Uncertain as its own outcome",
        "Uncertain rows are neither scam nor safe and are excluded. For included rows, Suspicious scores count as not scam.",
        f"Uncertain rows: {uncertain_summary['uncertain_rows']} total, {uncertain_summary['uncertain_scam_rows']} scam, {uncertain_summary['uncertain_safe_rows']} safe. Included rows: {uncertain_summary['included']} of 40.",
        "",
        "| Configuration | Accuracy | Precision | Recall | F1 | Included rows |",
        "|---|---:|---:|---:|---:|---:|",
        f"| full system | {uncertain_summary['accuracy']:.3f} | {uncertain_summary['precision']:.3f} | {uncertain_summary['recall']:.3f} | {uncertain_summary['f1']:.3f} | {uncertain_summary['included']} |",
    ])

    results_lines.extend([
        "",
        "Verdict category by row:",
        "",
        "| Row | Actual label | Verdict category | Score | Uncertain |",
        "|---:|---|---|---:|---|",
    ])
    for index, row in enumerate(rows):
        results_lines.append(
            f"| {index + 1} | {row['label']} | {row_categories[index]} | {row_scores[index]} | {row_uncertain[index]} |"
        )

    results_lines.extend(["", "Verdict category counts:", ""])
    results_lines.extend([
        "| Verdict category | Rows |",
        "|---|---:|",
    ])
    for category in CATEGORY_LABELS:
        results_lines.append(f"| {category} | {category_counts.get(category, 0)} |")

    results_lines.extend(["", "Suspicious counts before reclassification:"])
    for name in CONFIGURATIONS:
        result = summaries[scenarios[0][0]][name]
        results_lines.append(
            f"- {name}: {len(result['suspicious_rows'])} rows "
            f"({', '.join(map(str, result['suspicious_rows'])) or 'none'})."
        )
    results_lines.extend(["", "Unavailable score counts:"])
    for name in CONFIGURATIONS:
        result = summaries[scenarios[0][0]][name]
        results_lines.append(
            f"- {name}: {len(result['unavailable_rows'])} rows "
            f"({', '.join(map(str, result['unavailable_rows'])) or 'none'})."
        )

    full_predictions = predictions["full system"]
    for scenario, _threshold in scenarios:
        result = summaries[scenario]["full system"]
        results_lines.extend(["", f"### Full-system errors: {scenario}"])
        results_lines.extend(_full_system_error_lines(
            "False positives", result["false_positive_rows"], rows, full_predictions
        ))
        results_lines.extend(_full_system_error_lines(
            "False negatives", result["false_negative_rows"], rows, full_predictions
        ))

    results_lines.extend(["", "Scoring weights used:"])
    results_lines.extend(f"- {name}: {weight:.2f}" for name, weight in config.WEIGHTS.items())
    results_lines.extend([
        "",
        "Scoring weights were not tuned on this set. Results are development sanity checks only.",
        "Rules-only may be optimistic because this synthetic set and its rules share phrasing patterns; treat it as an upper bound, not evidence of generalization.",
        "",
        "Check-set row text is synthetic. False-positive and false-negative examples above use preprocessed masked text only.",
    ])
    RESULTS.write_text("\n".join(results_lines) + "\n", encoding="utf-8")

    print("Evaluation completed for 40 synthetic rows.")
    for scenario, _threshold in scenarios:
        print(f"{scenario}:")
        for name in CONFIGURATIONS:
            result = summaries[scenario][name]
            print(
                f"{name}: accuracy={result['accuracy']:.3f}, precision={result['precision']:.3f}, "
                f"recall={result['recall']:.3f}, f1={result['f1']:.3f}"
            )
    print(f"Results written to {RESULTS.relative_to(ROOT)}.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the synthetic ScamShield check set.")
    parser.add_argument("--show-row", type=int, help="Analyze and show one row using masked text only.")
    arguments = parser.parse_args()
    main(show_row=arguments.show_row)
