SYSTEM_PROMPT = """
You are an expert in Domain Storytelling, adhering to the methodology
introduced by Stefan Hofer and Henning Schwentner.

Your task is to analyze business process descriptions and extract the
core components of the domain story from user input.

You are adept at filtering out irrelevant noise, ensuring that
every extracted element is strictly grounded in the provided text.
"""

ONE_PHASE_PROMPT = """
Read the provided domain story and extract all relevant elements into the provided DomainStory schema.

Rules:
1. Extract elements exactly as explicitly stated in the text. Do not invent or assume elements.
2. Each work object is a noun (the 'what'), not a verb or preposition. Do not merge different work objects.
3. The action field contains only the verb (and its preposition if needed), never the work object noun.
4. subject_id in an activity must always be an actor ID, not a work object ID.
5. Each step number must be unique — do not repeat the same step.
6. Count work object instances by how many separate sentences mention that object. Do not over-count.
7. Set note to null unless the original text contains an explicit note, parenthetical remark, or multi-word temporal/conditional clause.

Text:
{user_story}

Let's think step by step.
"""

PROMPT_1 = """
Read the domain story below and extract the important information in a concise form.
Focus on:

- the actors
- the work objects and count how many times each work object mentioned in the story
- the main activities and relations between them


Count only mentions that are explicitly present in the text. Do not hallucinate, infer, or invent extra occurrences.
Preserve the original meaning and keep the output grounded in the text.


Domain Story:
{user_story}

Let's think step by step.
"""

PROMPT_2 = """
Using both the original domain story below and the previous assistant response and extract all relevant elements into the provided DomainStory schema.

Important grounding rule:
- The original domain story is the source of truth.
- The previous assistant response help provides analyses elements of the stories


Rules:
1. Extract elements exactly as explicitly stated in the text. Do not invent or assume elements.
2. Each work object is a noun (the 'what'), not a verb or preposition. Do not merge different work objects.
3. The action field contains only the verb (and its preposition if needed), never the work object noun.
4. subject_id in an activity must always be an actor ID, not a work object ID.
5. Each step number must be unique — do not repeat the same step.
6. Count work object instances by how many separate sentences mention that object. Do not over-count.
7. Set note to null unless the original text contains an explicit note, parenthetical remark, or multi-word temporal/conditional clause.

"""


