from types import SimpleNamespace
from unittest.mock import patch
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from utils.api_request import (
    DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE,
    api_response,
)


class _DummyResponse:
    def __init__(self, content: str = "ok"):
        self.choices = [SimpleNamespace(message=SimpleNamespace(content=content))]
        self.usage = SimpleNamespace(prompt_tokens=1, completion_tokens=2, total_tokens=3)


def _messages() -> list[dict[str, str]]:
    return [
        {"role": "system", "content": "Base system prompt."},
        {"role": "user", "content": "Hello"},
    ]


@patch("utils.api_request.completion")
def test_gpt_based_models_add_sampling_guidance_and_skip_temperature(mock_completion):
    mock_completion.return_value = _DummyResponse()

    api_response(
        model_name="gpt-5.5",
        messages=_messages(),
        custom_llm_provider="openai",
    )

    kwargs = mock_completion.call_args.kwargs
    assert "temperature" not in kwargs
    assert kwargs["messages"][0]["role"] == "system"
    assert DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE in kwargs["messages"][0]["content"]


@patch("utils.api_request.completion")
def test_gemini_3_models_add_sampling_guidance_and_skip_temperature(mock_completion):
    mock_completion.return_value = _DummyResponse()

    api_response(
        model_name="gemini/gemini-3.1-pro-preview",
        messages=_messages(),
        custom_llm_provider="gemini",
    )

    kwargs = mock_completion.call_args.kwargs
    assert "temperature" not in kwargs
    assert DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE in kwargs["messages"][0]["content"]


@patch("utils.api_request.completion")
def test_models_with_temperature_support_keep_temperature_without_extra_guidance(mock_completion):
    mock_completion.return_value = _DummyResponse()

    original_messages = _messages()
    api_response(
        model_name="deepseek-v4-pro",
        messages=original_messages,
        custom_llm_provider="openai",
    )

    kwargs = mock_completion.call_args.kwargs
    assert kwargs["temperature"] == 0
    assert kwargs["messages"] == original_messages
    assert DETERMINISTIC_SYSTEM_SAMPLING_GUIDANCE not in kwargs["messages"][0]["content"]

