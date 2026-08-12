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
from typing import Optional

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
            # Prepare CV data for ML predictor
            cv_data = {
                'Skills': ', '.join(cv.skills),
                'Experience': cv.experience_years or 0,
                'Education': cv.education or 'Bachelor',
                'Certifications': cv.extracted_data.get('certifications', 'None'),
                'Job Role': job.title,
                'Projects Count': cv.extracted_data.get('projects_count', 0),
                'Salary': cv.extracted_data.get('expected_salary', 50000)
            }

            result = self.predictor.predict(cv_data, use_optimal_threshold=True)

        except Exception as e:  # noqa: BLE001 - scoring must survive a bad row
            logger.error(f"ML scoring failed: {e}")
            return None

        if not result:
            return None

        raw = result['ml_score']
        return raw / 100.0 if raw > 1 else raw
