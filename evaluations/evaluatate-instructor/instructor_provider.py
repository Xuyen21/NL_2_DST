from __future__ import annotations

from litellm import completion
from dotenv import load_dotenv
load_dotenv()

import json
import sys
from pathlib import Path
from typing import Any, cast

import instructor
from openai.types.chat import ChatCompletionMessageParam

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from model_init.openAI import openai_client  # noqa: E402
from text_to_json.schema_design import DomainTest  # noqa: E402



SCHEMA_SYSTEM_PROMPT = """
You extract Domain Story elements from business-process text.
Return data that matches the DomainTest schema exactly.
Only return canonical actors and canonical work_objects.
Do not include title, work_object_instances, steps, or any extra top-level keys.
""".strip()


def extract_json(model: str, response_model: type[DomainTest], prompt: str, content: str) -> dict[str, Any]:
    client = instructor.from_openai(openai_client)
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content},
    ]

    extracted_json, raw_response = client.chat.completions.create_with_completion(
        model=model,
        response_model=response_model,
        temperature=0,
        messages=messages,
    )

    usage = getattr(raw_response, "usage", None)

    return {
        "result": extracted_json,
        "tokenUsage": {
            "prompt": getattr(usage, "prompt_tokens", 0) if usage else 0,
            "completion": getattr(usage, "completion_tokens", 0) if usage else 0,
            "total": getattr(usage, "total_tokens", 0) if usage else 0,
        },
    }


def call_api(prompt: str, options: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
    config = options.get("config", {})
    model = config.get("model")
    if not model:
        raise ValueError("options.config.model is required")

    result = extract_json(model, DomainTest, prompt, context["vars"]["input"])

    return {
        "output": json.dumps({
            "model": model,
            "result": result["result"].model_dump(mode="json"),
        }, ensure_ascii=False, indent=2),
        "tokenUsage": result["tokenUsage"],
        "metadata": {
            "model": model,
            "schema": "DomainTest",
        },
    }
    result = extract_json(model, DomainTest, prompt, context['vars']['input'])

    return {
        "output": json.dumps({
            "model": model,
            "result": result.model_dump(mode="json")
        }, ensure_ascii=False, indent=2),
        "metadata": {
            "model": model,
            "schema": "DomainTest",
        },
    }


call_api_gpt= call_api
call_api_gemmini = call_api
