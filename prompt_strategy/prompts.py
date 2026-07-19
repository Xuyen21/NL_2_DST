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
Read the domain story below and extract all actors, work objects, and activities.

Count each work object by how many separate sentences mention it — no more, no less.
A work object is always a noun (e.g., 'contract', 'car'), never a verb or preposition.
Do not invent elements. Do not merge different work objects that share a word.

Domain Story:
{user_story}
"""

PROMPT_2 = """
Using the previous response, map the extracted elements into the exact provided DomainStory schema.

Important:
- Create exactly as many work object instances as identified in the previous response. Do not add or remove any.
- The action field must contain only the verb (and its preposition), never the work object noun.
- subject_id in each activity must be an actor ID, not a work object ID.
- Each step number must be unique.
- Set note to null unless the original text explicitly contains a note, parenthetical remark, or multi-word temporal/conditional clause.

Let's think step by step.
"""

# PROMPT_1 = """
# Read the domain story below and extract the important information in a concise form.
# Focus on:
#
# - the actors
# - the work objects and how many times each work object appears
# - the main activities and relations between them
#
#
# Count only mentions that are explicitly present in the text. Do not hallucinate, infer, or invent extra occurrences.
# Preserve the original meaning and keep the output grounded in the text.
# Let's think step by step.
#
# Domain Story:
# {user_story}
# """
