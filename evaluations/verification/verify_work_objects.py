import itertools
from typing import Any

from evaluations.verification import VerifyOutput, normalize_text, count_primitive_kv_pairs, \
    semantic_similarity
from verification import VerificationResult
from verification.stats import WorkObjectStats


def group_by_instance(expected_work_objects: list[dict]) -> list[Any]:
    return list(itertools.chain.from_iterable(x['instances'] for x in expected_work_objects))


def group_by_name(expected_work_objects: list[dict]) -> dict[str, dict]:
    return {normalize_text(obj["name"]): obj for obj in expected_work_objects}


class VerifyWorkObjects(VerifyOutput):
    """Verifier for work objects comparing against an expected output"""

    def verify(self) -> VerificationResult[WorkObjectStats]:
        # count total key-value pairs in the specified fields
        included_fields_for_counting = ["name", "description", "instances"]
        total_fields = count_primitive_kv_pairs(self.expected_output, included_fields_for_counting)

        correct_fields = 0
        missing_fields = WorkObjectStats()
        hallu_fields = WorkObjectStats()

        expected_names = group_by_name(self.expected_output)
        actual_names = group_by_name(self.actual_output)

        expected_names_keys = set(expected_names.keys())  # a set of str
        actual_names_keys = set(actual_names.keys())

        correct_names = expected_names_keys & actual_names_keys
        missing_names = expected_names_keys - actual_names_keys
        hallu_names = actual_names_keys - expected_names_keys

        # if missing names exist mean the whole work object was missing:
        if missing_names:
            for missed_name in missing_names:
                count_fields = count_primitive_kv_pairs(expected_names[missed_name],
                                                        included_fields_for_counting)
                missing_fields.increase_total(count_fields)
                missing_fields.work_objects.increase_total(count_fields)
                missing_fields.work_objects.add_detail(missed_name)
        # if hallu manes exist mean the whole work object was hallucinated:
        if hallu_names:
            for hallu_name in hallu_names:
                count_fields = count_primitive_kv_pairs(actual_names[hallu_name], included_fields_for_counting)
                hallu_fields.increase_total(count_fields)

        # check missing instances when the work object is correctly extracted but some instances are missing
        for name in correct_names:
            expected_obj = expected_names[name]
            output_obj = actual_names[name]

            correct_fields += 1

            # check the description
            output_description = output_obj["description"]
            expected_description = expected_obj["description"]
            description_similarity = semantic_similarity(output_description, expected_description)
            if description_similarity['similarity_score'] >= 0.75:
                correct_fields += 1
            else:
                if description_similarity['case'] == 'hallucination' or description_similarity[
                    'case'] == 'both_has_content':
                    hallu_fields.increase_total()
                if description_similarity['case'] == 'missing':
                    missing_fields.increase_total()

            # check for instances
            output_instances = output_obj["instances"]
            expected_instances = expected_obj["instances"]

            output_instances_map = {obj['instance_id']: obj['note'] for obj in output_instances}
            expected_instances_map = {obj['instance_id']: obj['note'] for obj in expected_instances}

            missing_instances = expected_instances_map.keys() - output_instances_map.keys()
            hallu_instances = output_instances_map.keys() - expected_instances_map.keys()
            correct_instances = expected_instances_map.keys() & output_instances_map.keys()

            for i in correct_instances:
                correct_fields += 1
                output_note = output_instances_map[i]
                note_similarity = semantic_similarity(output_note, expected_instances_map[i])

                if note_similarity['similarity_score'] >= 0.80:
                    correct_fields += 1  # 1 for the correct note
                else:
                    # only the instance is correct
                    if note_similarity['case'] == 'hallucination':
                        hallu_fields.increase_total()
                        hallu_fields.work_object_instances.increase_total()
                        hallu_fields.work_object_instances.add_detail(output_note)
                    if note_similarity['case'] == 'missing':
                        missing_fields.increase_total()
                        missing_fields.work_object_instances.increase_total()
                        missing_fields.work_object_instances.add_detail(output_note)

            if missing_instances:
                local_missing = len(missing_instances)
                missing_fields.increase_total(local_missing * 2)
                missing_fields.work_object_instances.increase_total(local_missing)
                missing_fields.work_object_instances.extend_details(missing_instances)

            if hallu_instances:
                local_hallu = len(hallu_instances)
                hallu_fields.increase_total(local_hallu * 2)
                hallu_fields.work_object_instances.increase_total(local_hallu)
                hallu_fields.work_object_instances.extend_details(hallu_instances)

        return VerificationResult(
            total_fields=total_fields,
            correct_fields=correct_fields,
            missing_fields=missing_fields,
            hallu_fields=hallu_fields
        )
