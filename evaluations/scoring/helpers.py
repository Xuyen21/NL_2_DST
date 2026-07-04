import itertools
import json
import spacy
from pathlib import Path
from typing import Any, Set, Dict


def normalize_text(text):
    text = str(text).lower().strip()
    return text


def load_json(file_path):
    return json.loads(Path(file_path).read_text(encoding="utf-8"))


def count_primitive_kv_pairs(data, include_fields: list[str] | None = None) -> int:
    # Convert to set once at the top level for fast O(1) lookups
    if include_fields is not None:
        include_fields = set(include_fields)

    def traverse_data(data_node, force_include: bool = False) -> int:
        count = 0

        if isinstance(data_node, dict):
            for key, value in data_node.items():
                is_primitive = not isinstance(value, (dict, list))

                matches = (include_fields is None) or force_include or (key in include_fields)

                if is_primitive and matches:
                    count += 1

                # If this key matched our filter, force all its descendants to be counted
                next_force = force_include or (include_fields is not None and key in include_fields)

                # Keep digging recursively
                count += traverse_data(value, force_include=next_force)

        elif isinstance(data_node, list):
            for item in data_node:
                # Lists don't have keys, pass the current state down
                count += traverse_data(item, force_include=force_include)

        return count

    # Start the recursive search
    return traverse_data(data)


# Load the medium english model
# interminal: python -m spacy download en_core_web_md
nlp = spacy.load("en_core_web_md")


def semantic_similarity(extracted_text, expected_text):
    # 1. Safely handle None values by converting them to strings and stripping spaces
    actual_text = str(extracted_text).strip() if extracted_text else ""
    exp_text = str(expected_text).strip() if expected_text else ""

    result = {'similarity_score': 0.0,
              'case': ''}

    # 2. Catch the empty/null cases BEFORE asking spaCy to do any math
    if not actual_text and not exp_text:
        # Both are empty/null.
        result['similarity_score'] = 1.0
        result['case'] = 'both_empty'
        return result
    if not actual_text and exp_text:
        # Extracted is empty/null, expected is not --> hallucination
        result['similarity_score'] = 0.0
        result['case'] = 'missing'
        return result
    if actual_text and not exp_text:
        print(
            'Warning: Expected text is not empty, but extracted text is empty. This may indicate a missing extraction.')
        # Extracted is not empty/null, expected is --> omission
        result['similarity_score'] = 0.0
        result['case'] = 'hallucination'
        return result

    # 3. Only run the NLP math if both strings actually contain words
    a = nlp(exp_text)
    b = nlp(actual_text)

    # 4. Compare the average word vectors
    similarity = a.similarity(b)
    result['similarity_score'] = round(similarity, 2)
    result['case'] = 'both_has_content'

    return result


def eval_work_objects(output_work_objects: list[dict], expected_work_objects: list[dict]) -> dict[str, int]:
    # couunt total key-value pairs in the specified fields
    included_fields_for_counting = ["name", "description", "instances"]
    total_fields = count_primitive_kv_pairs(expected_work_objects, included_fields_for_counting)

    # init
    correct_fields = 0
    missing_fields = init_fields()
    hallu_fields = init_fields()

    expected_names_map = group_by_name(expected_work_objects)
    # expected_instances_list = group_by_instance(expected_work_objects)
    # expected_instances_map = {obj['instance_id']: obj['note'] for obj in expected_instances_list}

    # print(f'expected name map {expected_names_map}')
    output_names_map = group_by_name(output_work_objects)
    # output_instances_list = group_by_instance(output_work_objects)
    # output_instances_map = {obj['instance_id']: obj['note'] for obj in output_instances_list}

    expected_names = set(expected_names_map.keys())  # a set of str
    output_names = set(output_names_map.keys())

    correct_names = expected_names & output_names
    missing_names = expected_names - output_names
    hallu_names = output_names - expected_names

    # if missing names exist mean the whole work object was missing:
    if missing_names:
        for missed_name in missing_names:
            count_fields = count_primitive_kv_pairs(expected_names_map[missed_name], included_fields_for_counting)
            missing_fields['total'] += count_fields
            details = missing_fields['work_object']['detail']
            missing_fields['work_object']['total'] += count_fields
            details.append(missed_name)
            # print(f'added {count_fields} to missing fields')

    # if hallu manes exist mean the whole work object was hallucinated:
    if hallu_names:
        for hallu_name in hallu_names:
            count_fields = count_primitive_kv_pairs(output_names_map[hallu_name], included_fields_for_counting)
            hallu_fields['total'] += count_fields
            print(f'added {count_fields} to hallu fields')

    # check missing instances when the work object is correctly extracted but some instances are missing
    for name in correct_names:
        expected_obj = expected_names_map[name]
        output_obj = output_names_map[name]

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

        # print(f'missing_instances: {missing_instances}, total: {len(missing_instances)}')
        # print(f'hallu_instances: {hallu_instances}, total: {len(hallu_instances)}')
        # print(f'correct_instances: {correct_instances}, total: {len(correct_instances)}')

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
            missing_fields['total'] = missing_fields + (local_missing * 2)
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


def group_by_instance(expected_work_objects: list[dict]) -> list[Any]:
    return list(itertools.chain.from_iterable(x['instances'] for x in expected_work_objects))


def group_by_name(expected_work_objects: list[dict]) -> dict[str, dict]:
    return {normalize_text(obj["name"]): obj for obj in expected_work_objects}


def init_fields() -> dict[str, int | dict[str, int | list[Any]]]:
    return {'total': 0,
            'work_object': {
                'total': 0,
                'detail': []
            },
            'work_object_instances': {
                'total': 0,
                'detail': []
            },
            'note': {
                'total': 0,
                'detail': []
            }
            }


def eval_actors(extracted_actors: list[dict], expected_actors: list[dict]) -> Dict[str, int]:
    # Map normalized expected names to their full objects for instant lookup
    expected_names_map = {normalize_text(obj["name"]): obj for obj in expected_actors}

    correct_fields = 0
    extra_fields = 0

    for output_obj in extracted_actors:
        obj_name = normalize_text(output_obj.get("name", ""))
        obj_type = output_obj.get("type")

        # Check if the generated work object exists in our expected map
        if obj_name in expected_names_map:
            # 1. The name matched correctly
            correct_fields += 1

            # Fetch the actual expected object using the name as the key
            expected_object = expected_names_map[obj_name]

            # 2. Go further to check if the type matches
            if obj_type == expected_object.get("type"):
                correct_fields += 1
            else:
                # Name matched, but type was incorrect (1 extra incorrect field)
                extra_fields += 1
        else:
            # The entire output work object wasn't in the expected list (2 extra incorrect fields)
            extra_fields += 2

    # Missing fields are simply whatever expected fields we failed to match
    # missing_fields = total_fields - correct_fields
    #
    # return {
    #     "total_fields": total_fields,
    #     "correct_fields": correct_fields,
    #     "missing_fields": missing_fields,
    #     "extra_fields": extra_fields,
    # }


if __name__ == "__main__":
    # output_story_1 = r"C:\code\NL_2_DST\alphorn-test-json\output_example_alphorn-1-gemini-flash2.5.json"
    # expected_1 = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn-gold-standard\gold-alphorn-1.json"

    output2 = r"C:\code\NL_2_DST\alphorn-test-json\output_example_alphorn-2-gemini-flash2.5.json"
    expected_2 = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn-gold-standard\gold-alphorn-2.json"

    output = load_json(output2)
    expected_output = load_json(expected_2)

    # output_actors = output["actors"]
    # expected_actors = expected_output["actors"]

    output_work_objects = output["work_objects"]
    expected_work_objects = expected_output["work_objects"]

    test = eval_work_objects(output_work_objects, expected_work_objects)
    print(f"Evaluation results: {test}")
