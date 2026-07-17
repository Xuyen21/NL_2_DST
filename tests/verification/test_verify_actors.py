import pytest

from evaluations.verification.verify_actors import VerifyActors


class TestVerifyActors:
    def _verify(self, actual_data, expected_data):
        verifier = VerifyActors(actual_data, expected_data)
        return verifier.verify()

    @pytest.fixture(scope="class")
    def actor_fixture(self):
        return [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
            {"id": "rating_agency_website", "name": "rating agency website", "type": "System", "note": None},
            {"id": "sales_person", "name": "sales person", "type": "Person", "note": None},
            {"id": "risk_management_system", "name": "risk management system", "type": "System", "note": None},
        ]

    def test_verify_actors_all_correct(self, actor_fixture):
        result = self._verify(actor_fixture, actor_fixture)

        assert result.total_fields == 12
        assert result.correct_fields == 12
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 0
        assert result.missing_fields.names.total == 0
        assert result.missing_fields.types.total == 0
        assert result.hallu_fields.names.total == 0
        assert result.hallu_fields.types.total == 0

    def test_verify_actors_missing_actor(self):
        actual_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
            {"id": "rating_agency_website", "name": "rating agency website", "type": "System", "note": None},
            {"id": "sales_person", "name": "sales person", "type": "Person", "note": None},
        ]
        expected_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
            {"id": "rating_agency_website", "name": "rating agency website", "type": "System", "note": None},
            {"id": "sales_person", "name": "sales person", "type": "Person", "note": None},
            {"id": "risk_management_system", "name": "risk management system", "type": "System", "note": None},
        ]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 12
        assert result.correct_fields == 9
        assert result.missing_fields.total == 3
        assert result.hallu_fields.total == 0

    def test_verify_actors_hallucinated_actor(self):
        actual_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
            {"id": "rating_agency_website", "name": "rating agency website", "type": "System", "note": None},
            {"id": "sales_person", "name": "sales person", "type": "Person", "note": None},
            {"id": "risk_management_system", "name": "risk management system", "type": "System", "note": None},
        ]
        expected_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
            {"id": "rating_agency_website", "name": "rating agency website", "type": "System", "note": None},
            {"id": "sales_person", "name": "sales person", "type": "Person", "note": None},
        ]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 9
        assert result.correct_fields == 9
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 3

    def test_verify_actors_incorrect_type(self):
        actual_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "System", "note": None},
        ]
        expected_data = [
            {"id": "risk_manager", "name": "risk manager", "type": "Person", "note": None},
        ]

        result = self._verify(actual_data, expected_data)

        assert result.total_fields == 3
        assert result.correct_fields == 2
        assert result.missing_fields.total == 0
        assert result.hallu_fields.total == 1
