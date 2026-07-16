import os
import random
import sys
import time
from typing import Any

import litellm
from dotenv import load_dotenv

from text_to_json.schema_design import DomainTest

load_dotenv()

MAX_RETRIES = 5
BASE_RETRY_DELAY_SECONDS = 2.0
MAX_RETRY_DELAY_SECONDS = 30.0


def qwen_hosted_model(label: str, model: str) -> dict[str, str]:
    return {
        "label": label,
        "provider": "qwen-compatible",
        "model": model,
        "api_key_env": "DASHSCOPE_API_KEY",
        "custom_llm_provider": "openai",
        "api_base_env": "QWEN_API_BASE",
    }


def provider_model(
    label: str,
    provider: str,
    model: str,
    api_key_env: str,
    api_base_env: str | None = None,
) -> dict[str, str]:
    config = {
        "label": label,
        "provider": provider,
        "model": model,
        "api_key_env": api_key_env,
    }
    if api_base_env:
        config["api_base_env"] = api_base_env
    return config


MODELS_TO_TEST: list[dict[str, str]] = [
    qwen_hosted_model("Qwen3.7-Max", "qwen3.7-max"),
    qwen_hosted_model("GLM-5.2", "glm-5.2"),
    qwen_hosted_model("GLM-5.1", "glm-5.1"),
    qwen_hosted_model("Qwen3.7-Plus", "qwen3.7-plus"),
    qwen_hosted_model("Qwen3.6-Plus", "qwen3.6-plus"),
    qwen_hosted_model("DeepSeek v4 Pro", "deepseek-v4-pro"),
    qwen_hosted_model("DeepSeek v4 Flash", "deepseek-v4-flash"),
    qwen_hosted_model("Kimi K2.5", "kimi-k2.5"),
    provider_model("Claude Fable 5", "anthropic", "anthropic/claude-fable-5", "ANTHROPIC_API_KEY"),
    provider_model("Claude Opus 4.8", "anthropic", "anthropic/claude-opus-4.8", "ANTHROPIC_API_KEY"),
    provider_model("Claude Opus 4.7", "anthropic", "anthropic/claude-opus-4.7", "ANTHROPIC_API_KEY"),
    provider_model("Gemini 3.5 Flash", "gemini", "gemini/gemini-3.5-flash", "GEMINI_API_KEY"),
    provider_model("Gemini 3.1 Pro", "gemini", "gemini/gemini-3.1-pro-preview", "GEMINI_API_KEY"),
    provider_model("Gpt-5.6 Sol", "openai", "gpt-5.6-sol", "OPENAI_API_KEY"),
    provider_model("Gpt-5.6 Terra", "openai", "gpt-5.6-terra", "OPENAI_API_KEY"),
    provider_model("Gpt-5.5", "openai", "gpt-5.5", "OPENAI_API_KEY"),
    provider_model("Gpt-5.4", "openai", "gpt-5.4", "OPENAI_API_KEY"),
    provider_model("Kimi K2.6", "openrouter", "openrouter/moonshotai/kimi-k2.6", "OPENROUTER_API_KEY"),
    provider_model("Mistral Medium 3.5", "mistral", "mistral/mistral-medium-3.5", "MISTRAL_API_KEY"),
    provider_model("Grok 4.3", "xai", "xai/grok-4.3", "XAI_API_KEY"),
    provider_model("Grok 4.20", "xai", "xai/grok-4.20", "XAI_API_KEY"),
]

SYSTEM_PROMPT = """
You are an expert in Domain Storytelling, adhering to the methodology
introduced by Stefan Hofer and Henning Schwentner.
Your task is to analyze business process descriptions and extract the
core components of the domain story from user input.
You are adept at filtering out irrelevant noise, ensuring that
every extracted elements are strictly grounded in the
provided text. When a required schema is provided, you
accurately map these elements into that schema.
"""


def is_retryable_error(exc: Exception) -> bool:
    message = str(exc).lower()
    retryable_markers = (
        "high demand",
        "please try again later",
        "temporarily unavailable",
        "rate limit",
        "429",
        "503",
        "529",
        "timeout",
    )
    return any(marker in message for marker in retryable_markers)


def detect_missing_capability(exc: Exception) -> str:
    message = str(exc).lower()
    capability_markers = {
        "response_format / structured output": (
            "response_format",
            "structured output",
            "json schema",
            "response_format type is unavailable now",
        ),
        "streaming": (
            "stream is not supported",
            "streaming is not supported",
        ),
        "capacity / availability": (
            "serviceunavailableerror",
            "currently experiencing high demand",
            '"status": "unavailable"',
            "temporarily unavailable",
            "503",
        ),
        "authentication": (
            "invalid api key",
            "incorrect api key",
            "authenticationerror",
        ),
        "model access": (
            "model_not_found",
            "notfounderror",
            "not found",
        ),
        "credentials": (
            "missing ",
            "api_key client option must be set",
        ),
        "configuration": (
            "api base is not configured",
        ),
    }

    for capability, markers in capability_markers.items():
        if any(marker in message for marker in markers):
            return capability

    return "unknown"


def shorten(text: str, max_length: int = 100) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def get_api_base(model_config: dict[str, str]) -> str | None:
    api_base_env = model_config.get("api_base_env")
    if api_base_env:
        api_base = os.environ.get(api_base_env)
        if api_base:
            return api_base
    return model_config.get("api_base_default")


def build_messages() -> list[dict[str, str]]:
    sample_story = (
        "1. The customer submits an order.\n"
        "2. The system stores the order.\n"
        "3. The clerk checks the order."
    )
    prompt = (
        "Extract only the actors and work objects from the following story. "
        "Return valid JSON matching the provided schema.\n\n"
        f"{sample_story}"
    )
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]


def build_completion_kwargs(model_config: dict[str, str], api_key: str) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "model": model_config["model"],
        "api_key": api_key,
        "messages": build_messages(),
        "response_format": DomainTest,
        "max_tokens": 300
    }

    custom_llm_provider = model_config.get("custom_llm_provider")
    if custom_llm_provider:
        kwargs["custom_llm_provider"] = custom_llm_provider

    api_base = get_api_base(model_config)
    if api_base:
        kwargs["api_base"] = api_base

    return kwargs


def format_table(rows: list[dict[str, str]]) -> str:
    headers = [
        "Result",
        "Provider",
        "Model",
        "LiteLLM model",
        "API Base",
        "Missing capability",
        "Latency ms",
        "Details",
    ]
    table_rows = [headers] + [
        [
            row["result"],
            row["provider"],
            row["label"],
            row["model"],
            row["api_base"],
            row["missing_capability"],
            row["latency_ms"],
            row["details"],
        ]
        for row in rows
    ]
    widths = [max(len(str(item)) for item in column) for column in zip(*table_rows)]

    def format_row(values: list[str]) -> str:
        return " | ".join(value.ljust(width) for value, width in zip(values, widths))

    separator = "-+-".join("-" * width for width in widths)
    return "\n".join([
        format_row(headers),
        separator,
        *[format_row(row) for row in table_rows[1:]],
    ])


def check_model_capability(model_config: dict[str, str]) -> dict[str, str]:
    label = model_config["label"]
    model_name = model_config["model"]
    provider = model_config["provider"]
    api_key_env = model_config["api_key_env"]
    api_base = get_api_base(model_config)
    api_key = os.environ.get(api_key_env)
    api_base_env = model_config.get("api_base_env")

    if not api_key:
        return {
            "result": "✘",
            "provider": provider,
            "label": label,
            "model": model_name,
            "api_base": shorten(api_base or "-", 36),
            "missing_capability": "credentials",
            "latency_ms": "0",
            "details": f"Missing {api_key_env} in .env",
        }

    if api_base_env and not api_base:
        return {
            "result": "✘",
            "provider": provider,
            "label": label,
            "model": model_name,
            "api_base": "-",
            "missing_capability": "configuration",
            "latency_ms": "0",
            "details": f"Missing {api_base_env} in .env",
        }

    last_error: Exception | None = None
    for attempt in range(1, MAX_RETRIES + 1):
        start_time = time.time()
        try:
            litellm.completion(**build_completion_kwargs(model_config, api_key))
            latency_ms = int((time.time() - start_time) * 1000)
            return {
                "result": "✔",
                "provider": provider,
                "label": label,
                "model": model_name,
                "api_base": shorten(api_base or "-", 36),
                "missing_capability": "-",
                "latency_ms": str(latency_ms),
                "details": f"response_format works ({api_key_env})",
            }
        except Exception as exc:
            last_error = exc
            latency_ms = int((time.time() - start_time) * 1000)
            if attempt == MAX_RETRIES or not is_retryable_error(exc):
                return {
                    "result": "✘",
                    "provider": provider,
                    "label": label,
                    "model": model_name,
                    "api_base": shorten(api_base or "-", 36),
                    "missing_capability": detect_missing_capability(exc),
                    "latency_ms": str(latency_ms),
                    "details": shorten(str(exc)),
                }

            delay_seconds = min(BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)), MAX_RETRY_DELAY_SECONDS)
            delay_seconds += random.uniform(0, 0.5)
            print(
                f"Attempt {attempt} failed for {provider}/{model_name} with a transient error: {exc}. "
                f"Retrying in {delay_seconds:.1f}s...",
                file=sys.stderr,
            )
            time.sleep(delay_seconds)

    raise last_error if last_error is not None else RuntimeError("Unexpected capability check failure")


if __name__ == '__main__':
    rows = [check_model_capability(model_config) for model_config in MODELS_TO_TEST]
    print(format_table(rows))

