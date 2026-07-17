import json
import sys
from pathlib import Path

# Ensure both the project root and evaluations/ are on sys.path so that
# sibling packages (scoring, verification) are importable when promptfoo
# runs this file as a standalone script.
_EVALUATIONS_DIR = Path(__file__).resolve().parents[1]  # .../evaluations/
_ROOT_DIR = _EVALUATIONS_DIR.parent  # .../NL_2_DST/
for _p in (_ROOT_DIR, _EVALUATIONS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scoring import evaluate
from verification import load_json


def extract_actors(payload):
    # payload = load_json(payload)
    if isinstance(payload, dict):
        # if "result" in payload and isinstance(payload["result"], dict):
        #     return payload["result"].get("actors", [])
        return payload.get("actors", [])
    return []


def grading(actual_output, context):
    get_expected_output = context["vars"]["expected_output"]
    if isinstance(get_expected_output, dict):
        expected_output = get_expected_output
    else:
        candidate = Path(str(get_expected_output))
        if candidate.exists():
            expected_output = load_json(candidate)
        else:
            expected_output = json.loads(get_expected_output)

    eval_story = evaluate(actual_output, expected_output)

    return {
        "pass": True,
        "score": eval_story['pass_rate'],
        "reason": "",
        "total_fields": eval_story['total_fields'],
        "correct_fields": eval_story['correct_fields'],
        "actors_result": eval_story['actors_stats'],
        "work_objects_result": eval_story['work_objects_stats'],
        "activities_result": eval_story['activities_stats']
    }


project_root = Path(__file__).parents[2]
output_path = project_root / "alphorn-test-json" / "output_example_alphorn-3.json"
expected_path = project_root / "evaluations" / "promptfoo_eval" / "alphorn-gold-standard" / "gold-alphorn-3.json"

if __name__ == "__main__":
    actual_data = load_json(output_path)
    expected_data = load_json(expected_path)

    eval = evaluate(actual_data, expected_data)
    print(round(eval, 3))
