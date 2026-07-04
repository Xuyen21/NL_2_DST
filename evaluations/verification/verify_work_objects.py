import itertools
from typing import Any

from evaluations.verification import VerifyOutput, init_fields, normalize_text, count_primitive_kv_pairs, \
    semantic_similarity


def group_by_instance(expected_work_objects: list[dict]) -> list[Any]:
    return list(itertools.chain.from_iterable(x['instances'] for x in expected_work_objects))


def group_by_name(expected_work_objects: list[dict]) -> dict[str, dict]:
    return {normalize_text(obj["name"]): obj for obj in expected_work_objects}


class VerifyWorkObjects(VerifyOutput):
    """Verifier for work objects comparing against an expected output"""

    def __init__(self, actual_output: list[dict], expected_output: list[dict]):
        self.actual_output = actual_output
        self.expected_output = expected_output

    def verify(self) -> dict[str, Any]:
        # count total key-value pairs in the specified fields
        included_fields_for_counting = ["name", "description", "instances"]
        total_fields = count_primitive_kv_pairs(self.expected_output, included_fields_for_counting)

        correct_fields = 0
        missing_fields = init_fields()
        hallu_fields = init_fields()

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
                missing_fields['total'] += count_fields
                details = missing_fields['work_object']['detail']
                missing_fields['work_object']['total'] += count_fields
                details.append(missed_name)
                # print(f'added {count_fields} to missing fields')

        # if hallu manes exist mean the whole work object was hallucinated:
        if hallu_names:
            for hallu_name in hallu_names:
                count_fields = count_primitive_kv_pairs(actual_names[hallu_name], included_fields_for_counting)
                hallu_fields['total'] += count_fields
                print(f'added {count_fields} to hallu fields')

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
                # print(f"Description similarity for '{extracted_name}' is {description_similarity} (correct)")
            else:
                if description_similarity['case'] == 'hallucination' or description_similarity[
                    'case'] == 'both_has_content':
                    hallu_fields['total'] += 1
                    print(f"HALLU INSTANCE!!! ouput: {output_description}")
                if description_similarity['case'] == 'missing':
                    missing_fields['total'] += 1
                    print(f"MISSING INSTANCE!!!, expected {expected_description}")
                # print(f"Description similarity for '{output_description}' is {description_similarity} (incorrect)")

            # check for instances
            output_instances = output_obj["instances"]
            expected_instances = expected_obj["instances"]

            output_instances_map = {obj['instance_id']: obj['note'] for obj in output_instances}
            expected_instances_map = {obj['instance_id']: obj['note'] for obj in expected_instances}
            # print(f'output_instances_map: {output_instances_map}')
            # print(f'expected_instances_map: {expected_instances_map}')

            missing_instances = expected_instances_map.keys() - output_instances_map.keys()
            hallu_instances = output_instances_map.keys() - expected_instances_map.keys()
            correct_instances = expected_instances_map.keys() & output_instances_map.keys()

            for i in correct_instances:
                correct_fields += 1
                output_note = output_instances_map[i]
                note_similarity = semantic_similarity(output_note, expected_instances_map[i])
                print(f'output note: {output_note}, expected note: {expected_instances_map[i]}')

                # print(f"Note similarity for instance '{i}' is {note_similarity}")
                if note_similarity['similarity_score'] >= 0.80:
                    correct_fields += 1  # 1 for the correct note
                else:
                    # only the instance is correct
                    if note_similarity['case'] == 'hallucination':
                        hallu_fields['total'] += 1
                        hallu_fields['work_object_instances']['total'] += 1
                        hallu_fields['work_object_instances']['detail'].append(output_note)
                        print('HALLU INSTANCE!!!')
                    if note_similarity['case'] == 'missing':
                        missing_fields['total'] += 1
                        missing_fields['work_object_instances']['total'] += 1
                        details = (missing_fields['work_object_instances']['detail'])
                        details.append(output_note)
                        print(f'MISSING INSTANCE!!!')

                    # print(f"Note similarity for instance '{i}' is {note_similarity} (incorrect)")

            if missing_instances:
                local_missing = len(missing_instances)
                missing_fields['total'] = missing_fields['total'] + (local_missing * 2)
                missing_fields['work_object_instances']['total'] += local_missing
                details = missing_fields['work_object_instances']['detail']
                details.append(missing_instances)
                print(f"Missing instances for work object '{name}': {missing_instances}")

            if hallu_instances:
                local_hallu = len(hallu_instances)
                hallu_fields['total'] = hallu_fields['total'] + (local_hallu * 2)
                hallu_fields['work_object_instances']['total'] += local_hallu

                details = hallu_fields['work_object_instances']['detail']
                details.append(hallu_instances)

                print(f"Hallucinated instances: {hallu_instances}, total: {local_hallu}")

        return {
            "total_fields": total_fields,
            "correct_fields": correct_fields,
            "missing_fields": missing_fields,
            "hallu_fields": hallu_fields,
        }