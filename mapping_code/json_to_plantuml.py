import json

INIT_LINE = ["@startuml", "!include <domainstory/Domainstory>"]
ACTOR_STYLE = '$color="DarkGreen", $scale=1.5'


def content():
    test_path = r"C:\code\NL_2_DST\instructor\output\test_pipeline.json"
    with open(test_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data


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


def init_activities(steps: list[object]):
    activities_list = []
    for step in steps:
        for index, line in enumerate(step['lines']):
            # within the same step, only assign step number for the first activities. For substep, use empty string
            order = f'activity({step['step']}' if index == 0 else f'activity( '
            # preposition and target_id can be null
            preposition = f', {line['preposition']}' if line['preposition'] is not None else ''
            target_id = f', {line['target_id']}' if line['target_id'] is not None else ''
            action = f"{order}, {line['subject_id']}, {line['action']}, {line['object_id']} {preposition} {target_id})"
            activities_list.append(action)
    return activities_list


def create_plantuml_syntax(story_json):
    title = f'title <size:24><b>{story_json["title"]}</b></size>'
    INIT_LINE.append(title)

    # actors
    actors_list = init_actors(story_json["actors"])
    INIT_LINE.extend(actors_list)

    # sprites
    work_objects_list = init_sprites(story_json["work_objects"])
    INIT_LINE.extend(work_objects_list)

    # work object instances
    work_obj_instance_list = init_work_objects(story_json["work_object_instances"])
    INIT_LINE.extend(work_obj_instance_list)

    # activities
    activities_list = init_activities(story_json["steps"])
    INIT_LINE.extend(activities_list)

    INIT_LINE.append("@enduml")
    return "\n".join(INIT_LINE)


if __name__ == "__main__":
    json_data = content()
    print(create_plantuml_syntax(json_data))
