from evaluations.verification import VerifyOutput
from verification import VerificationResult, count_primitive_kv_pairs, semantic_similarity
from verification.stats import ActivitiesStats
from verification.verify_work_objects import group_by_key


class VerifyActivities(VerifyOutput):
    """Verifier for activities comparing against an expected output"""

    def __init__(self, actual_output, expected_output):
        super().__init__(actual_output, expected_output)
        self.correct_fields = 0
        self.missing_fields = ActivitiesStats()
        self.hallu_fields = ActivitiesStats()

    def exact_match(self, actual_output: str | int, expected_output: str | int):
        if actual_output == expected_output:
            self.correct_fields += 1

        elif not actual_output and expected_output:
            self.missing_fields.increase_total()
            self.missing_fields.main_activity.add_detail(str(actual_output))

        else:
            self.hallu_fields.increase_total()
            self.hallu_fields.main_activity.add_detail(str(actual_output))

    def semantic_match(self, actual_output: str, expected_output: str):
        result = semantic_similarity(actual_output, expected_output)
        if result['similarity_score'] > 0.6:
            self.correct_fields += 1
        else:
            match result['case']:
                case 'missing':
                    self.missing_fields.increase_total()
                    # self.missing_fields.main_activity.add_detail(actual_output)
                case 'hallucination' | 'both_has_content':
                    self.hallu_fields.increase_total()
                    # self.hallu_fields.main_activity.add_detail(actual_output)

    def verify(self) -> VerificationResult[ActivitiesStats]:
        included_fields_for_counting = ['step', 'main_activity', 'sub_activities']
        total_fields = count_primitive_kv_pairs(self.expected_output, included_fields_for_counting)

        expected_steps = group_by_key("step", self.expected_output)
        actual_steps = group_by_key("step", self.actual_output)

        expected_steps_keys = set(expected_steps.keys())
        actual_steps_keys = set(actual_steps.keys())

        correct_steps = expected_steps_keys & actual_steps_keys
        missing_steps = expected_steps_keys - actual_steps_keys
        hallu_steps = actual_steps_keys - expected_steps_keys

        if missing_steps:
            for missed_step in missing_steps:
                count_fields = count_primitive_kv_pairs(expected_steps[missed_step], included_fields_for_counting)
                self.missing_fields.step.add_detail(missed_step)
                self.missing_fields.increase_total(count_fields)
                self.missing_fields.step.increase_total(count_fields)
        if hallu_steps:
            for hallu_step in hallu_steps:
                count_fields = count_primitive_kv_pairs(actual_steps[hallu_step], included_fields_for_counting)
                self.hallu_fields.increase_total(count_fields)
                self.hallu_fields.step.increase_total(count_fields)
                self.hallu_fields.step.add_detail(hallu_step)

        # check children content when the step is correct
        for step in correct_steps:
            expected_obj = expected_steps[step]
            actual_obj = actual_steps[step]

            self.correct_fields += 1

            # check main activity
            actual_subject_id, actual_action, actual_object_id, actual_relation, actual_target_id = actual_obj[
                "main_activity"].values()
            exp_subject_id, exp_action, exp_object_id, exp_relation, exp_target_id = expected_obj[
                "main_activity"].values()

            self.exact_match(actual_subject_id, exp_subject_id)
            self.exact_match(actual_object_id, exp_object_id)
            self.exact_match(actual_target_id, exp_target_id)

            self.semantic_match(actual_action, exp_action)
            self.semantic_match(actual_relation, exp_relation)

            # check sub activities
            actual_sub_activities = actual_obj.get("sub_activities", [])
            expected_sub_activities = expected_obj.get("sub_activities", [])
            self.check_subactivities(actual_sub_activities, expected_sub_activities)

        return VerificationResult(
            total_fields=total_fields,
            correct_fields=self.correct_fields,
            missing_fields=self.missing_fields,
            hallu_fields=self.hallu_fields
        )

    def check_subactivities(self, actual_output: list[dict], expected_output: list[dict]):

        actual_lines = group_by_key("line_order", actual_output)
        expected_lines = group_by_key("line_order", expected_output)

        actual_lines_keys = set(actual_lines.keys())
        expected_lines_keys = set(expected_lines.keys())

        correct_lines = expected_lines_keys & actual_lines_keys
        missing_lines = expected_lines_keys - actual_lines_keys
        hallu_lines = actual_lines_keys - expected_lines_keys

        if missing_lines:
            for missing_line in missing_lines:
                self.missing_fields.increase_total(4)  # each missing line comes along with 4 fields in total
                self.missing_fields.sub_activities.add_detail(missing_line)
        if hallu_lines:
            for hallu_line in hallu_lines:
                self.hallu_fields.increase_total(4)
                self.hallu_fields.sub_activities.add_detail(hallu_line)

        for correct_line in correct_lines:
            self.correct_fields += 1
            actual_line = actual_lines[correct_line]
            expected_line = expected_lines[correct_line]

            _, actual_subject_id, actual_relation, actual_target_id = actual_line.values()
            _, expected_subject_id, expected_relation, expected_target_id = expected_line.values()

            self.exact_match(actual_subject_id, expected_subject_id)
            self.exact_match(actual_target_id, expected_target_id)
            self.semantic_match(actual_relation, expected_relation)


import json
from dataclasses import asdict

if __name__ == "__main__":
    def serialize(obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)


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

    verifier = VerifyActivities(actual_data, expected_data)
    result = verifier.verify()
    print(json.dumps(asdict(result), indent=2, default=serialize))
