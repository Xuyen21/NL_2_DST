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

Rules for Extraction:
1. Extract elements exactly as explicitly mentioned in the text.
2. Do not invent, hallucinate, or assume elements that are not present.
3. Do not merge different work objects just because they share words.
4. Strictly follow the constraints and definitions provided in the schema field descriptions.

Text:
{user_story}

Let's think step by step.
"""

# PROMPT_1 = """
# Identify the Actors, Activities, Work Objects.
# Then you count how many times the same work object is mentioned throughout the entire story
# in the following text:
# Text: {user_story}
# Let’s think step by step.
# """
# PROMPT_1 = """
# Read the domain story below and extract all relevant domain story elements in a complete intermediate representation.
# Include all actors mentioned in the text, including persons, groups, and systems.
# Include all work objects, exactly how many times each work object is explicitly mentioned, and all activities and relations in their original order.
#
# Count work object mentions strictly by the exact object referred to in the text.
# Do not merge distinct work objects just because they share a head noun or overlapping words.
#
# Do not summarize away details. Do not hallucinate or invent missing elements.
# Do not use JSON or strict schema formatting.
#
# Let's think step by step.
#
# Domain Story:
# {user_story}
# """
PROMPT_1 = """
Read the domain story below and extract all actors, work objects, and activities.

Count each work object exactly as explicitly mentioned in the text.
Do not invent elements.
Do not merge different work objects just because they share words.

Do not use JSON or strict schema formatting.


Domain Story:
{user_story}
"""
# two-phase
#this will output json like schema
# PROMPT_1 = """
# Extract the domain story from the text below as a concise intermediate representation.
# Identify the title, actors, work objects, the number of times a same work object is actually mentioned throughout the story, and the activities/relations between them.
#
# Count only mentions that are explicitly present in the text. Do not hallucinate, infer, or invent extra occurrences.
#
# Preserve the order of mentions and keep the output grounded in the text.
# Let's think step by step.
#
# Domain Story:
# {user_story}
# """

# PROMPT_1 = """
# Read the domain story below and extract the important information in a concise, human-readable form.
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

PROMPT_2 = """
Using the previous response, map the extracted elements into the exact provided DomainStory schema.
For each work object, create exactly as many instances as were identified in the previous response.
Preserve the mention counts from the previous response and do not add or remove instances.
"""
