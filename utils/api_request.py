from litellm import completion
from typing import Type, TypeVar, Optional
from pydantic import BaseModel

from text_to_json.schema_design import DomainStory

T = TypeVar("T", bound=BaseModel)


def api_response(
    model_name: str,
    messages: list[object],
    schema: Type[T] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    custom_llm_provider: Optional[str] = None,
):
    kwargs = {
        "model": model_name,
        "messages": messages,
        # "temperature": 0,
        # "seed": 42,
        # "timeout": 60
    }

    if schema is not None:
        kwargs["response_format"] = schema

    if api_key:
        kwargs["api_key"] = api_key

    if api_base:
        kwargs["api_base"] = api_base

    if custom_llm_provider:
        kwargs["custom_llm_provider"] = custom_llm_provider

    resp = completion(**kwargs)
    output = resp.choices[0].message.content
    if output is None:
        raise ValueError(f"Model '{model_name}' returned no message content")
    output_text: str = output

    if schema is not None:
        validated_output = DomainStory.model_validate_json(output_text)
    else:
        validated_output = output_text

    usage = None
    if getattr(resp, "usage", None) is not None:
        usage = {
            "prompt": resp.usage.prompt_tokens,
            "completion": resp.usage.completion_tokens,
            "total": resp.usage.total_tokens,
        }

    return {
        "output": validated_output,
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
