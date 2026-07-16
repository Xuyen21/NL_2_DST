from evaluations.verification import VerifyOutput, normalize_text, semantic_similarity
from verification import VerificationResult, count_primitive_kv_pairs
from verification.stats import ActorsStats
from verification.verify_work_objects import group_by_key


class VerifyActors(VerifyOutput):
    """Verifier for actors comparing against an expected output"""

    def __init__(self, actual_output, expected_output):
        super().__init__(actual_output, expected_output)
        self.total_fields = 0
        self.correct_fields = 0
        self.missing_fields = ActorsStats()
        self.hallu_fields = ActorsStats()

    def exact_match(self, actual_output: str | int, expected_output: str | int):
        if actual_output == expected_output:
            self.correct_fields += 1

        elif not actual_output and expected_output:
            self.missing_fields.increase_total()
            self.missing_fields.names.add_detail(str(actual_output))

        else:
            self.hallu_fields.increase_total()
            self.hallu_fields.names.add_detail(str(actual_output))

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

    def verify(self) -> VerificationResult[ActorsStats]:
        include_fields_for_counting = ["name", "type", "note"]
        self.total_fields = count_primitive_kv_pairs(self.expected_output, include_fields_for_counting)

        actual_actors = group_by_key("name", self.actual_output)
        expected_actors = group_by_key("name", self.expected_output)

        actual_name_key = set(actual_actors.keys())
        expected_names_key = set(expected_actors.keys())

        correct_names = actual_name_key & expected_names_key
        missing_names = expected_names_key - actual_name_key
        hallu_names = actual_name_key - expected_names_key

        if missing_names:
            for missed_name in missing_names:
                self.missing_fields.increase_total(3)
                self.missing_fields.names.add_detail(missed_name)

        if hallu_names:
            for hallu_name in hallu_names:
                self.hallu_fields.increase_total(3)
                self.hallu_fields.names.add_detail(hallu_name)

        for name in correct_names:
            self.correct_fields += 1

            actual_obj = actual_actors[name]['type']
            expected_obj = expected_actors[name]['type']
            self.exact_match(actual_obj, expected_obj)

            actual_note = actual_actors[name]['note']
            expected_note = expected_actors[name]['note']
            self.semantic_match(actual_note, expected_note)

        return VerificationResult(
            total_fields=self.total_fields,
            correct_fields=self.correct_fields,
            missing_fields=self.missing_fields,
            hallu_fields=self.hallu_fields,
        )
