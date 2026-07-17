import re
from typing import Any

from pyarrow import null

ACTOR_STYLE = '$color="DarkGreen", $scale=1.5'
JsonDict = dict[str, Any]


def sanitize_identifier(value: object, *, fallback_prefix: str = "id") -> str:
    text = str(value).strip()
    sanitized = re.sub(r"[^A-Za-z0-9_]", "_", text)
    sanitized = re.sub(r"_+", "_", sanitized).strip("_")

    if not sanitized:
        sanitized = fallback_prefix

    if sanitized[0].isdigit():
        sanitized = f"{fallback_prefix}_{sanitized}"

    return sanitized


def init_actors(actors: list[JsonDict]):
    actors_list = []
    for actor in actors:
        note = actor["note"] if actor["note"] else ""
        actor_id = sanitize_identifier(actor["id"], fallback_prefix="actor")
        init_actor = f'{actor["type"]}({actor_id},{actor["name"]},{ACTOR_STYLE}, $note="{note}")'
        actors_list.append(init_actor)
    return actors_list


def init_sprites(work_objects: list[JsonDict]):
    sprites_list = []
    for work_object in work_objects:
        procedure_name = sanitize_identifier(work_object["id"], fallback_prefix="work_object")
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


def init_work_objects(work_obj_instances: list[JsonDict]):
    work_obj_instance_list = []

    for work_obj_instance in work_obj_instances:
        work_object_id = sanitize_identifier(work_obj_instance['work_object_id'], fallback_prefix="work_object")
        instance_id = sanitize_identifier(work_obj_instance['instance_id'], fallback_prefix=work_object_id)
        # the name is same as id, but writen with a space, instead of underscore
        label = str(work_obj_instance['work_object_id']).replace("_", " ")
        note = work_obj_instance['note']

        if note is None:
            init_work_obj = f"""{work_object_id}({instance_id}, {label})"""
        else:
            init_work_obj = f"""{work_object_id}({instance_id}, {label}, $note="{note}")"""
        work_obj_instance_list.append(init_work_obj)
    return work_obj_instance_list


def init_activities(activities: list[JsonDict]):
    activities_list = []
    for activity in activities:
        # within the same step, only assign step number for the first activities. For substep, use empty string
        order = f'activity({activity['step']}'

        main_activity = activity['main_activity']
        # preposition and target_id can be null
        relation = f'{main_activity['relation']}' if main_activity['relation'] is not None else ''
        target_id = sanitize_identifier(main_activity['target_id'], fallback_prefix="target") if main_activity[
                                                                                                     'target_id'] is not None else ''
        subject_id = sanitize_identifier(main_activity['subject_id'], fallback_prefix="subject")
        object_id = sanitize_identifier(main_activity['object_id'], fallback_prefix="object")

        # final syntax
        action = (f"{order}, {subject_id}, {main_activity['action']},"
                  f" {object_id}, {relation}, {target_id})")

        activities_list.append(action)
        sub_activities = activity['sub_activities']

        if sub_activities:
            for sub_act in sub_activities:
                sub_subject_id = sanitize_identifier(sub_act['subject_id'], fallback_prefix="subject")
                sub_target_id = sanitize_identifier(sub_act['target_id'], fallback_prefix="target")
                sub_action = f"activity( , {sub_subject_id}, {sub_act['relation']}, {sub_target_id})"
                activities_list.append(sub_action)

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
