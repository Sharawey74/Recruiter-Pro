"""
Scoring weights must have exactly one definition.

The bug these tests exist to prevent: config/agents.yaml declared
skill/experience/education/keyword weights, ScoringConfig declared the same
four, and src/agents/agent3_scorer.py applied a different five -- including a
title component no config mentioned. Editing the YAML changed nothing, and the
sum-to-1.0 validator guarded numbers that were never used.

test_yaml_matches_dataclass_defaults is the guard: it fails the moment the two
declarations drift apart again.
"""
from pathlib import Path

import pytest
import yaml

from src.core.config import PROJECT_ROOT, Config, ScoringConfig

AGENTS_YAML = PROJECT_ROOT / "config" / "agents.yaml"

RULE_WEIGHT_FIELDS = [
    "skill_weight",
    "title_weight",
    "experience_weight",
    "education_weight",
    "keyword_weight",
]


class TestScoringWeights:
    def test_rule_weights_sum_to_one(self):
        cfg = ScoringConfig()
        total = sum(getattr(cfg, f) for f in RULE_WEIGHT_FIELDS)
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_ml_and_rule_weights_sum_to_one(self):
        cfg = ScoringConfig()
        assert cfg.ml_weight + cfg.rule_weight == pytest.approx(1.0, abs=1e-9)

    def test_title_weight_exists(self):
        """Title similarity carries real weight; it must be declared, not implicit."""
        assert hasattr(ScoringConfig(), "title_weight")
        assert ScoringConfig().title_weight > 0

    @pytest.mark.parametrize("field", RULE_WEIGHT_FIELDS)
    def test_invalid_rule_weight_is_rejected(self, field):
        """Validation runs on construction, not only when a YAML happens to be found."""
        with pytest.raises(ValueError, match="Rule weights must sum to 1.0"):
            ScoringConfig(**{field: 0.9})

    def test_invalid_ml_split_is_rejected(self):
        with pytest.raises(ValueError, match="ML and rule weights must sum to 1.0"):
            ScoringConfig(ml_weight=0.9)

    def test_error_message_names_the_file_and_the_values(self):
        """get_config() runs at import time, so the traceback has to be self-explanatory."""
        with pytest.raises(ValueError) as exc:
            ScoringConfig(skill_weight=0.9)
        message = str(exc.value)
        assert "config/agents.yaml" in message
        assert "skill_weight=0.9" in message


class TestSingleSourceOfTruth:
    def test_yaml_matches_dataclass_defaults(self):
        """
        The regression guard for item 2.3.

        If someone retunes config/agents.yaml without updating the dataclass
        defaults (or the reverse), this fails and names the offending key.
        """
        raw = yaml.safe_load(AGENTS_YAML.read_text(encoding="utf-8"))
        declared = raw["scoring"]
        defaults = ScoringConfig()

        for field in RULE_WEIGHT_FIELDS:
            assert field in declared, f"{field} missing from config/agents.yaml"
            assert declared[field] == pytest.approx(getattr(defaults, field)), (
                f"{field} disagrees: agents.yaml={declared[field]}, "
                f"ScoringConfig default={getattr(defaults, field)}"
            )

    def test_yaml_weights_are_loadable(self):
        cfg = Config.from_yaml(AGENTS_YAML)
        total = sum(getattr(cfg.scoring, f) for f in RULE_WEIGHT_FIELDS)
        assert total == pytest.approx(1.0, abs=1e-9)

    def test_scorer_reads_weights_from_config(self):
        """
        Proves the weights are not hardcoded in the scorer any more.

        Changing a weight on the config must change the score. Before item 2.3
        this assertion failed -- the scorer ignored config entirely.
        """
        import json

        from src.agents.agent3_scorer import HybridScoringAgent
        from src.storage.models import CVProfile, JobPosting

        payload = json.loads(
            (PROJECT_ROOT / "data/json/jobs.json").read_text(encoding="utf-8")
        )
        job = JobPosting(**payload["jobs"][0])
        cv = CVProfile(
            cv_id="weights-probe",
            file_name="weights-probe.pdf",
            skills=["Python", "Machine Learning"],
            experience_years=5,
            education="Bachelor's",
            extracted_data={"current_title": "Machine Learning Engineer"},
        )

        agent = HybridScoringAgent()
        before = agent.score_match(cv, job, include_ml=False).rule_based_score

        # Shift weight from skills to title, keeping the sum at 1.0.
        agent.scoring_config.skill_weight = 0.30
        agent.scoring_config.title_weight = 0.37
        after = agent.score_match(cv, job, include_ml=False).rule_based_score

        assert before != after, "scorer ignored the config weights"
