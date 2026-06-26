rules = """
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

SYSTEM_PROMPT = """You are an expert assistant specialized in recognizing and understanding named entities
and their interrelations in Domain Storytelling. You are adept at filtering and presenting only the
relevant and valid results. You will exclude any entities or activities that are not pertinent or are
inaccurate according to the text."""

# Damage report handling
few_shot_example_1 = """
1.The customer reports damage to the leased vehicle.

2.The leasing company registers the damage report.

3. The company checks the contract conditions.

4. The company creates a repair order.
Note: when the damage is covered

""" #5. Company informs the customer about the next steps.

few_shot_example_1_solution = {
    "actors": [
        "online leasing service",
        "rating agency website",
        "risk manager"
    ],
    "work_objects": [
        "contract",
        "credit rating",
        "credit rating report",
        "risk assessment",
        "voting result",
        "voted contract",
        "decision"
    ],
    "activities": [
        {
            "step": 1,
            "actor": "online leasing service",
            "action": "fetches",
            "work_object": "credit rating",
            "from": "rating agency website",
            "for": "contract"
        },
        {
            "step": 2,
            "actor": "rating agency website",
            "action": "generates",
            "work_object": "credit rating report",
            "for": "online leasing service"
        },
        {
            "step": 3,
            "actor": "online leasing service",
            "action": "creates",
            "work_object": "risk assessment",
            "for": "contract",
            "based_on": "credit rating report",
            "in": "risk management system"
        },
        {
            "step": 4,
            "actor": "online leasing service",
            "action": "notifies",
            "recipient": "risk manager",
            "about": "credit rating"
        },
        {
            "step": 5,
            "actor": "risk manager",
            "action": "decides",
            "work_object": "voting result",
            "for": "risk assessment"
        },

    ]
}

# Vehicle handover
few_shot_example_2 = """ 
1. The leasing company schedules a pickup appointment with the customer.
2. On the appointment day, the company verifies the signed contract and the customer’s identity.
3. Then the vehicle is handed over to the customer.
4. The handover is recorded in the system.
"""
few_shot_example_2_solution = """

"""
# "gemini/gemini-3.1-pro-preview", #"claude-sonnet-4-6", #"gpt-5.4",
