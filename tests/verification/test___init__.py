"""
Unit tests for evaluations/verification/__init__.py
(shared helper functions: normalize_text, count_primitive_kv_pairs,
semantic_similarity, init_fields)
"""
from evaluations.verification import (
    count_primitive_kv_pairs,
    normalize_text,
    semantic_similarity,
)


# ===========================================================================
# normalize_text
# ===========================================================================
class TestNormalizeText:
    def test_lowercases(self):
        assert normalize_text("Hello World") == "hello world"

    def test_strips_whitespace(self):
        assert normalize_text("  hello  ") == "hello"

    def test_converts_none_to_string(self):
        assert normalize_text(None) == "none"

    def test_converts_int(self):
        assert normalize_text(42) == "42"


# ===========================================================================
# count_primitive_kv_pairs
# ===========================================================================
class TestCountPrimitiveKvPairs:
    def test_flat_dict_no_filter(self):
        data = {"a": 1, "b": "x", "c": True}
        assert count_primitive_kv_pairs(data) == 3

    def test_nested_dict_no_filter(self):
        data = {"a": {"b": 1, "c": 2}}
        assert count_primitive_kv_pairs(data) == 2

    def test_list_of_dicts(self):
        data = [{"name": "foo"}, {"name": "bar"}]
        assert count_primitive_kv_pairs(data) == 2

    def test_include_fields_filters_correctly(self):
        data = [{"name": "foo", "type": "Person", "id": "foo_id"}]
        assert count_primitive_kv_pairs(data, include_fields=["name", "type"]) == 2

    def test_include_fields_counts_nested_under_matched_key(self):
        # 'instances' matched → its children are force-included
        data = {
            "name": "contract",
            "instances": [{"instance_id": "c1", "note": None}],
        }
        # 'name' = 1 + 'instance_id' + 'note' = 3 total
        assert count_primitive_kv_pairs(data, include_fields=["name", "instances"]) == 3

    def test_empty_data(self):
        assert count_primitive_kv_pairs({}) == 0
        assert count_primitive_kv_pairs([]) == 0


# ===========================================================================
# semantic_similarity
# ===========================================================================
class TestSemanticSimilarity:
    def test_both_empty(self):
        result = semantic_similarity("", "")
        assert result["similarity_score"] == 1.0
        assert result["case"] == "both_empty"

    def test_both_none(self):
        result = semantic_similarity(None, None)
        assert result["similarity_score"] == 1.0
        assert result["case"] == "both_empty"

    def test_extracted_empty_expected_not(self):
        result = semantic_similarity("", "expected text")
        assert result["similarity_score"] == 0.0
        assert result["case"] == "missing"

    def test_extracted_not_empty_expected_empty(self):
        result = semantic_similarity("extracted text", "")
        assert result["similarity_score"] == 0.0
        assert result["case"] == "hallucination"

    def test_identical_texts_high_similarity(self):
        result = semantic_similarity("legal agreement", "legal agreement")
        assert result["similarity_score"] >= 0.99
        assert result["case"] == "both_has_content"

    def test_similar_texts_reasonable_score(self):
        result = semantic_similarity("billing document", "invoice document")
        assert 0.5 <= result["similarity_score"] <= 1.0

    def test_unrelated_texts_lower_score(self):
        similar = semantic_similarity("cat", "cat")
        unrelated = semantic_similarity("cat", "invoice")
        assert similar["similarity_score"] > unrelated["similarity_score"]