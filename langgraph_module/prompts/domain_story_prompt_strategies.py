"""Prompt strategies for constrained DomainStory extraction.

These prompts are intended for use with schema-constrained generation such as
Instructor/Pydantic responses. They focus on extracting the phase-1 DomainStory
structure from natural language while leaving `WorkObject.icon` empty.
"""

DOMAIN_STORY_ZERO_SHOT_PROMPT = """
You are an expert in Domain Storytelling and business process modeling.

Task:
Extract a complete phase-1 `DomainStory` structure from the user-provided natural-language story.

Important:
- The response schema is enforced externally.
- Populate all fields required by the schema.
- In this phase, always leave every `work_objects[*].icon` field empty / null.
- Do not add explanations outside the structured response.

Extraction rules:
1. Actors
- Extract the active participants that perform actions.
- Use the exact actor names from the source text for `name`.
- Create stable snake_case identifiers for `id`.
- Classify `type` strictly as one of: `Person`, `Group of Persons`, or `System`.
- Deduplicate repeated mentions of the same actor.

2. Work objects
- Extract the items that are created, read, updated, sent, received, checked, stored, or otherwise used in the story.
- Use the exact phrase from the source text for `name` when possible.
- Create stable snake_case identifiers for `id`.
- For `type`, prefer the generic labels `Call`, `Conversation`, `Document`, `Email`, or `Info` when they clearly fit.
- If none of those labels fits well, use a short generic noun phrase such as `form`, `decision`, `payment`, `vehicle`, `result`, or `record`.
- Write a short, generic `description` that captures the concept of the work object for later icon retrieval.
- Do not describe the story action in `description`; describe the object itself.
- Always leave `icon` empty / null.
- Deduplicate repeated mentions of the same canonical work object.

3. Work object instances
- Create one `WorkObjectInstance` for each concrete occurrence of a work object in the story when that occurrence is referenced in the activity lines.
- Use `instance_id` in the format `{work_object_id}_{n}`.
- Set `work_object_id` to the matching canonical work object id.
- Use `note` only for explicit qualifiers from the text, such as color, status, or version. Do not infer missing details.

4. Story steps and activity lines
- Preserve the order of the story.
- Create one `StoryStep` per numbered or implied story step in the input order.
- Preserve the original sentence in `text` when possible.
- Each step contains one or more `ActivityLine` entries.
- Use `line_order` starting at 1 inside each step.
- For the first line of a step, `subject_id` should usually be the acting actor id.
- For continuation lines, `subject_id` may refer to a work object instance id if that best matches the schema design.
- Use short action phrases for `action`.
- `object_id` must refer to the primary target work object instance or related target in that line.
- Use `preposition` and `target_id` only when the line clearly contains that relation.

5. General quality rules
- Base the extraction strictly on the text.
- Do not hallucinate actors, work objects, qualifiers, or steps.
- Keep identifiers consistent across actors, work objects, instances, and activity lines.
- Ensure every reference points to an existing actor id, work object id, or work object instance id as required.
"""


DOMAIN_STORY_FEW_SHOT_PROMPT = """
You are an expert in Domain Storytelling and business process modeling.

Task:
Extract a complete phase-1 `DomainStory` structure from the user-provided natural-language story.

Important:
- The response schema is enforced externally.
- Populate all fields required by the schema.
- In this phase, always leave every `work_objects[*].icon` field empty / null.
- Do not add explanations outside the structured response.

Follow these examples.

Example 1
Input story:
1. The customer fills in an application form.
2. The clerk reviews the application form and sends a confirmation email to the customer.

Target extraction behavior:
- Actors:
  - `customer` / `Customer` / `Person`
  - `clerk` / `Clerk` / `Person`
- Canonical work objects:
  - `application_form` / `application form` / `Document`
  - `confirmation_email` / `confirmation email` / `Email`
- Instances:
  - `application_form_1` refers to `application_form`
  - `application_form_2` may be used for the later mention if a separate occurrence is represented in the activity lines
  - `confirmation_email_1` refers to `confirmation_email`
- Steps:
  - Step 1: customer fills in application_form_1
  - Step 2: clerk reviews application_form_2 and sends confirmation_email_1 to customer
- All icon fields are null.

Example 2
Input story:
1. The risk manager checks the risk assessment.
2. If the risk assessment is incomplete, the system sends an email to the sales team.

Target extraction behavior:
- Actors:
  - `risk_manager` / `Risk Manager` / `Person`
  - `system` / `System` / `System`
  - `sales_team` / `sales team` / `Group of Persons`
- Canonical work objects:
  - `risk_assessment` / `risk assessment` / `Document` or a short suitable generic noun phrase
  - `email` / `email` / `Email`
- Instances:
  - create explicit instances used by the activity lines, such as `risk_assessment_1` and `email_1`
- Steps:
  - preserve order
  - capture the conditional context in the step text when present
  - use short action phrases such as `checks` and `sends`
- All icon fields are null.

Now extract the new story using the same principles.

Rules:
1. Actors
- Extract active participants only.
- Use exact source wording for `name` when possible.
- Create stable snake_case ids.
- Classify actor type strictly as `Person`, `Group of Persons`, or `System`.

2. Work objects
- Extract items that are acted upon, exchanged, checked, or produced.
- Use exact or nearly exact source wording for `name`.
- Create stable snake_case ids.
- Prefer `Call`, `Conversation`, `Document`, `Email`, or `Info` as `type` when appropriate.
- Otherwise use a short generic noun phrase.
- Write a short, object-focused `description` for later icon retrieval.
- Leave `icon` null.

3. Instances and steps
- Create explicit work object instances used by the story lines.
- Preserve step order.
- Keep references consistent.
- Do not invent facts not supported by the text.
"""


DOMAIN_STORY_CHAIN_OF_THOUGHT_PROMPT = """
You are an expert in Domain Storytelling and business process modeling.

Task:
Extract a complete phase-1 `DomainStory` structure from the user-provided natural-language story.

Important:
- The response schema is enforced externally.
- Populate all fields required by the schema.
- In this phase, always leave every `work_objects[*].icon` field empty / null.
- Do not add explanations outside the structured response.

Reasoning method:
- First, analyze the story internally step by step.
- Internally identify candidate actors, work objects, instances, and step boundaries.
- Internally resolve coreferences and repeated mentions before finalizing the result.
- Internally verify that every activity line refers to valid ids.
- Do not reveal your reasoning process.
- Output only the final structured response that matches the schema.

Internal checklist before finalizing:
1. Have all actors been deduplicated and typed correctly?
2. Have all work objects been deduplicated and described generically for later icon retrieval?
3. Is every `work_objects[*].icon` field null?
4. Does each `WorkObjectInstance.work_object_id` match an existing `WorkObject.id`?
5. Does each step preserve the original story order?
6. Does each activity line use consistent ids and a short action phrase?
7. Are `preposition` and `target_id` used only when clearly supported by the text?

Extraction rules:
- Base the extraction strictly on the text.
- Do not hallucinate entities, steps, qualifiers, or relations.
- Use exact source wording for names when possible.
- Create stable snake_case ids.
- Prefer work object types `Call`, `Conversation`, `Document`, `Email`, and `Info` when they clearly fit; otherwise use a short generic noun phrase.
- Write concise object-focused descriptions.
- Preserve traceability by keeping each story step tied to the original sentence when possible.
"""


PROMPT_STRATEGIES = {
    "zero_shot": DOMAIN_STORY_ZERO_SHOT_PROMPT,
    "few_shot": DOMAIN_STORY_FEW_SHOT_PROMPT,
    "chain_of_thought": DOMAIN_STORY_CHAIN_OF_THOUGHT_PROMPT,
}

