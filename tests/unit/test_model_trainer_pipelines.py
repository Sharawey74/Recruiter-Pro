"""
The training pipelines, and model selection.

Training is the least-tested part of this project and the part whose output is
most trusted: a model gets written to models/production/ and every hybrid score
afterwards carries 40% of it. These tests do not check that the model is good
-- the dataset makes that meaningless, see the README -- they check that the
machinery is wired the way the code claims.

Real training runs here, on a tiny synthetic frame with a fixed seed. It is
slow enough to notice and fast enough to keep.
"""

import numpy as np
import pytest
from sklearn.model_selection import ParameterGrid

from src.ml_engine.model_trainer import ATSModelTrainer


@pytest.fixture(scope="module")
def dataset():
    """
    Deliberately imbalanced, 30/70, seeded.

    SMOTE is pinned at sampling_strategy=0.7 and raises on data already more
    balanced than that, so a 50/50 fixture fails deterministically and an
    unseeded one fails intermittently. Both have happened in this repository.
    """
    rng = np.random.default_rng(7)
    n = 120
    X = rng.normal(size=(n, 6))
    y = np.array([1] * int(n * 0.3) + [0] * (n - int(n * 0.3)))
    # Give the positive class a nudge so the fit is not pure noise.
    X[y == 1] += 0.8
    return X, y


@pytest.fixture
def trainer(tmp_path):
    """output_dir at tmp_path: training writes plots and summaries."""
    return ATSModelTrainer(random_state=42, output_dir=str(tmp_path))


class TestPipelineConstruction:
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.parametrize(
        "factory",
        [
            "create_logistic_regression_pipeline",
            "create_random_forest_pipeline",
            "create_xgboost_pipeline",
        ],
    )
    def test_every_pipeline_puts_smote_before_the_classifier(self, trainer, factory):
        """
        Order matters and is easy to get wrong: oversampling before the split
        leaks synthetic minority rows into validation. Inside an imblearn
        pipeline SMOTE runs on the training fold only, which is the whole
        reason for using one.
        """
        pipeline, _ = getattr(trainer, factory)()
        steps = [name for name, _ in pipeline.steps]
        assert steps.index("smote") < steps.index("classifier")

    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.parametrize(
        "factory",
        [
            "create_logistic_regression_pipeline",
            "create_random_forest_pipeline",
            "create_xgboost_pipeline",
        ],
    )
    def test_every_pipeline_returns_a_searchable_grid(self, trainer, factory):
        _, grid = getattr(trainer, factory)()
        assert grid, "an empty grid makes the hyperparameter search a no-op"

        # A search space is one grid or a list of them; sklearn accepts either.
        grids = grid if isinstance(grid, list) else [grid]
        for one in grids:
            assert all(key.startswith("classifier__") for key in one), (
                "grid keys must be namespaced to the pipeline step or the "
                "search silently matches nothing"
            )

    @pytest.mark.unit
    @pytest.mark.ml
    def test_l1_ratio_is_only_searched_where_it_does_something(self, trainer):
        """
        `l1_ratio` applies to elasticnet alone. sklearn ignores it for l1 and l2
        and warns, so a flat grid crossing the two searched 54 combinations for
        30 distinct models -- refitting every l1 and l2 model three times over
        for a parameter that changed nothing about it.

        Refitting was the cheap part. `best_params_` reported an l1_ratio
        alongside a penalty it had no bearing on, and the model card generator
        copies that value out as a hyperparameter of the trained model. This
        asserts on the expansion rather than on the shape of the grid, so it
        holds however the space is expressed.
        """
        _, grid = trainer.create_logistic_regression_pipeline()
        candidates = list(ParameterGrid(grid))

        misapplied = [
            c
            for c in candidates
            if "classifier__l1_ratio" in c and c["classifier__penalty"] != "elasticnet"
        ]
        assert not misapplied, (
            f"{len(misapplied)} candidates vary l1_ratio under a penalty that " f"ignores it"
        )

        elasticnet = [c for c in candidates if c["classifier__penalty"] == "elasticnet"]
        assert elasticnet, "elasticnet dropped out of the search entirely"
        assert all("classifier__l1_ratio" in c for c in elasticnet), (
            "elasticnet without an l1_ratio falls back to sklearn's default "
            "and the mixing parameter goes untuned"
        )

        # Both penalties still reachable: the fix must not have narrowed the
        # search to whichever grid happens to come first.
        penalties = {c["classifier__penalty"] for c in candidates}
        assert penalties == {"l1", "l2", "elasticnet"}

    @pytest.mark.unit
    @pytest.mark.ml
    def test_the_random_state_is_threaded_through(self, trainer):
        """Without this, two runs of the same data produce different models."""
        pipeline, _ = trainer.create_random_forest_pipeline()
        assert pipeline.named_steps["smote"].random_state == 42
        assert pipeline.named_steps["classifier"].random_state == 42


class TestTraining:
    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_training_returns_a_fitted_model_and_metrics(self, trainer, dataset):
        X, y = dataset
        pipeline, grid = trainer.create_logistic_regression_pipeline()

        result = trainer.train_with_grid_search(
            "LogReg", pipeline, grid, X, y, X, y, use_randomized=True, n_iter=2
        )

        assert result["model"] is not None
        assert result["model"].predict(X).shape == y.shape
        for metric in ("recall", "f1", "roc_auc"):
            assert 0.0 <= result["val_metrics"][metric] <= 1.0

    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_training_records_the_run_on_the_trainer(self, trainer, dataset):
        X, y = dataset
        pipeline, grid = trainer.create_logistic_regression_pipeline()
        trainer.train_with_grid_search(
            "LogReg", pipeline, grid, X, y, X, y, use_randomized=True, n_iter=2
        )
        assert "LogReg" in trainer.models

    @pytest.mark.unit
    @pytest.mark.ml
    @pytest.mark.slow
    def test_a_composite_score_is_computed(self, trainer, dataset):
        """Model selection ranks on this, so its absence would pick at random."""
        X, y = dataset
        pipeline, grid = trainer.create_logistic_regression_pipeline()
        result = trainer.train_with_grid_search(
            "LogReg", pipeline, grid, X, y, X, y, use_randomized=True, n_iter=2
        )
        assert isinstance(result["composite_score"], float)


class TestModelSelection:
    @staticmethod
    def _record(recall, f1, roc_auc, composite, meets):
        return {
            "val_metrics": {"recall": recall, "f1": f1, "roc_auc": roc_auc},
            "composite_score": composite,
            "meets_criteria": meets,
            "model": object(),
            "best_params": {},
        }

    @pytest.mark.unit
    @pytest.mark.ml
    def test_prefers_a_qualifying_model_over_a_higher_scoring_one(self, trainer):
        """
        The criteria exist to veto. A model with the best composite score that
        fails them must not win, or the criteria are decoration.
        """
        trainer.models = {
            "fails_criteria": self._record(0.99, 0.99, 0.99, 0.99, False),
            "qualifies": self._record(0.90, 0.85, 0.88, 0.80, True),
        }
        trainer._select_best_model()
        assert trainer.best_model_name == "qualifies"

    @pytest.mark.unit
    @pytest.mark.ml
    def test_picks_the_highest_composite_among_qualifying_models(self, trainer):
        trainer.models = {
            "lower": self._record(0.90, 0.85, 0.88, 0.70, True),
            "higher": self._record(0.91, 0.86, 0.89, 0.85, True),
        }
        trainer._select_best_model()
        assert trainer.best_model_name == "higher"

    @pytest.mark.unit
    @pytest.mark.ml
    def test_still_chooses_something_when_nothing_qualifies(self, trainer):
        """
        Returning no model at all would end training with an empty
        models/production/, which is worse than a flagged best-effort pick.
        """
        trainer.models = {
            "a": self._record(0.50, 0.50, 0.50, 0.40, False),
            "b": self._record(0.60, 0.60, 0.60, 0.55, False),
        }
        trainer._select_best_model()
        assert trainer.best_model_name in {"a", "b"}


class TestResultsSummary:
    @pytest.mark.unit
    @pytest.mark.ml
    def test_writes_a_readable_summary(self, trainer, tmp_path):
        import json

        import numpy as np

        trainer.models = {
            "LogReg": {
                "val_metrics": {"recall": 0.9, "f1": 0.85, "roc_auc": 0.88},
                "cv_score": 0.86,
                "composite_score": 0.87,
                # numpy.bool_, as EvaluationCriteria actually returns. json.dump
                # cannot serialise it, and the whole training run once crashed
                # on this line -- after the production artifacts had been
                # written, so a successful train looked like a failed one.
                "meets_criteria": np.bool_(True),
                "optimal_threshold": np.float64(0.229),
                "best_params": {"classifier__C": 1.0},
                "model": object(),
            }
        }
        trainer.best_model_name = "LogReg"

        out = tmp_path / "summary.json"
        trainer.save_results_summary(str(out))

        assert out.exists()
        payload = json.loads(out.read_text(encoding="utf-8"))
        assert payload["best_model"] == "LogReg"
        assert payload["models"]["LogReg"]["meets_criteria"] is True

    @pytest.mark.unit
    @pytest.mark.ml
    def test_a_default_path_is_used_when_none_is_given(self, trainer, tmp_path):
        """output_dir is where a real run drops its summary."""
        import numpy as np

        trainer.models = {
            "LogReg": {
                "val_metrics": {"recall": 0.9, "f1": 0.85, "roc_auc": 0.88},
                "cv_score": 0.86,
                "composite_score": 0.87,
                "meets_criteria": np.bool_(False),
                "optimal_threshold": np.float64(0.5),
                "best_params": {},
                "model": object(),
            }
        }
        trainer.best_model_name = "LogReg"
        trainer.save_results_summary()
        assert list(tmp_path.glob("training_results_*.json"))
