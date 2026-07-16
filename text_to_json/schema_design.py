from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ActorType(str, Enum):
    PERSON = "Person"
    GROUP = "Group"
    SYSTEM = "System"


class Actor(BaseModel):
    id: str = Field(
        description="Unique identifier for the actor, usually the same as the name."
    )
    name: str = Field(
        description="The 'who'—Person/people or System that performs an action."
    )
    type: ActorType = Field(
        description="The type of actor: Person, Group of Persons, or System."
    )
    note: Optional[str] = Field(
        default=None,
        description="Optional note about the actor, extracted only when the input explicitly includes a note label or text in parentheses."
    )


class Icon(BaseModel):
    mdi_name: Optional[str] = None
    svg: Optional[str] = None
    # confidence: Optional[float] = None


class WorkObjectInstance(BaseModel):
    instance_id: str = Field(
        description=(
            "Unique identifier for this occurrence of a work object in the story. "
            "Format it as '{work_object_id}_{n}', where n starts at 1 and increments "
            "for each repeated appearance of the same work object, for example 'car_1', 'car_2'."
        )
    )
    note: str | None = Field(
        default=None,
        description=(
            "Use only for multi-word temporal clauses, conditional states, or explicit user notes. "
            "Include text that appears in parentheses and orphaned temporal or conditional phrases "
            "(e.g., 'after the leasing period', 'in the event of failure', 'if approved'). "
            "Exclude single adjectives (e.g., 'specific', 'new') and single-word adverbs (e.g., 'regularly', 'automatically'). "
            "If no qualifying phrase or explicit note is present, set this to null."
        ),
    )


class WorkObject(BaseModel):
    id: str = Field(
        description="Unique identifier for the work object,the same as the name but connected words using underscores."
    )

    name: str = Field(
        description=(
            "The concrete name of the work object; the 'what' that is acted upon, exchanged, or used. For example 'catalog'."
            "Grammatical constraint: Only extract nouns that act as the direct receiver (direct object) of the main activity verb. "
            "Do not extract nouns if they are functioning as modifiers, bridges, temporal phases (e.g., 'leasing period', 'shift'), "
            "or conditions trapped inside prepositional phrases (e.g., 'after...', 'during...', 'based on...')."
        )
    )

    description: str = Field(
        description=(
            "A short, generic concept phrase (ideally from 1-6 words) describing what the work object is about for semantic icon search. The description for Icon used in Car leasing domain"
            "Focus only on the core object itself, not the story context, actors, actions, or relations. "
            "Keep it concise and concept-based."
        )
    )

    instances: list[WorkObjectInstance] = Field(
        description="A list of all specific occurrences of this work object throughout the story."
    )

    icon: Optional[Icon]


class MainActivity(BaseModel):
    subject_id: str = Field(
        description="Primary actor or system of the first activity line."
    )
    action: str = Field(
        description=(
            "Predicate of the first activity line. "
            "If the verb relies on a preposition to connect to the work object "
            "(e.g., 'informs about', 'asks for'), absorb that preposition into this field."
        )
    )
    object_id: str = Field(
        description=(
            "The ID of the work object being exchanged. "
            "This value must exactly match an existing WorkObjectInstance.instance_id "
            "from the work_objects list. Never invent a new ID."
        )
    )
    relation: str | None = Field(
        default=None,
        description=(
            "The pure edge label connecting the primary object to a secondary target. "
            "Graph chaining rule: when there is a chain of multiple nested work objects "
            "(e.g., 'contract for a car with an installment') going to a final receiving actor ('to the customer'), "
            "leave this null and push the routing relation (e.g., 'to') to the final SubActivity instead."
        ),

    )
    target_id: str | None = Field(
        default=None,
        description=(
            "(Optional) The ID of a secondary actor or another work object instance. "
            "Graph chaining rule: when the sentence specifies a final receiving actor (e.g., 'customer') "
            "but a chain of multiple work objects modifies the primary object, do not attach the receiving actor here. "
            "Leave target_id null and defer the receiving actor to the target_id of the very last SubActivity in the chain."
        ),
    )


class SubActivity(BaseModel):
    line_order: int = Field(
        description="Order of the continuation line within the same step, starting at 2."
    )
    subject_id: str = Field(
        description=(
            "The ID of the entity that this continuation branches from. "
            "Strict chaining rule: form a continuous, single-path linear chain. "
            "If line_order is 2, this must exactly match the object_id (or target_id) of the MainActivity. "
            "If line_order is > 2, this must exactly match the target_id of the immediately preceding SubActivity (line_order - 1). "
            "Never branch back to earlier objects in the chain. For example, if line 3 targets 'contract', line 4's subject must be 'contract'."
        )
    )
    relation: str = Field(
        description=(
            "The contextual phrase or edge label connecting the subject to the target in this continuation. "
            "Extract the full relational context (e.g., 'on', 'stored in', 'derived from', 'based on'). "
            "Do not include nouns that act as direct work objects; only include the phrasing that bridges the two systems or objects."
        )
    )
    target_id: str = Field(
        description=(
            "The ID of the secondary actor or another work object instance that receives this continuation. "
            # "For example, if the chain is 'car' -> 'with' -> 'monthly_installment', this field is 'monthly_installment'."
        )
    )


class Activity(BaseModel):
    step: int
    text: str | None = None
    main_activity: MainActivity
    sub_activities: List[SubActivity] = Field(default_factory=list)


class DomainStory(BaseModel):
    title: str = Field(
        description="A short title summarizing the story, prioritize if user explicitly provides it."
    )
    actors: List[Actor]
    work_objects: List[WorkObject]
    activities: List[Activity] = Field(default_factory=list)


class DomainStory_Fewshot_CoT(BaseModel):
    user_input: Optional[str] = Field(
        None,
        description="Leave this field blank/null. It is only for reference in examples.",
    )
    steps: List[Activity] = Field(default_factory=list)
    title: str = Field(
        description="A short title summarizing the story, prioritize if user explicitly provides it."
    )
    actors: List[Actor]
    work_objects: List[WorkObject]
    work_object_instances: List[WorkObjectInstance] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)

    # provide examples:
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                # ----------------- example 1 -------------
                {
                    "reasoning": "The text outlines a vehicle damage reporting workflow. The 'Customer' is a Person actor, and the 'Leasing company' (referred to as 'the company' in later steps) is an organization/System actor. The objects being handled are the 'damage', 'leased vehicle', 'damage report', 'contract conditions', and 'repair order'. Step 4 contains a conditional constraint noted at the end of the text.",
                    "user_input": "1.The customer reports damage to the leased vehicle.\n2.The leasing company registers the damage report.\n3. The company checks the contract conditions.\n4. The company creates a repair order.\nNote: when the damage is covered",
                    "title": "Leased Vehicle Damage Reporting Process",
                    "actors": [
                        {"id": "actor_1", "name": "Customer", "type": "Person"},
                        {"id": "actor_2", "name": "Leasing company", "type": "System"},
                    ],
                    "work_objects": [
                        {"id": "wo_1", "name": "damage"},
                        {"id": "wo_2", "name": "leased vehicle"},
                        {"id": "wo_3", "name": "damage report"},
                        {"id": "wo_4", "name": "contract conditions"},
                        {"id": "wo_5", "name": "repair order"},
                    ],
                    "work_object_instances": [
                        {"id": "woi_1", "work_object_id": "wo_1", "state": "reported"},
                        {"id": "woi_2", "work_object_id": "wo_2", "state": "damaged"},
                        {
                            "id": "woi_3",
                            "work_object_id": "wo_3",
                            "state": "registered",
                        },
                        {"id": "woi_4", "work_object_id": "wo_4", "state": "checked"},
                        {"id": "woi_5", "work_object_id": "wo_5", "state": "created"},
                    ],
                    "steps": [
                        {
                            "step_number": 1,
                            "actor_id": "actor_1",
                            "activity": "reports",
                            "work_object_instance_ids": ["woi_1", "woi_2"],
                            "target_id": "actor_2",
                        },
                        {
                            "step_number": 2,
                            "actor_id": "actor_2",
                            "activity": "registers",
                            "work_object_instance_ids": ["woi_3"],
                        },
                        {
                            "step_number": 3,
                            "actor_id": "actor_2",
                            "activity": "checks",
                            "work_object_instance_ids": ["woi_4"],
                        },
                        {
                            "step_number": 4,
                            "actor_id": "actor_2",
                            "activity": "creates",
                            "work_object_instance_ids": ["woi_5"],
                            "note": "When the damage is covered",
                        },
                    ],
                }
            ]
        },
        # ----------------- example 2 -------------
    )


class DomainTest(BaseModel):
    actors: List[Actor]
    work_objects: List[WorkObject]
