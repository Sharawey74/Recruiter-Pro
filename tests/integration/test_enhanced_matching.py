"""
Agents 1 -> 2 -> 3 against a real file on disk.

This file previously contained a demo script: it parsed a resume that was not
in the repository, printed a scoring table, and asserted **nothing**. pytest
collected it because of the name, so it counted toward the suite while being
incapable of failing for any reason except the missing file -- which is exactly
how it failed, on every run, for as long as it existed.

Rewritten as the test the name promised. It is the only coverage that starts
from a file rather than a constructed CVProfile, so it is what would catch a
break in the hand-off between the three agents.
"""
import json
from pathlib import Path

import pytest

from src.agents.agent1_parser import RawParser
from src.agents.agent2_extractor import CandidateExtractor
from src.agents.agent3_scorer import HybridScoringAgent
from src.storage.models import CVProfile, JobPosting

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SAMPLE_CV = Path(__file__).resolve().parents[1] / "fixtures" / "sample_cv.txt"


@pytest.fixture(scope="module")
def parsed_cv():
    """The real Agent 1 -> Agent 2 hand-off, from a real file."""
    raw = RawParser().parse_file(str(SAMPLE_CV))
    extracted = CandidateExtractor().extract(raw.get("raw_text", ""))

    education = extracted.get("education") or None
    if isinstance(education, list):
        education = ", ".join(education) or None

    return CVProfile(
        cv_id="enhanced-matching",
        file_name=SAMPLE_CV.name,
        file_path=str(SAMPLE_CV),
        name=extracted.get("name"),
        email=extracted.get("email"),
        skills=extracted.get("skills", []),
        experience_years=extracted.get("experience_years"),
        education=education,
        raw_text=raw.get("raw_text", ""),
        extracted_data=extracted,
    )


@pytest.fixture(scope="module")
def jobs():
    payload = json.loads(
        (PROJECT_ROOT / "data/json/jobs.json").read_text(encoding="utf-8")
    )
    return [JobPosting(**j) for j in payload["jobs"][:120]]


@pytest.mark.integration
class TestAgentHandoff:
    """Each agent's output has to be usable by the next one."""

    def test_agent1_extracts_text(self, parsed_cv):
        assert len(parsed_cv.raw_text) > 200

    def test_agent2_finds_the_contact_details(self, parsed_cv):
        assert parsed_cv.email == "jordan.ellis@example.com"
        assert parsed_cv.name

    def test_agent2_finds_the_skills_the_cv_lists(self, parsed_cv):
        skills = {s.lower() for s in parsed_cv.skills}
        for expected in ("python", "docker", "kubernetes", "postgresql"):
            assert expected in skills, f"{expected} missing from {sorted(skills)}"

    def test_agent2_reads_the_experience(self, parsed_cv):
        assert parsed_cv.experience_years == 8

    def test_agent2_output_is_canonical_for_agent3(self, parsed_cv):
        """
        The point of the shared vocabulary: a skill Agent 2 extracts must be
        one Agent 3 can match. Before they shared an index, Agent 2 could
        produce names Agent 3 had never heard of and the candidate silently
        lost the points.
        """
        matcher = HybridScoringAgent().skill_matcher
        canonical = set(matcher.skills_index.values())
        for skill in parsed_cv.skills:
            assert skill in canonical, f"{skill!r} is not a canonical name"


@pytest.mark.integration
class TestScoringAcrossTheCorpus:
    def test_every_job_scores_in_range(self, parsed_cv, jobs):
        agent = HybridScoringAgent()
        for breakdown in agent.score_matches(parsed_cv, jobs, include_ml=False):
            assert 0.0 <= breakdown.hybrid_score <= 1.0
            assert 0.0 <= breakdown.skill_score <= 1.0

    def test_the_breakdown_reconstructs_the_rule_score(self, parsed_cv, jobs):
        """
        Every returned component, weighted, must add up to rule_based_score.
        title_score was computed, weighted at 17% and then discarded, so the
        components the API returned could not reconstruct the total.
        """
        agent = HybridScoringAgent()
        w = agent.scoring_config
        for b in agent.score_matches(parsed_cv, jobs[:40], include_ml=False):
            expected = (
                b.skill_score * w.skill_weight
                + b.title_score * w.title_weight
                + b.experience_score * w.experience_weight
                + b.education_score * w.education_weight
                + b.keyword_score * w.keyword_weight
            )
            assert b.rule_based_score == pytest.approx(expected, abs=1e-12)

    def test_a_backend_cv_beats_unrelated_roles(self, parsed_cv, jobs):
        """
        The product claim, at its coarsest: this CV should rank an engineering
        job above a job sharing none of its skills. A0 broke exactly this --
        every skill collapsed to its family name, so a Python CV matched a Java
        job perfectly.
        """
        agent = HybridScoringAgent()
        scored = list(zip(jobs, agent.score_matches(parsed_cv, jobs, include_ml=False)))
        scored.sort(key=lambda pair: -pair[1].hybrid_score)

        best_job, best = scored[0]
        worst_job, worst = scored[-1]
        assert best.hybrid_score > worst.hybrid_score
        assert best.matched_skills, f"top match {best_job.job_id} matched no skills at all"

    def test_scoring_does_not_mutate_the_cv(self, parsed_cv, jobs):
        before = list(parsed_cv.skills)
        HybridScoringAgent().score_matches(parsed_cv, jobs[:20], include_ml=False)
        assert parsed_cv.skills == before
