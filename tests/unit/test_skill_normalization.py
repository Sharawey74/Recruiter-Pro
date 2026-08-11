"""
Regression tests for skill normalization — the A0 bug.

`_get_canonical_skill` assumed the vocabulary file was flat
(`{canonical: [aliases]}`) when it is nested by family. Iterating it bound
`canonical` to the *family name* and `aliases` to the inner dict, so the alias
membership test ran against the inner dict's keys and the function returned
the family name. Every programming language normalized to
"programming_languages", so a Python developer scored a perfect skill match
against a Java job.

Skills are 50% of the rule-based score, which is 60% of the hybrid score, so
roughly a third of every score the product reported was noise — biased upward,
silently, with no exception and no log line.

These tests are the guard that should have existed from the start.
"""
import pytest

from src.agents.agent3_scorer import HybridScoringAgent


@pytest.fixture(scope="module")
def agent():
    """A real agent, reading the real vocabulary file from config."""
    return HybridScoringAgent()


class TestSkillNormalizationIsNotCategoryCollapse:
    """The core defect: unrelated skills must not normalize to the same string."""

    @pytest.mark.unit
    @pytest.mark.parametrize("a, b", [
        ("python", "java"),          # both were "programming_languages"
        ("python", "javascript"),
        ("java", "javascript"),
        ("react", "django"),         # both were "frameworks"
        ("mysql", "postgresql"),     # both were "databases"
    ])
    def test_unrelated_skills_do_not_collapse(self, agent, a, b):
        na = agent._normalize_skills([a])[0]
        nb = agent._normalize_skills([b])[0]
        assert na != nb, (
            f"{a!r} and {b!r} both normalized to {na!r} — unrelated skills are "
            f"being collapsed, so they will match each other perfectly."
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("skill", [
        "python", "java", "react", "docker", "mysql", "excel", "salesforce",
    ])
    def test_normalization_never_returns_a_family_name(self, agent, skill):
        """
        A family name is never a valid canonical skill. This is the specific
        symptom A0 produced, and it was visible in the UI: match cards
        displayed 'programming_languages' and 'devops' as if they were skills.
        """
        result = agent._normalize_skills([skill])[0]
        family_names = {
            "programming_languages", "frameworks", "databases", "devops",
            "cloud", "tools", "soft_skills", "data_science", "families",
        }
        assert result.lower() not in family_names, (
            f"{skill!r} normalized to the family name {result!r}"
        )

    @pytest.mark.unit
    def test_aliases_resolve_to_their_canonical_form(self, agent):
        """The point of having a vocabulary at all."""
        assert agent._normalize_skills(["py"]) == agent._normalize_skills(["python"])
        assert agent._normalize_skills(["js"]) == agent._normalize_skills(["javascript"])

    @pytest.mark.unit
    def test_normalization_is_deterministic(self, agent):
        """Same input, same output — required by ADR-1 for Agent 3."""
        skills = ["python", "docker", "aws", "sql", "react"]
        assert agent._normalize_skills(skills) == agent._normalize_skills(skills)

    @pytest.mark.unit
    def test_unknown_skills_pass_through_unchanged(self, agent):
        """A skill absent from the vocabulary must survive, not vanish."""
        assert agent._normalize_skills(["quantum basket weaving"]) == [
            "quantum basket weaving"
        ]


class TestScoringConsequence:
    """The behaviour that matters: a Python CV must not match a Java-only job."""

    @pytest.mark.unit
    def test_python_cv_does_not_perfectly_match_a_java_job(self, agent):
        cv_skills = set(agent._normalize_skills(["Python", "Django", "PostgreSQL"]))
        java_job = set(agent._normalize_skills(["Java", "Spring", "Oracle"]))
        assert not (cv_skills & java_job), (
            f"A Python CV shares {cv_skills & java_job} with a Java-only job."
        )

    @pytest.mark.unit
    def test_matching_skills_still_match(self, agent):
        """The fix must not break the case that is supposed to work."""
        cv_skills = set(agent._normalize_skills(["Python", "Docker"]))
        job = set(agent._normalize_skills(["python", "docker"]))
        assert cv_skills == job


class TestSubstringCollisions:
    """
    A0's failure mode survived in a second place.

    After skills were correctly canonicalised, _find_skill_matches still granted
    credit on raw substrings: `job_skill in cv_skill or cv_skill in job_skill`
    for anything four characters or longer. Twenty-nine ordered collisions exist
    among the canonical names, so a CV holding JavaScript satisfied a Java
    requirement, and ".NET" -- which normalised to the bare string "net" --
    satisfied "Penetration Testing", because n-e-t appears inside "PeNETration".

    Partial credit is now granted on whole tokens and only in one direction:
    holding the specialisation satisfies a requirement for the general skill,
    never the reverse.
    """

    @pytest.mark.unit
    @pytest.mark.parametrize("job_skill,cv_skill", [
        ("Java", "JavaScript"),
        ("Git", "GitHub"),
        ("Git", "GitHub Actions"),
        ("SQL", "MySQL"),
        ("Swift", "SwiftUI"),
        ("Penetration Testing", ".NET"),
    ])
    def test_substring_overlap_is_not_a_match(self, agent, job_skill, cv_skill):
        cv = set(agent._normalize_skills([cv_skill]))
        assert not agent._find_skill_matches(cv, set(agent._normalize_skills([job_skill]))), (
            f"{cv_skill!r} should not satisfy a {job_skill!r} requirement"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("job_skill,cv_skill", [
        ("Ruby", "Ruby on Rails"),
        ("React", "React Native"),
        ("Communication", "Written Communication"),
        (".NET", "ASP.NET"),
    ])
    def test_holding_the_specialisation_satisfies_the_general_skill(self, agent, job_skill, cv_skill):
        cv = set(agent._normalize_skills([cv_skill]))
        assert agent._find_skill_matches(cv, set(agent._normalize_skills([job_skill]))), (
            f"{cv_skill!r} should satisfy a {job_skill!r} requirement"
        )

    @pytest.mark.unit
    @pytest.mark.parametrize("job_skill,cv_skill", [
        ("Ruby on Rails", "Ruby"),
        ("React Native", "React"),
        ("Written Communication", "Communication"),
    ])
    def test_the_general_skill_does_not_satisfy_the_specialisation(self, agent, job_skill, cv_skill):
        cv = set(agent._normalize_skills([cv_skill]))
        assert not agent._find_skill_matches(cv, set(agent._normalize_skills([job_skill]))), (
            f"{cv_skill!r} should not satisfy a {job_skill!r} requirement"
        )


class TestPunctuatedSkillsResolve:
    """Six canonical skills were unreachable by their own name -- punctuation
    was stripped before the vocabulary was consulted, so '.NET' became 'net'."""

    @pytest.mark.unit
    @pytest.mark.parametrize("skill", [
        ".NET", "T-SQL", "Monday.com", "Outreach.io", "Stand-ups",
        "Non-Conformance Management",
    ])
    def test_punctuated_canonical_resolves_to_itself(self, agent, skill):
        assert agent._normalize_skills([skill])[0] == skill

    @pytest.mark.unit
    @pytest.mark.parametrize("given,expected", [
        ("node.js", "Node.js"), ("dev-ops", "DevOps"), ("c++", "C++"),
    ])
    def test_stripped_fallback_still_resolves(self, agent, given, expected):
        """Forms the index does not carry verbatim must still resolve."""
        assert agent._normalize_skills([given])[0] == expected
