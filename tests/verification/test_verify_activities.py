import pytest

from evaluations.verification.verify_activities import VerifyActivities


class TestVerifyActivities:
    def _verify(self, actual_data, expected_data):
        verifier = VerifyActivities(actual_data, expected_data)
        return verifier.verify()

    @pytest.fixture(scope="class")
    def result(self):
        actual_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]
        expected_data = [{
            "step": 5,
            "text": "The risk manager passes the voted contract on to the sales person",
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "ask for",
                "object_id": "voted_contract_1",
                "relation": "to",
                "target_id": "sales_person"
            },
            "sub_activities": []
        }]

        return self._verify(actual_data, expected_data)

    def test_verify_activity_all_correct(self):
        actual_data = [{
            "step": 1,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "fills out",
                "object_id": "credit_rating_form_1",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "credit_rating_form_1",
                    "relation": "with",
                    "target_id": "information_1"
                }
            ]
        }]

        expected_data = [{
            "step": 1,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "fills out",
                "object_id": "credit_rating_form_1",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "credit_rating_form_1",
                    "relation": "with",
                    "target_id": "information_1"
                }
            ]
        }]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 10
        assert result.correct_fields == 10
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 0
        assert result.missing_fields.main_activity.total == 0
        assert result.missing_fields.sub_activities.total == 0
        assert result.hallu_fields.main_activity.total == 0
        assert result.hallu_fields.sub_activities.total == 0

    def test_verify_activity_missing_main_activity_action(self):
        actual_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": None,
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        expected_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 10
        assert result.correct_fields == 9
        assert result.missing_fields.total == 1
        assert result.hallu_fields.total == 0

    def test_verify_activity_hallucinated_main_activity_action(self):
        actual_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "banana",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        expected_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 10
        assert result.correct_fields == 9
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 1

    def test_verify_activity_missing_subactivity_line(self):
        actual_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        expected_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                },
                {
                    "line_order": 3,
                    "subject_id": "sales_person",
                    "relation": "to",
                    "target_id": "bank_officer"
                }
            ]
        }]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 14
        assert result.correct_fields == 10
        assert result.missing_fields.total == 4
        assert result.hallu_fields.total == 0

    def test_verify_activity_hallucinated_subactivity_line(self):
        actual_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                },
                {
                    "line_order": 3,
                    "subject_id": "sales_person",
                    "relation": "to",
                    "target_id": "bank_officer"
                }
            ]
        }]

        expected_data = [{
            "step": 5,
            "text": None,
            "main_activity": {
                "subject_id": "risk_manager",
                "action": "asks",
                "object_id": "contract_3",
                "relation": None,
                "target_id": None
            },
            "sub_activities": [
                {
                    "line_order": 2,
                    "subject_id": "contract_3",
                    "relation": "on to",
                    "target_id": "sales_person"
                }
            ]
        }]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 10
        assert result.correct_fields == 10
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 4
