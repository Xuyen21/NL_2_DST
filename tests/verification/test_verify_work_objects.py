from pathlib import Path

import pytest

from evaluations.verification import load_json
from evaluations.verification.verify_work_objects import group_by_name, group_by_instance, VerifyWorkObjects

# Path to real test fixtures
_PROJECT_ROOT = Path(__file__).parents[2]
_OUTPUT_ALPHORN_2 = _PROJECT_ROOT / "alphorn-test-json" / "output_example_alphorn-2-gemini-flash2.5.json"
_GOLD_ALPHORN_2 = _PROJECT_ROOT / "evaluations" / "promptfoo-eval" / "alphorn-gold-standard" / "gold-alphorn-2.json"

# Small inline fixtures shared by several unit tests
_WORK_OBJECTS_SINGLE = [
    {
        "name": "Contract",
        "description": "A legal agreement.",
        "instances": [
            {"instance_id": "contract_1", "note": None},
            {"instance_id": "contract_2", "note": "signed copy"},
        ],
    }
]

_WORK_OBJECTS_MULTI = [
    {
        "name": "Invoice",
        "description": "Billing document.",
        "instances": [{"instance_id": "invoice_1", "note": None}],
    },
    {
        "name": "Contract",
        "description": "A legal agreement.",
        "instances": [{"instance_id": "contract_1", "note": None}],
    },
]


# ===========================================================================
# group_by_name / group_by_instance
# ===========================================================================
class TestGroupByName:
    def test_returns_dict_keyed_by_normalized_name(self):
        result = group_by_name(_WORK_OBJECTS_MULTI)
        assert "invoice" in result
        assert "contract" in result

    def test_preserves_original_object(self):
        result = group_by_name(_WORK_OBJECTS_SINGLE)
        assert result["contract"]["description"] == "A legal agreement."

    def test_normalizes_mixed_case(self):
        objects = [{"name": "Risk Assessment", "description": "d", "instances": []}]
        result = group_by_name(objects)
        assert "risk assessment" in result


class TestGroupByInstance:
    def test_flattens_all_instances(self):
        result = group_by_instance(_WORK_OBJECTS_MULTI)
        assert len(result) == 2  # invoice_1 + contract_1

    def test_flattens_multiple_instances_per_object(self):
        result = group_by_instance(_WORK_OBJECTS_SINGLE)
        assert len(result) == 2
        instance_ids = [i["instance_id"] for i in result]
        assert "contract_1" in instance_ids
        assert "contract_2" in instance_ids


# eval_work_objects — unit-level (small inline data)
class TestEvalWorkObjectsUnit:
    def test_perfect_match_returns_all_correct(self):
        work_objects = [
            {
                "name": "invoice",
                "description": "billing document",
                "instances": [{"instance_id": "invoice_1", "note": None}],
            }
        ]
        verifier = VerifyWorkObjects(work_objects, work_objects)
        result = verifier.verify()
        assert result["missing_fields"]["total"] == 0
        assert result["hallu_fields"]["total"] == 0

    def test_completely_missing_work_object(self):
        expected = [
            {
                "name": "invoice",
                "description": "billing document",
                "instances": [{"instance_id": "invoice_1", "note": None}],
            }
        ]
        verifier = VerifyWorkObjects(actual_output=[], expected_output=expected)
        result = verifier.verify()
        assert result["missing_fields"]["total"] > 0
        assert result["correct_fields"] == 0

    def test_hallucinated_work_object(self):
        extra = [
            {
                "name": "extra object",
                "description": "not in gold",
                "instances": [{"instance_id": "extra_1", "note": None}],
            }
        ]
        verifier = VerifyWorkObjects(actual_output=extra, expected_output=[])
        result = verifier.verify()
        assert result["hallu_fields"]["total"] > 0

    def test_result_keys_present(self):
        verifier = VerifyWorkObjects(actual_output=[], expected_output=[])
        result = verifier.verify()
        assert set(result.keys()) == {"total_fields", "correct_fields", "missing_fields", "hallu_fields"}


# eval_work_objects — integration test
class TestEvalWorkObjectsAlphorn2:
    """
    Scenario: alphorn-2 LLM output evaluated against its gold standard.
    Known differences:
      - 'voted contract' exists in gold but is absent from the output  →  missing
      - 'contract' has an extra instance (contract_3) in the output   →  hallucinated
      - 'risk_assessment_1.note' has text in gold but is null in output  →  missing note
    """

    @pytest.fixture(scope="class")
    @classmethod
    def result(cls):
        output = load_json(_OUTPUT_ALPHORN_2)
        expected = load_json(_GOLD_ALPHORN_2)
        verifier = VerifyWorkObjects(actual_output=output["work_objects"], expected_output=expected["work_objects"])
        return verifier.verify()

    def test_returns_expected_keys(self, result):
        assert set(result.keys()) == {"total_fields", "correct_fields", "missing_fields", "hallu_fields"}

    def test_total_fields_positive(self, result):
        assert result["total_fields"] == 36

    def test_correct_fields_positive(self, result):
        assert result["correct_fields"] == 23

    def test_missing_fields_because_voted_contract_absent(self, result):
        # 'voted contract' is in gold but not in the model output
        assert result["missing_fields"]["total"] == 7
        assert "voted contract" in result["missing_fields"]["work_object"]["detail"]

    def test_hallucinated_fields_because_extra_contract_instance(self, result):
        # contract_3 appears in the output but is not in the gold standard
        assert result["hallu_fields"]["total"] == 8

    def test_correct_fields_do_not_exceed_total(self, result):
        assert result["correct_fields"] <= result["total_fields"]
