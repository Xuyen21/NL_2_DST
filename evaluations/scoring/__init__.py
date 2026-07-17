# calculate Pass Rate = correct_fields/ total fields for the entire schema
import json
from dataclasses import asdict

from verification import load_json
from verification.verify_activities import VerifyActivities
from verification.verify_actors import VerifyActors
from verification.verify_work_objects import VerifyWorkObjects


def evaluate(actual_output: dict, expected_output: dict) -> dict:
    def serialize(obj):
        if hasattr(obj, "__dict__"):
            return obj.__dict__
        return str(obj)

    actual_actors = actual_output["actors"]
    expected_actors = expected_output["actors"]

    actual_work_objects = actual_output["work_objects"]
    expected_work_objects = expected_output["work_objects"]

    actual_activities = actual_output["activities"]
    expected_activities = expected_output["activities"]

    calc_actors = VerifyActors(actual_actors, expected_actors)
    actors_verification_result = calc_actors.verify()
    total_actors_fields = actors_verification_result.total_fields
    total_correct_actors = actors_verification_result.correct_fields

    calc_work_objects = VerifyWorkObjects(actual_work_objects, expected_work_objects)
    work_objects_verification_result = calc_work_objects.verify()
    total_work_objects_fields = work_objects_verification_result.total_fields
    total_correct_work_objects = work_objects_verification_result.correct_fields

    calc_activities = VerifyActivities(actual_activities, expected_activities)
    activities_verification_result = calc_activities.verify()
    total_activities_fields = activities_verification_result.total_fields
    total_correct_activities = activities_verification_result.correct_fields

    total_fields = total_actors_fields + total_work_objects_fields + total_activities_fields
    total_correct_fields = total_correct_actors + total_correct_work_objects + total_correct_activities

    pass_rate = round(total_correct_fields / total_fields, 2)

    actors_full_info = json.loads(json.dumps(asdict(actors_verification_result), default=serialize))
    work_objects_full_info = json.loads(json.dumps(asdict(work_objects_verification_result), default=serialize))
    activities_full_info = json.loads(json.dumps(asdict(activities_verification_result), default=serialize))

    print(f'type of actors full info: {type(actors_full_info)}')

    return {
        "pass_rate": pass_rate,
        "total_fields": total_fields,
        "correct_fields": total_correct_fields,
        "actors_stats": {
            "total": actors_full_info['total_fields'],
            "corrects": actors_full_info['correct_fields'],
            "missings": actors_full_info['missing_fields']['total'],
            "hallu": actors_full_info['hallu_fields']['total'],
        },
        "work_objects_stats": {
            "total": work_objects_full_info['total_fields'],
            "corrects": work_objects_full_info['correct_fields'],
            "missings": work_objects_full_info['missing_fields']['total'],
            "hallu": work_objects_full_info['hallu_fields']['total'],
        },
        "activities_stats": {
            "total": activities_full_info['total_fields'],
            "corrects": activities_full_info['correct_fields'],
            "missings": activities_full_info['missing_fields']['total'],
            "hallu": activities_full_info['hallu_fields']['total'],
        }
    }


if __name__ == "__main__":
    actual_story_3 = r'C:\code\NL_2_DST\alphorn-test-json\output_example_alphorn-3.json'
    expected_story_3 = r'C:\code\NL_2_DST\evaluations\promptfoo_eval\alphorn-gold-standard\gold-alphorn-3.json'

    actual = load_json(actual_story_3)
    expected = load_json(expected_story_3)

    print(evaluate(actual, expected))
