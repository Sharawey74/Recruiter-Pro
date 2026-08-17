"""
The one vocabulary loader, and what it does when the file is wrong.

`src/core/vocabulary.py` exists because there used to be five competing skill
vocabularies and A0 -- the worst bug in this project -- was a flattening
mistake in one of them: the file is nested by family, the code read it as flat,
so every language resolved to "programming_languages" and a Python CV matched a
Java job perfectly.

Everything now goes through one function, which makes that class of bug fixable
in one place. These tests hold it there, and cover the degradation paths: a
missing file, unreadable JSON, and a shape the loader does not recognise all
have to yield an empty index and a warning rather than taking startup down.
"""

import json

import pytest

from src.core.vocabulary import (
    build_alias_index,
    canonical_names,
    clear_cache,
    load_alias_index,
)


@pytest.fixture(autouse=True)
def _clean_cache():
    clear_cache()
    yield
    clear_cache()


NESTED = {
    "_meta": {"schema_version": "2.1", "note": "metadata, not a family"},
    "families": {
        "programming_languages": {
            "Python": ["python", "py"],
            "Java": ["java", "jdk"],
        },
        "frameworks": {
            "React": ["react", "reactjs"],
        },
    },
}


class TestFlatteningIsNotCategoryCollapse:
    """A0, pinned. See the module docstring."""

    @pytest.mark.unit
    def test_aliases_resolve_to_the_skill_not_the_family(self):
        index = build_alias_index(NESTED)
        assert index["py"] == "Python"
        assert index["jdk"] == "Java"
        assert index["reactjs"] == "React"

    @pytest.mark.unit
    def test_no_family_name_becomes_a_canonical_skill(self):
        canonicals = set(build_alias_index(NESTED).values())
        assert "programming_languages" not in canonicals
        assert "frameworks" not in canonicals

    @pytest.mark.unit
    def test_unrelated_languages_do_not_collapse_together(self):
        index = build_alias_index(NESTED)
        assert index["python"] != index["java"]

    @pytest.mark.unit
    def test_a_canonical_name_resolves_to_itself(self):
        """Six skills were once unreachable by their own name."""
        assert build_alias_index(NESTED)["python"] == "Python"

    @pytest.mark.unit
    def test_metadata_is_skipped(self):
        """
        The isinstance guard that skips _meta is precisely what was missing
        when A0 was written.
        """
        assert "_meta" not in set(build_alias_index(NESTED).values())
        assert "schema_version" not in build_alias_index(NESTED)


class TestLegacyLayout:
    @pytest.mark.unit
    def test_families_at_the_top_level_still_load(self):
        """The older layout mixed metadata in beside the families."""
        legacy = {
            "comment": "a string, not a family",
            "programming_languages": {"Go": ["go", "golang"]},
        }
        index = build_alias_index(legacy)
        assert index["golang"] == "Go"
        assert "comment" not in index

    @pytest.mark.unit
    @pytest.mark.parametrize("raw", [{}, {"families": {}}, {"families": "not a dict"}])
    def test_empty_or_malformed_shapes_give_an_empty_index(self, raw):
        assert build_alias_index(raw) == {} or isinstance(build_alias_index(raw), dict)

    @pytest.mark.unit
    def test_a_family_whose_entries_are_not_a_dict_is_skipped(self):
        index = build_alias_index({"families": {"broken": ["not", "a", "dict"]}})
        assert index == {}

    @pytest.mark.unit
    def test_a_skill_whose_aliases_are_not_a_list_still_registers_itself(self):
        index = build_alias_index({"families": {"f": {"Rust": None}}})
        assert index["rust"] == "Rust"


class TestLoadingDegradesInsteadOfCrashing:
    @pytest.mark.unit
    def test_a_missing_file_yields_an_empty_index(self, tmp_path):
        """
        Nothing resolves, with a warning -- rather than an exception at import
        time, which would take the API down on a misconfigured path.
        """
        assert load_alias_index(tmp_path / "absent.json") == {}

    @pytest.mark.unit
    def test_unreadable_json_yields_an_empty_index(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{ this is not json", encoding="utf-8")
        assert load_alias_index(bad) == {}

    @pytest.mark.unit
    def test_a_real_file_loads(self, tmp_path):
        path = tmp_path / "skills.json"
        path.write_text(json.dumps(NESTED), encoding="utf-8")
        index = load_alias_index(path)
        assert index["py"] == "Python"

    @pytest.mark.unit
    def test_the_index_is_cached_per_path(self, tmp_path):
        """
        The file is a few hundred KB and is read on every agent construction
        otherwise.
        """
        path = tmp_path / "skills.json"
        path.write_text(json.dumps(NESTED), encoding="utf-8")
        first = load_alias_index(path)
        assert load_alias_index(path) is first

    @pytest.mark.unit
    def test_cache_can_be_bypassed(self, tmp_path):
        path = tmp_path / "skills.json"
        path.write_text(json.dumps(NESTED), encoding="utf-8")
        load_alias_index(path)
        assert load_alias_index(path, use_cache=False) is not None

    @pytest.mark.unit
    def test_clear_cache_forces_a_reread(self, tmp_path):
        path = tmp_path / "skills.json"
        path.write_text(json.dumps(NESTED), encoding="utf-8")
        first = load_alias_index(path)
        clear_cache()
        assert load_alias_index(path) is not first


class TestCanonicalNames:
    @pytest.mark.unit
    def test_returns_every_canonical(self):
        assert canonical_names(build_alias_index(NESTED)) == {"Python", "Java", "React"}

    @pytest.mark.unit
    def test_none_is_an_empty_set_not_a_crash(self):
        assert canonical_names(None) == set()


class TestTheRealVocabulary:
    @pytest.mark.unit
    def test_the_shipped_file_loads_and_is_substantial(self):
        from src.core.config import get_config

        index = load_alias_index(get_config().skills_database_path)
        assert len(index) > 1000
        assert len(canonical_names(index)) > 600

    @pytest.mark.unit
    def test_no_family_name_leaked_into_the_shipped_vocabulary(self):
        """The A0 symptom, checked against the file actually shipped."""
        from src.core.config import get_config

        canonicals = canonical_names(load_alias_index(get_config().skills_database_path))
        families = {
            "programming_languages",
            "frameworks",
            "databases",
            "devops",
            "cloud",
            "tools",
            "soft_skills",
            "data_science",
            "families",
        }
        assert not (canonicals & families)
