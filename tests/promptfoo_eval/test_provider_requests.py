import pytest
from unittest.mock import patch

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from text_to_json.schema_design import (
    DomainStory, Actor, ActorType, WorkObject, WorkObjectInstance, Icon,
    Activity, MainActivity,
)
from evaluations.promptfoo_eval.provider_requests import ApiCall

_MOD_PATH = "evaluations.promptfoo_eval.provider_requests"


def _make_domain_story():
    """Return a minimal but valid DomainStory fixture."""
    return DomainStory(
        title="Test Story",
        actors=[
            Actor(id="customer", name="Customer", type=ActorType.PERSON, note=None),
        ],
        work_objects=[
            WorkObject(
                id="contract",
                name="contract",
                description="legal agreement",
                instances=[WorkObjectInstance(instance_id="contract_1", note=None)],
                icon=None,
            ),
        ],
        activities=[
            Activity(
                step=1,
                text=None,
                main_activity=MainActivity(
                    subject_id="customer",
                    action="signs",
                    object_id="contract_1",
                    relation=None,
                    target_id=None,
                ),
                sub_activities=[],
            ),
        ],
    )


def _make_domain_story_with_icon():
    """Same story but with an icon populated (as search_icons would return)."""
    ds = _make_domain_story()
    ds.work_objects[0].icon = Icon(mdi_name="mdi-file-sign", svg=None)
    return ds


def _build_api_call(model="gpt-test", provider="openai"):
    """Build an ApiCall instance with minimal options/context."""
    prompt = ""
    options = {"config": {"model": model, "provider": provider}}
    context = {"vars": {"input": "The customer signs a contract."}}
    return ApiCall(prompt, options, context)


# Fixtures

@pytest.fixture
def api_call():
    return _build_api_call()


@pytest.fixture
def domain_story():
    return _make_domain_story()


@pytest.fixture
def domain_story_with_icon():
    return _make_domain_story_with_icon()


MOCK_TOKEN_USAGE = {"prompt": 100, "completion": 50, "total": 150}


# one_phase_call

class TestOnePhaseCall:

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_output_and_token_usage(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.return_value = {
            "output": domain_story,
            "token_usage": MOCK_TOKEN_USAGE,
        }
        mock_search_icons.return_value = domain_story_with_icon

        result = api_call.one_phase_call()

        assert "output" in result
        assert result["output"]["title"] == "Test Story"
        assert result["token_usage"] == MOCK_TOKEN_USAGE

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_api_response_called_with_schema(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.return_value = {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE}
        mock_search_icons.return_value = domain_story_with_icon

        api_call.one_phase_call()

        call_kwargs = mock_api_response.call_args
        assert call_kwargs.kwargs["schema"] is DomainStory

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_search_icons_called_with_domain_story(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.return_value = {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE}
        mock_search_icons.return_value = domain_story_with_icon

        api_call.one_phase_call()

        mock_search_icons.assert_called_once_with(domain_story)

    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_error_on_general_exception(self, mock_api_response, api_call):
        mock_api_response.side_effect = Exception("something broke")

        result = api_call.one_phase_call()

        assert "error" in result
        assert "Provider failed" in result["error"]

    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_error_on_503(self, mock_api_response, api_call):
        mock_api_response.side_effect = Exception("503 service down")

        result = api_call.one_phase_call()

        assert "error" in result
        assert "503" in result["error"]


# two_phase_zeroshot_call

class TestTwoPhaseZeroshotCall:

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_output_and_combined_token_usage(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        phase1_usage = {"prompt": 80, "completion": 40, "total": 120}
        phase2_usage = {"prompt": 200, "completion": 60, "total": 260}

        mock_api_response.side_effect = [
            {"output": "intermediate free-form text", "token_usage": phase1_usage},
            {"output": domain_story, "token_usage": phase2_usage},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        result = api_call.two_phase_zeroshot_call()

        assert result["output"]["title"] == "Test Story"
        assert result["token_usage"]["prompt"] == 280
        assert result["token_usage"]["completion"] == 100
        assert result["token_usage"]["total"] == 380

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_api_response_called_twice(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.side_effect = [
            {"output": "intermediate text", "token_usage": MOCK_TOKEN_USAGE},
            {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        api_call.two_phase_zeroshot_call()

        assert mock_api_response.call_count == 2

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_phase1_called_without_schema(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.side_effect = [
            {"output": "intermediate text", "token_usage": MOCK_TOKEN_USAGE},
            {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        api_call.two_phase_zeroshot_call()

        first_call_kwargs = mock_api_response.call_args_list[0]
        assert first_call_kwargs.kwargs["schema"] is None

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_phase2_called_with_schema(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.side_effect = [
            {"output": "intermediate text", "token_usage": MOCK_TOKEN_USAGE},
            {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        api_call.two_phase_zeroshot_call()

        second_call_kwargs = mock_api_response.call_args_list[1]
        assert second_call_kwargs.kwargs["schema"] is DomainStory

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_phase2_messages_contain_assistant_reply_and_prompt2(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        intermediate_text = "Actors: Customer. Work objects: contract."
        mock_api_response.side_effect = [
            {"output": intermediate_text, "token_usage": MOCK_TOKEN_USAGE},
            {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        api_call.two_phase_zeroshot_call()

        second_call_kwargs = mock_api_response.call_args_list[1]
        messages = second_call_kwargs.kwargs["messages"]

        # Should have: system, user (prompt1), assistant (phase1 result), user (prompt2)
        assert len(messages) == 4
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"
        assert messages[2]["content"] == intermediate_text
        assert messages[3]["role"] == "user"

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_token_usage_fallback_when_phase1_is_none(
        self, mock_api_response, mock_search_icons, api_call, domain_story, domain_story_with_icon
    ):
        mock_api_response.side_effect = [
            {"output": "text", "token_usage": None},
            {"output": domain_story, "token_usage": MOCK_TOKEN_USAGE},
        ]
        mock_search_icons.return_value = domain_story_with_icon

        result = api_call.two_phase_zeroshot_call()

        assert result["token_usage"] == MOCK_TOKEN_USAGE

    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_error_on_general_exception(self, mock_api_response, api_call):
        mock_api_response.side_effect = Exception("connection lost")

        result = api_call.two_phase_zeroshot_call()

        assert "error" in result
        assert "Provider failed" in result["error"]

    @patch(f"{_MOD_PATH}.search_icons")
    @patch(f"{_MOD_PATH}.api_response")
    def test_returns_error_when_phase2_fails(
        self, mock_api_response, mock_search_icons, api_call
    ):
        mock_api_response.side_effect = [
            {"output": "intermediate text", "token_usage": MOCK_TOKEN_USAGE},
            Exception("phase 2 broke"),
        ]

        result = api_call.two_phase_zeroshot_call()

        assert "error" in result
        assert "Provider failed" in result["error"]

