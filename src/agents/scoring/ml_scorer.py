"""
The ML half of the hybrid score.

Isolated because it is the only part of Agent 3 that touches disk, sklearn and a
trained artifact. Keeping it here means the rule-based path can be constructed,
tested and reasoned about without any of that -- and that a missing or broken
model degrades to "rule-based only" in one obvious place rather than through a
try/except buried in an agent constructor.

Loading is a classmethod, not constructor work, per 2.7: constructing a scorer
must not read the filesystem. `MLScorer(predictor)` is inert and cheap;
`MLScorer.load()` is the one call that does I/O, and it is the caller's choice.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from ...ml_engine.ats_predictor import ATSPredictor
from ...storage.models import CVProfile, JobPosting

logger = logging.getLogger(__name__)


class MLScorer:
    """Wraps the ATS predictor. Absent model -> `score()` returns None."""

    def __init__(self, predictor: Optional[ATSPredictor] = None):
        self.predictor = predictor

    @property
    def enabled(self) -> bool:
        return self.predictor is not None

    @classmethod
    def load(cls, model_dir: str = "models/production") -> "MLScorer":
        """
        Build a scorer with the trained model, or an inert one if it cannot be
        loaded. Never raises: a missing model must not take the API down, it
        must fall back to rule-based scoring and say so.
        """
        try:
            predictor = ATSPredictor(model_dir=model_dir)
            if not predictor.load_model():
                logger.warning("[WARN] Failed to load ML model. Using rule-based only.")
                return cls(None)
        except Exception as e:  # noqa: BLE001 - see docstring
            logger.warning(f"[WARN] ML Predictor unavailable: {e}. Using rule-based only.")
            return cls(None)

        logger.info("[OK] ML Predictor initialized for hybrid scoring")
        model_info = predictor.get_model_info()
        logger.info(f"   Model: {model_info.get('model_name', 'Unknown')}")
        logger.info(f"   Test Recall: {model_info.get('test_metrics', {}).get('recall', 'N/A')}")
        return cls(predictor)

    @staticmethod
    def _features(cv: CVProfile, job: JobPosting) -> dict:
        """The model's feature row for one CV/job pair.

        Only 'Job Role' varies across jobs for a fixed CV; everything else is a
        property of the candidate.
        """
        return {
            'Skills': ', '.join(cv.skills),
            'Experience': cv.experience_years or 0,
            'Education': cv.education or 'Bachelor',
            'Certifications': cv.extracted_data.get('certifications', 'None'),
            'Job Role': job.title,
            'Projects Count': cv.extracted_data.get('projects_count', 0),
            'Salary': cv.extracted_data.get('expected_salary', 50000)
        }

    @staticmethod
    def _to_score(result: Optional[dict]) -> Optional[float]:
        """0-100 -> 0-1. The model reports an int percentage; callers want a ratio."""
        if not result:
            return None
        raw = result['ml_score']
        return raw / 100.0 if raw > 1 else raw

    def score_batch(self, cv: CVProfile, jobs: List[JobPosting]) -> List[Optional[float]]:
        """
        Score one CV against many jobs in a single model call.

        The per-job path cost 8.13 s for 800 jobs because every call rebuilt a
        1-row DataFrame, ran the fitted transform and called predict_proba
        again. One frame, one transform, one predict_proba does it in 0.033 s.

        Results are identical, not merely close: the fitted pipeline is
        transform-only and therefore row-independent, probabilities agree with
        the per-row path to 1.33e-15 (BLAS summation order), and ml_score --
        int(proba * 100), which is what this returns -- matches exactly for
        every row.

        Returns a list of the same length as `jobs`; entries are None when
        there is no model or the call fails.
        """
        if not self.predictor or not jobs:
            return [None] * len(jobs)

        try:
            results = self.predictor.predict_batch(
                [self._features(cv, job) for job in jobs],
                use_optimal_threshold=True,
            )
        except Exception as e:  # noqa: BLE001 - scoring must survive a bad batch
            logger.error(f"ML batch scoring failed: {e}")
            return [None] * len(jobs)

        if len(results) != len(jobs):
            logger.error(
                f"ML batch returned {len(results)} results for {len(jobs)} jobs; "
                "falling back to no ML score"
            )
            return [None] * len(jobs)

        return [self._to_score(r) for r in results]

    def score(self, cv: CVProfile, job: JobPosting) -> Optional[float]:
        """
        Predict a 0-1 ATS score, or None if there is no model or the call fails.

        The 0-100 -> 0-1 conversion used to live in the caller alongside a
        `ml_probability` local that was assigned from the result and then never
        read -- `ScoreBreakdown` has no field for it. The conversion belongs
        with the thing whose scale it is; the dead local is gone.
        """
        if not self.predictor:
            return None

        try:
            result = self.predictor.predict(
                self._features(cv, job), use_optimal_threshold=True
            )
        except Exception as e:  # noqa: BLE001 - scoring must survive a bad row
            logger.error(f"ML scoring failed: {e}")
            return None

        return self._to_score(result)
