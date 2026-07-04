import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import spacy


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



class VerifyOutput(ABC):
    @abstractmethod
    def verify(self) -> dict[str, Any]:
        """verify if a field is correct, hallucinated or missing"""
        pass