import instructor, time, json
from icons_module.icon_semantic_search_2 import search_icons
from mapping_code.json_to_plantuml import create_plantuml_syntax

from model_init.openAI import openai_client
from prompt_strategy.extraction_rules import rules, SYSTEM_PROMPT
from text_to_json.schema_design import DomainStory
import litellm
from litellm import completion
import os
from dotenv import load_dotenv

from utils.api_request import api_response

load_dotenv()

client = instructor.from_openai(openai_client)


def pipeline(response_model, prompt, content):
    start_time = time.perf_counter()
    print(f"Started pipeline: {start_time}")

    model = 'gemini/gemini-2.5-flash'  # "gpt-4o-mini"   #"gpt-5.4"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    resp = api_response(model, messages, response_model)
    update_icons = search_icons(resp)

    # 3. Stop the timer
    end_time = time.perf_counter()
    # 4. Calculate and print the duration
    runtime_seconds = end_time - start_time
    print(f"Model response runtime: {runtime_seconds:.2f} seconds")
    # print(f'type update icons: {type(update_icons)}')
    # convert class object to json dict
    final_json_output = update_icons.model_dump(mode="json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json_output, f, ensure_ascii=False, indent=2)

    print(f"Saved to {output_path}")
    # print (f'type final json: {type(final_json_output)}')
    # plantuml_syntax = create_plantuml_syntax(final_json_output)
    # # # print(f'type: {type(plantuml_syntax)}')
    # print(f"plantuml_syntax \n: {plantuml_syntax}")
    # return plantuml_syntax


alphorn_1 = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn_text\alphorn-1-standardcase.txt"

alphorn_2 = r'C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn_text\alphorn-2-riskassessment.txt'


# ---------------
def load_content(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


content = load_content(alphorn_2)

if __name__ == "__main__":
    output_path = r"C:\code\NL_2_DST\alphorn-test-json\output_example_alphorn-2-gemini-flash2.5.json"
    story = pipeline(response_model=DomainStory, prompt=SYSTEM_PROMPT, content=content)
    # print("type: ", type(story))
