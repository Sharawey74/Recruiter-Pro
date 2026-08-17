"""
The failure branches of the model-backed providers.

Every provider spends most of its code on what happens when the call does not
work: a server that is down, a model that is not pulled, a timeout, a 500, JSON
that will not parse, a response that is technically valid and useless. Those
branches decide whether a bad afternoon at the provider becomes a bad
afternoon for the user, and none of them run in a normal test.

They are exercised here with fakes rather than a live server, so the whole file
runs offline in CI. The contract each one checks is the same: a provider that
cannot answer returns None for that item and lets ExplainerAgent fall back --
it never raises, and it never returns a half-formed explanation.
"""

import json

import pytest

from src.agents.explaining import (
    ExplanationContext,
    LangChainProvider,
    OllamaProvider,
    OpenRouterProvider,
    prompt,
)
from src.core.config import get_config

CONTEXT = ExplanationContext(
    candidate_name="Jane Doe",
    job_title="Backend Engineer",
    final_score=0.82,
    decision="shortlist",
    confidence=0.9,
    skill_score=0.8,
    experience_score=0.9,
    education_score=1.0,
    keyword_score=0.6,
    matched_skills=["Python", "Docker"],
    missing_skills=["Kafka"],
    overqualified=True,
    underqualified=False,
)

GOOD_TEXT = "This candidate is a strong match. " * 5


@pytest.fixture
def llm_config():
    return get_config().llm


class FakeResponse:
    def __init__(self, status_code=200, payload=None, raise_on_json=False):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self._raise = raise_on_json

    def json(self):
        if self._raise:
            raise ValueError("Expecting value: line 1 column 1 (char 0)")
        return self._payload


class TestPromptBuilding:
    """Both network providers send this. A crash here breaks every provider."""

    @pytest.mark.unit
    def test_includes_the_facts_the_model_needs(self):
        text = prompt.build(CONTEXT)
        assert "Jane Doe" in text
        assert "Backend Engineer" in text
        assert "Python" in text
        assert "Kafka" in text

    @pytest.mark.unit
    def test_reports_the_qualification_flags(self):
        assert "Overqualified" in prompt.build(CONTEXT)

    @pytest.mark.unit
    def test_handles_a_context_with_no_skills_either_way(self):
        import dataclasses

        empty = dataclasses.replace(
            CONTEXT, matched_skills=[], missing_skills=[], overqualified=False, underqualified=False
        )
        text = prompt.build(empty)
        assert "None" in text  # rather than an empty list or a crash


class TestOllamaAvailability:
    @pytest.mark.unit
    def test_unavailable_when_the_server_is_down(self, llm_config, monkeypatch):
        def boom(*a, **k):
            raise ConnectionError("connection refused")

        monkeypatch.setattr("src.agents.explaining.ollama.requests.get", boom)
        assert OllamaProvider(llm_config).is_available() is False

    @pytest.mark.unit
    def test_unavailable_on_a_non_200(self, llm_config, monkeypatch):
        monkeypatch.setattr(
            "src.agents.explaining.ollama.requests.get", lambda *a, **k: FakeResponse(503)
        )
        assert OllamaProvider(llm_config).is_available() is False

    @pytest.mark.unit
    def test_unavailable_when_the_model_is_not_pulled(self, llm_config, monkeypatch):
        """
        A running Ollama with the wrong models is the common case, and it is
        the one worth distinguishing: the server answers, so a naive ping
        reports healthy while every generation fails.
        """
        monkeypatch.setattr(
            "src.agents.explaining.ollama.requests.get",
            lambda *a, **k: FakeResponse(200, {"models": [{"name": "something-else"}]}),
        )
        assert OllamaProvider(llm_config).is_available() is False

    @pytest.mark.unit
    def test_available_when_the_model_is_present(self, llm_config, monkeypatch):
        monkeypatch.setattr(
            "src.agents.explaining.ollama.requests.get",
            lambda *a, **k: FakeResponse(200, {"models": [{"name": llm_config.model}]}),
        )
        assert OllamaProvider(llm_config).is_available() is True

    @pytest.mark.unit
    def test_unavailable_when_the_llm_is_disabled_by_config(self, llm_config, monkeypatch):
        import dataclasses

        disabled = dataclasses.replace(llm_config, enabled=False)
        # No request should even be attempted.
        monkeypatch.setattr(
            "src.agents.explaining.ollama.requests.get",
            lambda *a, **k: pytest.fail("pinged a disabled provider"),
        )
        assert OllamaProvider(disabled).is_available() is False


class TestOllamaGeneration:
    @staticmethod
    def _with_post(monkeypatch, response):
        def post(*a, **k):
            if isinstance(response, Exception):
                raise response
            return response

        monkeypatch.setattr("src.agents.explaining.ollama.requests.post", post)

    @pytest.mark.unit
    def test_returns_the_generated_text(self, llm_config, monkeypatch):
        self._with_post(monkeypatch, FakeResponse(200, {"response": GOOD_TEXT}))
        out = OllamaProvider(llm_config).explain([CONTEXT])
        assert out[0].source == "ollama"
        assert out[0].text.startswith("This candidate")

    @pytest.mark.unit
    def test_a_timeout_yields_none_not_an_exception(self, llm_config, monkeypatch):
        self._with_post(monkeypatch, TimeoutError("read timed out"))
        assert OllamaProvider(llm_config).explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_a_500_yields_none(self, llm_config, monkeypatch):
        self._with_post(monkeypatch, FakeResponse(500))
        assert OllamaProvider(llm_config).explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_malformed_json_yields_none(self, llm_config, monkeypatch):
        self._with_post(monkeypatch, FakeResponse(200, raise_on_json=True))
        assert OllamaProvider(llm_config).explain([CONTEXT]) == [None]

    @pytest.mark.unit
    @pytest.mark.parametrize("body", [{"response": ""}, {"response": "too short"}, {}])
    def test_unusably_short_output_is_a_failure_not_an_explanation(
        self, llm_config, monkeypatch, body
    ):
        """
        A one-line non-answer returned as an explanation is worse than falling
        back: it looks deliberate.
        """
        self._with_post(monkeypatch, FakeResponse(200, body))
        assert OllamaProvider(llm_config).explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_one_result_per_context(self, llm_config, monkeypatch):
        self._with_post(monkeypatch, FakeResponse(200, {"response": GOOD_TEXT}))
        assert len(OllamaProvider(llm_config).explain([CONTEXT] * 3)) == 3

    @pytest.mark.unit
    def test_the_payload_carries_the_configured_model_and_options(self, llm_config, monkeypatch):
        seen = {}

        def post(url, json=None, timeout=None, **k):
            seen.update({"url": url, "json": json, "timeout": timeout})
            return FakeResponse(200, {"response": GOOD_TEXT})

        monkeypatch.setattr("src.agents.explaining.ollama.requests.post", post)
        OllamaProvider(llm_config).explain([CONTEXT])

        assert seen["url"].endswith("/api/generate")
        assert seen["json"]["model"] == llm_config.model
        assert seen["json"]["stream"] is False
        assert seen["json"]["options"]["temperature"] == llm_config.temperature
        assert seen["timeout"] == llm_config.timeout_seconds


class FakeCompletions:
    def __init__(self, behaviour="ok"):
        self.behaviour = behaviour
        self.kwargs = None

    def create(self, **kwargs):
        self.kwargs = kwargs
        if isinstance(self.behaviour, Exception):
            raise self.behaviour
        import types

        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=self.behaviour))]
        )


class FakeClient:
    def __init__(self, behaviour="ok"):
        completions = FakeCompletions(behaviour)
        self.completions = completions
        import types

        self.chat = types.SimpleNamespace(completions=completions)


def _openrouter(llm_config, behaviour):
    provider = OpenRouterProvider(llm_config, api_key="sk-test-not-a-real-key")
    client = FakeClient(behaviour)
    provider._client = client
    return provider, client


class TestOpenRouterCalls:
    @pytest.mark.unit
    def test_returns_the_completion_text(self, llm_config):
        provider, _ = _openrouter(llm_config, GOOD_TEXT)
        out = provider.explain([CONTEXT])
        assert out[0].source == "openrouter"
        assert out[0].text.startswith("This candidate")

    @pytest.mark.unit
    def test_sends_a_system_and_a_user_message(self, llm_config):
        provider, client = _openrouter(llm_config, GOOD_TEXT)
        provider.explain([CONTEXT])
        roles = [m["role"] for m in client.completions.kwargs["messages"]]
        assert roles == ["system", "user"]

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "error",
        [
            RuntimeError("429 rate limit exceeded"),
            TimeoutError("request timed out"),
            ConnectionError("name resolution failed"),
        ],
    )
    def test_any_call_failure_yields_none(self, llm_config, error):
        provider, _ = _openrouter(llm_config, error)
        assert provider.explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_a_rate_limit_sets_the_shared_backoff(self, llm_config):
        """
        Retry-After is the server stating the answer. Guessing instead is a
        slower way to get rate-limited again.
        """
        error = RuntimeError("429")
        error.response = type("R", (), {"headers": {"retry-after": "7"}})()
        provider, _ = _openrouter(llm_config, error)

        provider.explain([CONTEXT])
        assert provider.throttle._blocked_until > 0

    @pytest.mark.unit
    def test_unusably_short_output_is_a_failure(self, llm_config):
        provider, _ = _openrouter(llm_config, "no")
        assert provider.explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_no_client_means_every_item_is_none(self, llm_config):
        """No key configured: the batch fails wholesale rather than partially."""
        provider = OpenRouterProvider(llm_config, api_key=None)
        assert provider.explain([CONTEXT, CONTEXT]) == [None, None]

    @pytest.mark.unit
    def test_the_model_can_be_overridden(self, llm_config):
        provider = OpenRouterProvider(llm_config, api_key="sk-x", model="acme/model-1")
        assert provider.model == "acme/model-1"


class TestLangChainProvider:
    @pytest.mark.unit
    def test_unavailable_without_the_package(self, llm_config, monkeypatch):
        provider = LangChainProvider(llm_config)
        monkeypatch.setattr(provider, "_get_llm", lambda: None)
        assert provider.is_available() is False
        assert provider.explain([CONTEXT, CONTEXT]) == [None, None]

    @pytest.mark.unit
    def test_extracts_content_from_a_message_object(self, llm_config, monkeypatch):
        """
        LangChain returns a message, not a string -- one of the four response
        shapes ADR-2 flagged as needing normalisation.
        """
        import types

        class FakeLLM:
            def invoke(self, messages):
                return types.SimpleNamespace(content=GOOD_TEXT)

        provider = LangChainProvider(llm_config)
        monkeypatch.setattr(provider, "_get_llm", lambda: FakeLLM())
        out = provider.explain([CONTEXT])
        assert out[0].source == "langchain"
        assert out[0].text.startswith("This candidate")

    @pytest.mark.unit
    def test_an_invocation_failure_yields_none(self, llm_config, monkeypatch):
        class FailingLLM:
            def invoke(self, messages):
                raise RuntimeError("model unavailable")

        provider = LangChainProvider(llm_config)
        monkeypatch.setattr(provider, "_get_llm", lambda: FailingLLM())
        assert provider.explain([CONTEXT]) == [None]

    @pytest.mark.unit
    def test_a_response_with_no_content_yields_none(self, llm_config, monkeypatch):
        import types

        class EmptyLLM:
            def invoke(self, messages):
                return types.SimpleNamespace(content=None)

        provider = LangChainProvider(llm_config)
        monkeypatch.setattr(provider, "_get_llm", lambda: EmptyLLM())
        assert provider.explain([CONTEXT]) == [None]
