"""
Mechanical validation of a generated job corpus.

Turns every self-check item in JOBS_DATASET_SPEC.md into an assertion. A model
confirming its own output is not verification; this is.

Usage:
    python scripts/validate_corpus.py
    python scripts/validate_corpus.py --jobs data/json/jobs.json \
                                      --skills data/dictionaries/skills.json

Exit code 0 = corpus is loadable and internally consistent. Non-zero = do not ship it.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CATEGORIES = [
    "engineering", "sales", "marketing", "accounting",
    "management", "administrators", "maintenance", "operations",
]
PREFIX = {
    "engineering": "ENG", "sales": "SAL", "marketing": "MKT", "accounting": "ACC",
    "management": "MGT", "administrators": "ADM", "maintenance": "MNT", "operations": "OPS",
}
# seniority -> (min_lo, min_hi, max_lo, max_hi)
SENIORITY_BANDS = {
    "entry": (0, 1, 2, 3),
    "mid": (2, 4, 5, 7),
    "senior": (5, 8, 9, 12),
    "lead": (8, 10, 12, 15),
    "manager": (8, 12, 15, 18),
    "executive": (12, 18, 20, 25),
}
REMOTE_ALLOWED = {
    "maintenance": {"on-site"},
    "operations": {"on-site", "hybrid"},
    "administrators": {"on-site", "hybrid", "remote"},
}
DEFAULT_REMOTE = {"on-site", "hybrid", "remote"}
EDUCATION = ["High School", "Diploma", "Associate", "Bachelor's", "Master's", "PhD"]
DESC_MIN, DESC_MAX = 900, 1400
DESC_HEADINGS = ["About the role", "Responsibilities", "Requirements", "Nice to have"]
FORBIDDEN_KEYS = {"company", "location", "job_type", "created_at"}


class Report:
    """Collects failures so one run surfaces every problem, not just the first."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.checks = 0

    def check(self, label: str, ok: bool, detail: str = "") -> bool:
        self.checks += 1
        if ok:
            print(f"  PASS  {label}")
        else:
            print(f"  FAIL  {label}")
            if detail:
                for line in detail.splitlines():
                    print(f"        {line}")
            self.failures.append(label)
        return ok

    def warn(self, label: str, detail: str = "") -> None:
        print(f"  WARN  {label}")
        if detail:
            print(f"        {detail}")
        self.warnings.append(label)


def _sample(items, n: int = 6) -> str:
    items = sorted(items)
    shown = ", ".join(str(i) for i in items[:n])
    return f"{len(items)} item(s): {shown}{' ...' if len(items) > n else ''}"


def canonical_names(skills_raw: dict) -> set[str]:
    """Every canonical skill name, from either the flat or _meta/families layout."""
    families = skills_raw.get("families")
    if families is None:
        families = {k: v for k, v in skills_raw.items() if isinstance(v, dict)}
    names: set[str] = set()
    for family in families.values():
        if isinstance(family, dict):
            names.update(family.keys())
    return names


def validate(jobs_path: Path, skills_path: Path) -> int:
    r = Report()

    # ---------- load ----------
    print("\n[1] Loading files")
    if not r.check(f"{jobs_path} exists", jobs_path.exists()):
        return 1
    if not r.check(f"{skills_path} exists", skills_path.exists()):
        return 1

    payload = json.loads(jobs_path.read_text(encoding="utf-8"))
    skills_raw = json.loads(skills_path.read_text(encoding="utf-8"))

    r.check("jobs file is an object with a 'jobs' key (not a bare array)",
            isinstance(payload, dict) and "jobs" in payload,
            "Expected the envelope: {schema_version, generated_at, ..., jobs: [...]}")
    if not isinstance(payload, dict) or "jobs" not in payload:
        return 1

    jobs = payload["jobs"]
    vocab = canonical_names(skills_raw)
    vocab_lower = {v.lower() for v in vocab}
    print(f"        {len(jobs)} jobs, {len(vocab)} canonical skills")

    # ---------- structural ----------
    print("\n[2] Structure and identity")
    r.check("record_count matches actual length",
            payload.get("record_count") == len(jobs),
            f"metadata says {payload.get('record_count')}, file holds {len(jobs)}")

    by_cat = Counter(j.get("category") for j in jobs)
    bad_cat = {c for c in by_cat if c not in CATEGORIES}
    r.check("every category is one of the eight", not bad_cat, _sample(bad_cat))

    uneven = {c: by_cat.get(c, 0) for c in CATEGORIES if by_cat.get(c, 0) != len(jobs) // 8}
    if uneven:
        r.warn("categories are not evenly balanced", str(uneven))

    ids = [j.get("job_id") for j in jobs]
    dupe_ids = {i for i, n in Counter(ids).items() if n > 1}
    r.check("job_id values are unique", not dupe_ids, _sample(dupe_ids))

    bad_prefix = {
        j["job_id"] for j in jobs
        if j.get("category") in PREFIX
        and not str(j.get("job_id", "")).startswith(PREFIX[j["category"]] + "-")
    }
    r.check("job_id prefix matches category", not bad_prefix, _sample(bad_prefix))

    stray = {k for j in jobs for k in j if k in FORBIDDEN_KEYS}
    r.check("no deprecated keys (company/location/job_type/created_at)", not stray, _sample(stray))

    # ---------- the invariant that matters most ----------
    print("\n[3] Skill vocabulary invariant")
    unknown: set[str] = set()
    for j in jobs:
        for s in (j.get("required_skills") or []) + (j.get("preferred_skills") or []):
            if s not in vocab:
                unknown.add(s)
    r.check("every job skill is a canonical name in the vocabulary", not unknown,
            _sample(unknown, 10) if unknown else "")

    case_only = {s for s in unknown if s.lower() in vocab_lower}
    if case_only:
        r.warn("some unknown skills differ only by case (alias used instead of canonical)",
               _sample(case_only, 8))

    overlap = {j.get("job_id") for j in jobs
               if set(j.get("required_skills") or []) & set(j.get("preferred_skills") or [])}
    r.check("required and preferred skills do not overlap", not overlap, _sample(overlap))

    bad_count = {j.get("job_id") for j in jobs
                 if not (5 <= len(j.get("required_skills") or []) <= 9)}
    r.check("each job has 5-9 required skills", not bad_count, _sample(bad_count))

    # ---------- consistency ----------
    print("\n[4] Internal consistency")
    bad_band = []
    for j in jobs:
        band = SENIORITY_BANDS.get(j.get("seniority_level"))
        if not band:
            bad_band.append(f"{j.get('job_id')}: unknown seniority {j.get('seniority_level')!r}")
            continue
        lo_a, lo_b, hi_a, hi_b = band
        mn, mx = j.get("min_experience_years"), j.get("max_experience_years")
        if mn is None or mx is None or not (lo_a <= mn <= lo_b and hi_a <= mx <= hi_b and mx > mn):
            bad_band.append(f"{j.get('job_id')}: {j.get('seniority_level')} has {mn}-{mx}")
    r.check("experience range fits the seniority band", not bad_band,
            "\n".join(bad_band[:6]) + (f"\n... {len(bad_band)} total" if len(bad_band) > 6 else ""))

    bad_remote = {
        f"{j.get('job_id')} ({j.get('category')}={j.get('remote_type')})" for j in jobs
        if j.get("remote_type") not in REMOTE_ALLOWED.get(j.get("category"), DEFAULT_REMOTE)
    }
    r.check("remote_type is possible for the category (maintenance is on-site only)",
            not bad_remote, _sample(bad_remote))

    pairs = Counter((j.get("title"), j.get("company_name")) for j in jobs)
    dupe_pairs = {p for p, n in pairs.items() if n > 1}
    r.check("no duplicate (title, company_name) pairs", not dupe_pairs,
            _sample([f"{t} @ {c}" for t, c in dupe_pairs]))

    bad_edu = {j.get("education_level") for j in jobs if j.get("education_level") not in EDUCATION}
    r.check("education_level is one of the allowed values", not bad_edu, _sample(bad_edu))

    # ---------- descriptions ----------
    print("\n[5] Descriptions")
    bad_len, bad_head, echoes = [], [], []
    for j in jobs:
        d = j.get("description") or ""
        if not (DESC_MIN <= len(d) <= DESC_MAX):
            bad_len.append(f"{j.get('job_id')}: {len(d)} chars")
        if not all(h in d for h in DESC_HEADINGS):
            bad_head.append(str(j.get("job_id")))
        req = j.get("required_skills") or []
        if req and sum(1 for s in req if s.lower() in d.lower()) == len(req):
            echoes.append(str(j.get("job_id")))
    r.check(f"description length within {DESC_MIN}-{DESC_MAX} chars", not bad_len,
            "\n".join(bad_len[:6]) + (f"\n... {len(bad_len)} total" if len(bad_len) > 6 else ""))
    r.check("all four headings present in order", not bad_head, _sample(bad_head))
    if echoes:
        r.warn("descriptions that name every required skill (possible template echo)",
               _sample(echoes, 8) + "\n        Keyword scoring becomes circular when this happens.")

    # ---------- dates ----------
    print("\n[6] Dates")
    gen = payload.get("generated_at")
    try:
        gen_d = date.fromisoformat(gen)
    except (TypeError, ValueError):
        r.check("generated_at is a valid YYYY-MM-DD date", False, f"got {gen!r}")
        gen_d = None
    if gen_d:
        window = gen_d - timedelta(days=90)
        bad_dates = []
        for j in jobs:
            try:
                d = date.fromisoformat(j.get("posted_date"))
            except (TypeError, ValueError):
                bad_dates.append(f"{j.get('job_id')}: {j.get('posted_date')!r}")
                continue
            if not (window <= d <= gen_d):
                bad_dates.append(f"{j.get('job_id')}: {d}")
        r.check("posted_date within 90 days before generated_at", not bad_dates,
                "\n".join(bad_dates[:6]))

    # ---------- the real test: does the app load it ----------
    print("\n[7] Pydantic model acceptance")
    try:
        from src.storage.models import JobPosting
        errs = []
        for j in jobs:
            try:
                JobPosting(**j)
            except Exception as exc:  # noqa: BLE001 - we want the message, whatever it is
                errs.append(f"{j.get('job_id')}: {str(exc).splitlines()[0]}")
        r.check("every record constructs a JobPosting", not errs, "\n".join(errs[:6]))

        if jobs:
            probe = JobPosting(**jobs[0])
            r.check("category survives model construction",
                    getattr(probe, "category", None) == jobs[0].get("category"),
                    "The model is dropping 'category'. Pydantic v2 ignores unknown fields by "
                    "default, so an undeclared field vanishes silently.")
    except ImportError as exc:
        r.warn("could not import JobPosting", str(exc))

    # ---------- verdict ----------
    print("\n" + "=" * 62)
    if r.failures:
        print(f"FAILED - {len(r.failures)} of {r.checks} checks")
        for f in r.failures:
            print(f"  - {f}")
    else:
        print(f"PASSED - all {r.checks} checks")
    if r.warnings:
        print(f"{len(r.warnings)} warning(s): " + "; ".join(r.warnings))
    print("=" * 62)
    return 1 if r.failures else 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--jobs", type=Path, default=PROJECT_ROOT / "data/json/jobs.json")
    p.add_argument("--skills", type=Path,
                   default=PROJECT_ROOT / "data/dictionaries/skills.json")
    a = p.parse_args()
    return validate(a.jobs, a.skills)


if __name__ == "__main__":
    sys.exit(main())
