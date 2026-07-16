import json
import time
from pathlib import Path

from dotenv import load_dotenv

from icons_module.icon_semantic_search_2 import search_icons
from mapping_code.json_to_plantuml import create_plantuml_syntax
from prompt_strategy.extraction_rules import SYSTEM_PROMPT
from text_to_json.schema_design import DomainStory
from utils.api_request import api_response

load_dotenv()

# client = instructor.from_openai(openai_client)


def pipeline(response_model, prompt, content):
    start_time = time.perf_counter()
    print(f"Started pipeline: {start_time}")

    model = "gpt-5.4"  # 'gemini/gemini-2.5-flash'  # "gpt-4o-mini"   #
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content}
    ]
    resp = api_response(model, messages, response_model)
    update_icons = search_icons(resp['output'])

    end_time = time.perf_counter()
    runtime_seconds = end_time - start_time
    print(f"Model response runtime: {runtime_seconds:.2f} seconds")

    final_json_output = update_icons.model_dump(mode="json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(final_json_output, f, ensure_ascii=False, indent=2)

    plantuml_syntax = create_plantuml_syntax(final_json_output)
    puml_path = Path(output_path).with_suffix(".puml")
    puml_path.write_text(plantuml_syntax, encoding="utf-8")
    print(f"PlantUML written to: {puml_path}")
    # print(f"plantuml_syntax \n: {plantuml_syntax}")
    return plantuml_syntax


alphorn_5 = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn_text\alphorn-5.txt"

# alphorn_2 = r'C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn_text\alphorn-2.txt'
# ---------------
def load_content(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


content = load_content(alphorn_5)

if __name__ == "__main__":
    output_path = r"C:\code\NL_2_DST\evaluations\promptfoo-eval\alphorn-gold-standard\gold-alphorn-5-new.json"
    story = pipeline(response_model=DomainStory, prompt=SYSTEM_PROMPT, content=content)

