import json
from pathlib import Path

from pyarrow import null

ACTOR_STYLE = '$color="DarkGreen", $scale=1.5'


def init_actors(actors: list[object]):
    actors_list = []
    for actor in actors:
        init_actor = f'{actor["type"]}({actor["id"]},{actor["name"]},{ACTOR_STYLE})'
        actors_list.append(init_actor)
    return actors_list


def init_sprites(work_objects: list[object]):
    sprites_list = []
    for work_object in work_objects:
        procedure_name = work_object["id"]
        mdi_name = work_object["icon"]["mdi_name"]
        svg = work_object["icon"]["svg"]
        sprite = f"""
                sprite {mdi_name} <svg width="48" height="48"><g transform="scale(2)"><path d="{svg}" /></g></svg>\n
                !unquoted procedure {procedure_name}($name, $label = "", $tag = "", $note = "", $shape = $Object_Shape, $scale = $Object_IconScale, $color = $Object_IconColor, $background = "")\n
                  Object($name, "${mdi_name}", $name, $label, $tag, $note, $shape, $scale, $color, $background)\n
                !endprocedure
                """

        sprites_list.append(sprite)
    return sprites_list


# def init_work_objects(work_objects: list[object]):
#     work_objects_list = []
#     for work_object in work_objects:
#         work_obj_name = work_object['name']
#         work_obj_instances = work_object['instances']
#


def init_work_objects(work_obj_instances: list[object]):
    work_obj_instance_list = []

    for work_obj_instance in work_obj_instances:
        id = work_obj_instance['work_object_id']
        # the name is same as id, but writen with a space, instead of underscore
        label = id.replace("_", " ")
        note = work_obj_instance['note']

        if note is None:
            init_work_obj = f"""{id}({work_obj_instance['instance_id']}, {label})"""
        else:
            init_work_obj = f"""{id}({work_obj_instance['instance_id']}, {label}, $note="{note}")"""
        work_obj_instance_list.append(init_work_obj)
    return work_obj_instance_list


def init_activities(activities: list[object]):
    activities_list = []
    for activity in activities:
        # within the same step, only assign step number for the first activities. For substep, use empty string
        order = f'activity({activity['step']}'

        main_activity = activity['main_activity']
        # preposition and target_id can be null
        relation = f'{main_activity['relation']}' if main_activity['relation'] is not None else ''
        target_id = f'{main_activity['target_id']}' if main_activity['target_id'] is not None else ''

        # final syntax
        action = (f"{order}, {main_activity['subject_id']}, {main_activity['action']},"
                  f" {main_activity['object_id']}, {relation}, {target_id})")

        activities_list.append(action)
        sub_activities = activity['sub_activities']

        if sub_activities:
            for sub_act in sub_activities:
                sub_action = f"activity( , {sub_act['subject_id']}, {sub_act['relation']}, {sub_act['target_id']})"

                activities_list.append(sub_action)

        # print(f"activities_list: {"\n".join(activities_list)}")

    return activities_list


test = [
    {
        "step": 1,
        "text": null,
        "main_activity": {
            "line_order": 1,
            "subject_id": "online_leasing_service",
            "action": "fetches",
            "object_id": "credit_rating_report",
            "relation": "for",
            "target_id": "contract"
        },
        "sub_activities": []
    },
    {
        "step": 2,
        "text": null,
        "main_activity": {
            "line_order": 1,
            "subject_id": "rating_agency_website",
            "action": "generates",
            "object_id": "credit_rating_report",
            "relation": "for",
            "target_id": "online_leasing_service"
        },
        "sub_activities": [
            {
                "line_order": 2,
                "subject_id": "credit_rating",
                "relation": "from",
                "target_id": "rating_agency_website"
            }
        ]
    }]


# for activity in activities:
#     for index, line in enumerate(activity['lines']):
#         # within the same step, only assign step number for the first activities. For substep, use empty string
#         order = f'activity({activity['step']}' if index == 0 else f'activity( '
#         # preposition and target_id can be null
#         preposition = f', {line['preposition']}' if line['preposition'] is not None else ''
#         target_id = f', {line['target_id']}' if line['target_id'] is not None else ''
#         action = f"{order}, {line['subject_id']}, {line['action']}, {line['object_id']} {preposition} {target_id})"
#         activities_list.append(action)
# return activities_list


def create_plantuml_syntax(story_json) -> str:
    INIT_LINE = ["@startuml", "!include <domainstory/Domainstory>"]
    title = f'title <size:24><b>{story_json["title"]}</b></size>'
    INIT_LINE.append(title)

    # actors
    actors_list = init_actors(story_json["actors"])
    INIT_LINE.extend(actors_list)

    # sprites
    work_objects_list = init_sprites(story_json["work_objects"])
    INIT_LINE.extend(work_objects_list)

    # work object instances
    work_obj_instances = []
    for work_object in story_json["work_objects"]:
        for instance in work_object["instances"]:
            work_obj_instances.append({
                "work_object_id": work_object["id"],
                "instance_id": instance["instance_id"],
                "note": instance.get("note")
            })

    work_obj_instance_list = init_work_objects(work_obj_instances)
    # work_obj_instance_list = init_work_objects(story_json["work_objects"]["instances"])
    INIT_LINE.extend(work_obj_instance_list)

    # activities
    activities_list = init_activities(story_json["activities"])
    INIT_LINE.extend(activities_list)

    INIT_LINE.append("@enduml")
    return "\n".join(INIT_LINE)


def content():
    project_root = Path(__file__).parents[1]
    alphorn_3 = project_root / "alphorn-test-json" / "output_example_alphorn-2-gemini-flash2.5.json"
    with open(alphorn_3, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data


if __name__ == "__main__":
    json_data = content()
    output = Path(__file__).parent / "test.puml"
    output.write_text(create_plantuml_syntax(json_data), encoding="utf-8")
