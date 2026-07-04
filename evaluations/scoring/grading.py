import json
from typing import Dict, Any, Union
from helpers import load_json, normalize_text


def extract_actors(payload):
    # payload = load_json(payload)
    if isinstance(payload, dict):
        if "result" in payload and isinstance(payload["result"], dict):
            return payload["result"].get("actors", [])
        return payload.get("actors", [])
    return []


def compute_actor_metrics(detected_actors, expected_actors):
    detected_by_name = {
        normalize_text(actor["name"]): actor for actor in detected_actors
        if isinstance(actor, dict) and "name" in actor
    }
    expected_by_name = {
        normalize_text(actor["name"]): actor for actor in expected_actors
        if isinstance(actor, dict) and "name" in actor
    }

    matched_names = set(detected_by_name).intersection(expected_by_name)
    matched_count = len(matched_names)
    total_expected = len(expected_by_name)
    total_detected = len(detected_by_name)

    recall = matched_count / total_expected if total_expected > 0 else 1.0
    precision = matched_count / total_detected if total_detected > 0 else 1.0
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    missing = [actor["name"] for actor in expected_actors if normalize_text(actor["name"]) not in matched_names]
    extra = [actor["name"] for actor in detected_actors if normalize_text(actor["name"]) not in matched_names]

    return {
        "pass": matched_count == total_expected and total_detected == total_expected,
        "score": 2,  # precision,
        "metrics": {
            "precision": precision,
            "recall": recall,
            "f1": round(f1, 2),
            "matched_count": matched_count,
            "total_expected": total_expected,
            "total_detected": total_detected,
            "false_negatives": len(missing),
            "false_positives": len(extra),
        },
        "missing": missing,
        "extra": extra,
    }


def grading(output: str, context) -> Union[bool, float, Dict[str, Any]]:
    expected_output = context["vars"]["expected_output"]

    detected_actors = extract_actors(output)
    expected_actors = extract_actors(expected_output)

    compute_metric = compute_actor_metrics(detected_actors, expected_actors)
    return {
        **compute_metric,
        "reason": json.dumps(
            {
                "output": output,
                "expected_output": expected_output,
                "metrics": compute_metric["metrics"],
            },
            ensure_ascii=False,
            indent=2,
            default=str,
        )
    }

###################################

output_path = r"/alphorn-test-json/output_example_alphorn-3.json"
expected_path = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn-gold-standard\gold-alphorn-3.json"


def run_grading_from_files(output_file_path: str, expected_output_path: str) -> Union[bool, float, Dict[str, Any]]:
    output = load_json(output_file_path)
    expected_output = load_json(expected_output_path)

    detected_actors = extract_actors(output)
    expected_actors = extract_actors(expected_output)

    print(f"Detected actors: {[actor.get('name') for actor in detected_actors if isinstance(actor, dict)]}")
    print(f"Expected actors: {[actor.get('name') for actor in expected_actors if isinstance(actor, dict)]}")
    compute_metric = compute_actor_metrics(detected_actors, expected_actors)
    print(f'type of compute_metric: ', type(compute_metric))

    return compute_metric


if __name__ == "__main__":
    result = run_grading_from_files(output_path, expected_path)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
