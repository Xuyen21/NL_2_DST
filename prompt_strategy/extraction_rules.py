zero_shot_promt = """
You are an expert in Domain Storytelling for Car Leasing.
Extract a structured Domain Story with actors, canonical work objects, work object instances, and ordered story steps.

1. ACTOR: Performs an action (e.g., 'The Dealer calculates').
2. WORK OBJECT: Is acted upon (e.g., 'The Dealer signs the Contract').
3. PASSIVE SYSTEMS: If a system is just a place for storage (e.g., 'stored in the database'),
   it is a Work Object.
4. Create one canonical WorkObject per unique work object concept.
5. Create one WorkObjectInstance for each appearance of a work object in the story. Use instance ids in the form '{work_object_id}_{n}', such as 'car_1' and 'car_2'.
6. The note of a WorkObjectInstance must contain only explicit wording written in the text for that occurrence. If there is no explicit qualifier, return null.
7. Represent each numbered sentence as one StoryStep.
8. Each StoryStep contains ordered ActivityLine entries that are ready to map to PlantUML activity(...) lines.
9. Split long sentences into multiple ActivityLine entries when needed. The first line usually starts with an actor id, while continuation lines may start with a work_object_instance id.
10. Use preposition and target_id only when a PlantUML line needs a trailing ', preposition, target' pair.
"""