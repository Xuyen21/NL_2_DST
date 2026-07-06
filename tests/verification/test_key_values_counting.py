from verification import count_primitive_kv_pairs


def test_key_values_counting():
    data = [
        {
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
                },
                {
                    "line_order": 3,
                    "subject_id": "information_1",
                    "relation": "from",
                    "target_id": "contract_1"
                },
            ]
        },
    ]

    fields_to_count = ['step', 'main_activity', 'sub_activities']
    total_fields = count_primitive_kv_pairs(data, fields_to_count)
    assert total_fields == 14
