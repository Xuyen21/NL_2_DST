import json
from litellm import completion
from typing import Optional, Type, TypeVar
from pydantic import BaseModel

from text_to_json.schema_design import DomainStory

T = TypeVar("T", bound=BaseModel)


def api_response(model_name: str, messages: list[object], schema: Type[T] = None):
    kwargs = {
        "model": model_name,
        "messages": messages,
        # "temperature": 0,
        # "seed": 42,
        # "timeout": 60
    }

    if schema is not None:
        kwargs["response_format"] = schema

    resp = completion(**kwargs)
    output = resp.choices[0].message.content
    str_2_obj = DomainStory.model_validate_json(output)

    usage = None
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt": resp.usage.prompt_tokens,
            "completion": resp.usage.completion_tokens,
            "total": resp.usage.total_tokens,
        }

    return {
        "output": str_2_obj,
        "token_usage": usage,
    }

# def api_response(model_name: str, messages: list[object], schema: Type[T] = None):
#     kwargs = {
#         "model": model_name,
#         "messages": messages,
#         "temperature": 0
#     }
#
#     if schema is not None:
#         kwargs["response_format"] = schema
#
#     resp = completion(**kwargs)
#     output = resp.choices[0].message.content
#     str_2_obj = DomainStory.model_validate_json(output)
#     print("type",type(str_2_obj))
#
#     return str_2_obj
