from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from icons_module.icon_semantic_search_2 import search_icons
from prompt_strategy.prompts import SYSTEM_PROMPT
from text_to_json.schema_design import DomainStory
from utils.api_request import api_response

from typing import Any
from dotenv import load_dotenv

load_dotenv()


# gpt-5.4 one-phase
def one_phase_zeroshot(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    config = options.get("config", {})
    model_name = config.get("model")
    if not model_name:
        raise ValueError("options.config.model is required")

    user_story = context["vars"]["input"]

    messages_1 = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_story},
    ]

    resp = api_response(model_name=model_name, messages=messages_1, schema=DomainStory)
    print("type of resp: ", type(resp))
    update_icons = search_icons(resp)

    final_json_output = update_icons.model_dump(mode="json")

    return {"output": final_json_output,
            # "tokenUsage": {"total": resp.usage.total_tokens, "prompt": resp.usage.prompt_tokens,
            #                "completion": resp.usage.completion_tokens},
            }


# gpt-5.4 two-phase


# gemini one-phase


# gemini two-phase

one_phase_zeroshot_gpt = one_phase_zeroshot
one_phase_zeroshot_gpt_mini = one_phase_zeroshot_gpt
one_phase_zeroshot_gemini = one_phase_zeroshot
