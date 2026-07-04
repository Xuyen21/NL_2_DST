from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ActorType(str, Enum):
    PERSON = "Person"
    GROUP = "Group"
    SYSTEM = "System"


# --- 1. Define the Schema ---
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


# class WorkObjectType(str, Enum):
#     CALL = "Call"
#     INFO = "Info"
#     FOLDER = "Folder"
#     CONVERSATION = "Conversation"
#     DOCUMENT = "Document"
#     EMAIL = "Email"
#     OTHER = "Other"


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
            "Strictly for multi-word temporal clauses, conditional states, or explicit user notes. "
            "Extract explicit notes (e.g., text in parentheses) AND orphaned temporal/conditional phrases "
            "(e.g., 'after the leasing period', 'in the event of failure', 'if approved'). "
            "CRITICAL: Do NOT extract standard adjectives (e.g., 'specific', 'new') or single-word adverbs (e.g., 'regularly', 'automatically', 'quickly'). "
            "These minor descriptive words must be completely ignored. If there is no multi-word temporal/conditional phrase or explicit note, leave null."
        ),
    )
    # work_object_id: str = Field(
    #     description=(
    #         "The ID of the canonical work object that this instance refers to. "
    #         "This value must exactly match one existing WorkObject.id in the work_objects list. DON'T event new ID."
    #     )
    # )


class WorkObject(BaseModel):
    id: str = Field(
        description="Unique identifier for the work object, usually the same as the name but connected words using underscores."
    )

    name: str = Field(
        description=(
            "The concrete name of the work object; the 'what' that is acted upon, exchanged, or used. For example 'catalog'."
            "Grammatical constraint: Only extract nouns that act as the direct receiver (direct object) of the main activity verb. "
            "Do not extract nouns if they are functioning as modifiers, bridges, temporal phases (e.g., 'leasing period', 'shift'), "
            "or conditions trapped inside prepositional phrases (e.g., 'after...', 'during...', 'based on...')."
        )
        # description=(
        #     "The concrete name of the work object; the 'what' that is acted upon, exchanged, or used. "
        #     "Grammatical constraint: Only extract nouns that act as the direct receiver (direct object) of the main activity verb. "
        #     "Do not extract abstract nouns if they are functioning as modifiers, bridges, or are trapped inside prepositional phrases describing the flow between two other objects."
        # )
    )
    # type: #str = Field(
    #     description=(
    #         "The most suitable generic type label for the work object. "
    #         "First prefer one of these predefined PlantUML macro types when they clearly fit the object itself: "
    #         "Call, Conversation, Document, Email, Info. "
    #         "Use Info only for a general informational item, notice, or reference information represented by the info icon. "
    #         "If none of the predefined macro types fits well, return a short generic noun phrase such as vehicle, payment, result, decision, form, or catalog."
    #     )
    # )
    description: str = Field(
        description=("A short, generic, concept-based description of the work object for semantic matching. ")
        #              "For example, if the text is 'credit assessment', then the description must be about the assessment of credit, not only about the credit itself. Prioritize the core concept in the description"
        #              )
        # description=(
        #     "A minimalist, generic noun phrase (1-4 words) capturing only the core conceptual essence of the work object for semantic icon search. "
        #     "CRITICAL: Strip away all context, actors, conditions, and domain-specific details. Do not explain the object. "
        #     "For example, if the object is 'credit assessment', return 'assessment'. If 'credit rating report' then 'report'"
        # )
        # description=(
        #     "A minimalist, generic noun phrase (1-4 words) capturing only the core conceptual essence of the work object for semantic icon search. "
        #     "CRITICAL: Strip away all story context, actors, and relationships. Do not explain what the object is 'for' or who it belongs to. "
        #     "For example, if the text is 'credit assessment', return exactly 'assessment'. "
        #     "If the text is 'the risk being assessed for a contract', return exactly 'risk assessment' or 'evaluation'. "
        #     "Never include secondary objects like 'contract' or 'customer' in this string, or it will ruin the semantic icon search."
        # )
    )

    instances: list[WorkObjectInstance] = Field(
        description="A list of all specific occurrences of this work object throughout the story."
    )

    icon: Optional[Icon]


class MainActivity(BaseModel):
    # line_order: int = Field(
    #     description="Always 1 for the first PlantUML activity line of the story step."
    # )
    subject_id: str = Field(
        description="Primary actor or system of the first activity line."
    )
    action: str = Field(
        # description="Predicate of the first activity line."
        description=(
            "Predicate of the first activity line. "
            "If the verb relies on a preposition to connect to the work object "
            "(e.g., 'informs about', 'asks for'), absorb that preposition into this field."
        )
    )
    object_id: str = Field(
        description=(
            "The ID of the work object that being exchange.  "
            "This value must exactly match one existing WorkObjectInstance.instance_id "
            "in the work_objects_instances list. DON'T event new ID."
        )
    )
    relation: str | None = Field(
        default=None,
        description=(
            "The pure edge label connecting the primary object to a secondary target. "
            "CRITICAL GRAPH CHAINING RULE: If there is a chain of multiple nested work objects "
            "(e.g., 'contract for a car with an installment') going to a final receiving actor ('to the customer'), "
            "DO NOT put the routing relation (e.g., 'to') here. Leave this null and push it to the final SubActivity."
        ),
        # description=(
        #     "Optional contextual phrase connecting the primary object to a secondary target. "
        #     "If abstract words like 'information' or 'data' are part of a prepositional modifier "
        #     "(e.g., 'with information from'), include them here. "
        #     "However, if those words are the direct object of the main action (e.g., 'extracts data'), "
        #     "they belong in object_id, and this field should only be the remaining connection (e.g., 'from')."
        # )
    )
    target_id: str | None = Field(
        default=None,
        description=(
            "(Optional) The ID of secondary actor or another work object instance. "
            "CRITICAL GRAPH CHAINING RULE: If the sentence specifies a final receiving actor (e.g., 'customer'), "
            "but there is a chain of multiple work objects modifying the primary object, you MUST NOT attach the receiving actor here. "
            "Leave this target_id null, and defer the receiving actor so they become the target_id of the very last SubActivity in the chain."
        ),
        # description=(
        #     "(Optional) The ID of secondary actor or another work object instance that is connected to the main object through the relation. "
        # )
    )


class SubActivity(BaseModel):
    line_order: int = Field(
        description="Order of the continuation line within the same step, starting at 2."
    )
    subject_id: str = Field(
        # description=(
        #     "The ID of the entity that this continuation branches from. "
        #     "CRITICAL: This can be the object_id or target_id from the MainActivity, OR the target_id of a previous SubActivity. "
        #     "It must be a Work Object, not an Actor."
        # )
        description=(
            "The ID of the entity that this continuation branches from. "
            "CRITICAL STRICT CHAINING RULE: You must form a continuous, single-path linear chain. "
            "If line_order is 2, this MUST exactly match the object_id (or target_id) of the MainActivity. "
            "If line_order is > 2, this MUST exactly match the target_id of the IMMEDIATELY PRECEDING SubActivity (line_order - 1). "
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
            "For example, if the chain is 'car' -> 'with' -> 'monthly_installment', this field is 'monthly_installment'."
        )
        # description=(
        #     "(Optional) The ID of secondary actor or another work object instance that is connected to the main object through the relation. "
        # )
        # description="The target of the continuation line."
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
    # work_object_instances: List[WorkObjectInstance] = Field(default_factory=list)
    activities: List[Activity] = Field(default_factory=list)


class DomainStory_Fewshot_CoT(BaseModel):
    reasoning: str = Field(
        description="Step-by-step logic explaining the mapping from the user's input."
    )
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
