import os
from typing import Optional, Type, TypeVar

from litellm import completion
from pydantic import BaseModel

from text_to_json.schema_design import DomainStory

T = TypeVar("T", bound=BaseModel)

DEFAULT_TIMEOUT_SECONDS = float(os.getenv("LLM_TIMEOUT_SECONDS", "600"))
DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE = (
    "Be deterministic and consistent. Prefer the most literal, text-grounded "
    "interpretation. Avoid creative variation, randomness, and alternative phrasings "
    "unless the input explicitly requires them."
)


def _normalize_model_name(model_name: str) -> str:
    return model_name.strip().lower()


def _supports_temperature(model_name: str, custom_llm_provider: str | None) -> bool:
    normalized_model = _normalize_model_name(model_name)

    unsupported_temperature_prefixes = (
        "gemini-3",
        "gemini/gemini-3",
        "gpt-",
        "openai/gpt-",
    )
    return not normalized_model.startswith(unsupported_temperature_prefixes)


def _should_add_system_sampling_guidance(model_name: str, custom_llm_provider: str | None) -> bool:
    return not _supports_temperature(model_name, custom_llm_provider)


def _with_system_sampling_guidance(messages: list[object]) -> list[object]:
    updated_messages: list[object] = []
    appended_guidance = False

    for message in messages:
        if (
            not appended_guidance
            and isinstance(message, dict)
            and message.get("role") == "system"
            and isinstance(message.get("content"), str)
        ):
            updated_message = dict(message)
            content = updated_message["content"].rstrip()
            updated_message["content"] = f"{content}\n\n{DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE}"
            updated_messages.append(updated_message)
            appended_guidance = True
            continue

        updated_messages.append(message)

    if not appended_guidance:
        return [
            {"role": "system", "content": DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE},
            *updated_messages,
        ]

    return updated_messages


def _format_exception_details(exc: Exception) -> str:
    detail_parts = [f"{exc.__class__.__name__}: {exc}"]

    status_code = getattr(exc, "status_code", None)
    if status_code is not None:
        detail_parts.append(f"status_code={status_code}")

    code = getattr(exc, "code", None)
    if code is not None:
        detail_parts.append(f"code={code}")

    response = getattr(exc, "response", None)
    response_text = getattr(response, "text", None)
    if response_text:
        detail_parts.append(f"response={response_text}")

    exc_repr = repr(exc)
    if exc_repr and exc_repr != str(exc):
        detail_parts.append(f"repr={exc_repr}")

    return " | ".join(detail_parts)


def _mark_exception(exc: Exception, attempts: int) -> None:
    setattr(exc, "_api_request_attempts", attempts)
    setattr(exc, "_api_request_details", _format_exception_details(exc))


def api_response(
    model_name: str,
    messages: list[object],
    schema: Type[T] = None,
    api_key: Optional[str] = None,
    api_base: Optional[str] = None,
    custom_llm_provider: Optional[str] = None,
    timeout_seconds: Optional[float] = None,
):
    resolved_timeout_seconds = timeout_seconds or DEFAULT_TIMEOUT_SECONDS
    should_add_system_sampling_guidance = _should_add_system_sampling_guidance(
        model_name, custom_llm_provider
    )
    temperature_supported = _supports_temperature(model_name, custom_llm_provider)
    resolved_messages = (
        _with_system_sampling_guidance(messages)
        if should_add_system_sampling_guidance
        else messages
    )

    kwargs = {
        "model": model_name,
        "messages": resolved_messages,
        "timeout": resolved_timeout_seconds,
        "num_retries": 0,
        "seed": 42,
    }

    if temperature_supported:
        kwargs["temperature"] = 0

    if schema is not None:
        kwargs["response_format"] = schema

    if api_key:
        kwargs["api_key"] = api_key

    if api_base:
        kwargs["api_base"] = api_base

    if custom_llm_provider:
        kwargs["custom_llm_provider"] = custom_llm_provider

    try:
        resp = completion(**kwargs)
    except Exception as exc:
        _mark_exception(exc, attempts=1)
        raise


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
