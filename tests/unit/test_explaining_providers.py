"""
Unit tests for Agent 4's provider protocol (ADR-2).

Three things are worth testing here and the rest is prose generation:

1. **The fallback chain.** Every provider failure mode must still produce an
   explanation for every input, tagged with what produced it. Falling back is
   normal operation, not an incident.
2. **Malformed responses.** ADR-2 named response normalisation as the place
   bugs would appear, so each shape a provider can return badly gets a case.
3. **No mutable state.** The A7 race existed because provider selection lived
   in a mutable attribute on a shared object. These assert it is not possible
   to get back into that position.
"""
import types

import pytest

from src.agents.explaining import (
    ExplainerAgent,
    Explanation,
    ExplanationContext,
    LLMProvider,
    LangChainProvider,
    OllamaProvider,
    OpenRouterProvider,
    RuleBasedProvider,
    build_provider,
)


CONTEXT = ExplanationContext(
    candidate_name="Jane Doe",
    job_title="Backend Engineer",
    final_score=0.82,
    decision="shortlist",
    confidence=0.9,
    skill_score=0.80,
    experience_score=0.90,
    education_score=1.0,
    keyword_score=0.60,
    matched_skills=["Python", "Docker", "AWS"],
    missing_skills=["Kafka"],
)


class Fake:
    """A provider is five lines. That is the point of the protocol."""

    name = "fake"

    def __init__(self, behaviour="ok"):
        self.behaviour = behaviour
        self.calls = 0

    def is_available(self) -> bool:
        return self.behaviour != "unavailable"

    def explain(self, batch):
        self.calls += 1
        if self.behaviour == "raise":
            raise RuntimeError("quota exceeded")
        if self.behaviour == "none":
            return [None] * len(batch)
        if self.behaviour == "short":
            return []
        return [Explanation("x" * 100, self.name) for _ in batch]


class TestProtocolConformance:
    @pytest.mark.unit
    @pytest.mark.parametrize("cls", [
        RuleBasedProvider, OllamaProvider, OpenRouterProvider, LangChainProvider,
    ])
    def test_every_provider_satisfies_the_protocol(self, cls):
        assert isinstance(cls.__new__(cls), LLMProvider)

    @pytest.mark.unit
    @pytest.mark.parametrize("cls", [
        RuleBasedProvider, OllamaProvider, OpenRouterProvider, LangChainProvider,
    ])
    def test_every_provider_names_itself(self, cls):
        assert isinstance(cls.name, str) and cls.name


class TestFallbackChain:
    """The user always gets an explanation."""

    @pytest.mark.unit
    @pytest.mark.parametrize("behaviour", ["raise", "none", "short", "unavailable"])
    def test_any_failure_still_explains_every_input(self, behaviour):
        out = ExplainerAgent(Fake(behaviour)).explain([CONTEXT, CONTEXT])
        assert len(out) == 2
        assert all(e.text for e in out)
        assert all(e.source == "rule_based" for e in out)

    @pytest.mark.unit
    def test_a_working_provider_is_used(self):
        out = ExplainerAgent(Fake("ok")).explain([CONTEXT])
        assert out[0].source == "fake"

    @pytest.mark.unit
    def test_fallback_is_per_item_not_per_batch(self):
        """One bad response must not discard the good ones beside it."""
        class Partial(Fake):
            def explain(self, batch):
                return [Explanation("y" * 100, self.name), None]

        out = ExplainerAgent(Partial()).explain([CONTEXT, CONTEXT])
        assert [e.source for e in out] == ["fake", "rule_based"]

    @pytest.mark.unit
    def test_use_llm_false_never_calls_the_provider(self):
        fake = Fake("ok")
        out = ExplainerAgent(fake).explain([CONTEXT], use_llm=False)
        assert fake.calls == 0
        assert out[0].source == "rule_based"

    @pytest.mark.unit
    def test_empty_batch_is_empty_not_an_error(self):
        assert ExplainerAgent(Fake()).explain([]) == []


class TestNoMutableState:
    """
    The A7 race existed because per-request settings were written onto a shared
    singleton, and the restore was not in a finally block -- so one raising
    request altered every later one.
    """

    @pytest.mark.unit
    def test_provider_is_not_swapped_by_a_request(self):
        agent = ExplainerAgent(Fake("ok"))
        before = agent.provider
        agent.explain([CONTEXT], use_llm=False)
        agent.explain([CONTEXT], use_llm=True)
        assert agent.provider is before

    @pytest.mark.unit
    def test_a_raising_provider_leaves_the_agent_intact(self):
        agent = ExplainerAgent(Fake("raise"))
        before = agent.provider
        agent.explain([CONTEXT])
        assert agent.provider is before
        assert agent.explain([CONTEXT])[0].text

    @pytest.mark.unit
    def test_llm_available_is_read_only(self):
        agent = ExplainerAgent(Fake("ok"))
        with pytest.raises(AttributeError):
            agent.llm_available = False


class TestRuleBasedProvider:
    @pytest.mark.unit
    def test_always_available(self):
        assert RuleBasedProvider().is_available() is True

    @pytest.mark.unit
    def test_one_explanation_per_context(self):
        out = RuleBasedProvider().explain([CONTEXT, CONTEXT, CONTEXT])
        assert len(out) == 3

    @pytest.mark.unit
    def test_explanation_is_substantial(self):
        assert len(RuleBasedProvider().explain([CONTEXT])[0].text) > 50

    @pytest.mark.unit
    def test_names_actual_skills(self):
        text = RuleBasedProvider().explain([CONTEXT])[0].text
        assert "Python" in text
        assert "Kafka" in text

    @pytest.mark.unit
    def test_deterministic(self):
        """
        Variant selection used hash(candidate) % 3. Python randomises string
        hashing per process, so the same candidate got a different opening
        after every restart -- the ADR-1 determinism rule, broken the same way
        Agent 3's keyword scoring was. crc32 is stable across processes.
        """
        provider = RuleBasedProvider()
        assert provider.explain([CONTEXT])[0].text == provider.explain([CONTEXT])[0].text

    @pytest.mark.unit
    @pytest.mark.parametrize("decision", ["shortlist", "review", "reject"])
    def test_every_decision_produces_a_recommendation(self, decision):
        import dataclasses
        ctx = dataclasses.replace(CONTEXT, decision=decision)
        assert len(RuleBasedProvider().explain([ctx])[0].text) > 50


class TestOpenRouterResponseHandling:
    """ADR-2 flagged normalisation as where bugs appear. One case per shape."""

    @staticmethod
    def _response(choices):
        return types.SimpleNamespace(choices=choices)

    @staticmethod
    def _message(content):
        return types.SimpleNamespace(message=types.SimpleNamespace(content=content))

    @pytest.mark.unit
    def test_extracts_normal_content(self):
        r = self._response([self._message("hello" * 20)])
        assert OpenRouterProvider._extract(r).startswith("hello")

    @pytest.mark.unit
    @pytest.mark.parametrize("choices", [[], None])
    def test_missing_choices_is_none_not_a_crash(self, choices):
        assert OpenRouterProvider._extract(self._response(choices)) is None

    @pytest.mark.unit
    @pytest.mark.parametrize("content", [None, "", "   "])
    def test_empty_content_is_empty_not_a_crash(self, content):
        assert not OpenRouterProvider._extract(self._response([self._message(content)]))

    @pytest.mark.unit
    def test_garbage_object_is_none_not_a_crash(self):
        assert OpenRouterProvider._extract(object()) is None

    @pytest.mark.unit
    def test_no_api_key_means_unavailable(self):
        from src.core.config import get_config
        provider = OpenRouterProvider(get_config().llm, api_key=None)
        assert provider.is_available() is False

    @pytest.mark.unit
    def test_key_is_never_exposed_on_the_instance_repr(self):
        from src.core.config import get_config
        provider = OpenRouterProvider(get_config().llm, api_key="sk-secret-value")
        assert "sk-secret-value" not in repr(provider)


class TestProviderSelection:
    @pytest.mark.unit
    @pytest.mark.parametrize("name,expected", [
        ("ollama", "ollama"),
        ("openrouter", "openrouter"),
        ("langchain", "langchain"),
        ("rule_based", "rule_based"),
    ])
    def test_config_selects_the_provider(self, name, expected):
        assert build_provider(name=name).name == expected

    @pytest.mark.unit
    @pytest.mark.parametrize("name", ["nonsense", "gpt5", "openai"])
    def test_unknown_provider_degrades_to_rule_based(self, name):
        """A typo in config must not take the API down."""
        assert build_provider(name=name).name == "rule_based"

    @pytest.mark.unit
    @pytest.mark.parametrize("name", ["", None])
    def test_unset_provider_uses_the_configured_default(self, name):
        """
        Empty means unset, not unknown. `provider: ""` in a YAML file is an
        absent setting and should land on the configured default -- only a name
        that was actually chosen and is not recognised is a typo worth
        degrading for.
        """
        assert build_provider(name=name).name == "ollama"
