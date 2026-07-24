import logging
from typing import Any

from dotenv import load_dotenv

from icons_module.icon_semantic_search_2 import search_icons
from mapping_code.json_to_plantuml import create_plantuml_syntax
from prompt_strategy.prompts import SYSTEM_PROMPT, ONE_PHASE_PROMPT
from text_to_json.schema_design import DomainStory
from utils.api_request import api_response

load_dotenv()
logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-5.5"  # 'gemini/gemini-2.5-flash'


def pipeline(content: str, model: str = DEFAULT_MODEL) -> str:
    """End-to-end: plain text → PlantUML syntax."""
    final_json_output = get_json_response(content, model=model)
    plantuml_syntax = create_plantuml_syntax(final_json_output)
    return plantuml_syntax


def get_json_response(content: str, model: str = DEFAULT_MODEL) -> dict[str, Any]:
    user_prompt = ONE_PHASE_PROMPT.format(user_story=content)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    try:
        resp = api_response(model_name=model, messages=messages, schema=DomainStory)
    except Exception as e:
        logger.error("LLM call failed: %s", e)
        raise RuntimeError(f"LLM extraction failed: {e}") from e

    update_icons = search_icons(resp["output"])
    return update_icons.model_dump(mode="json")
