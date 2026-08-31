"""
NEXUS-NER | Tests — Model & Inference
(These tests require the model to be trained first)
"""

import sys
import pytest
from pathlib import Path

AI_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AI_ROOT))

MODEL_PATH = AI_ROOT / "models" / "risk_model.pkl"
requires_model = pytest.mark.skipif(
    not MODEL_PATH.exists(),
    reason="Model not trained yet — run python training/train.py"
)


# ---------------------------------------------------------------------------
# Tests — predictor (inference engine)
# ---------------------------------------------------------------------------

class TestPredictor:

    VALID_INPUT = {
        "rainfall_1h": 88.0, "rainfall_3h": 205.0,
        "traffic_level": 0.72, "road_condition": 0.32,
        "slope": 18.4, "river_distance": 0.9,
        "historical_incidents": 7,
    }

    LOW_RISK_INPUT = {
        "rainfall_1h": 3.0, "rainfall_3h": 8.0,
        "traffic_level": 0.10, "road_condition": 0.92,
        "slope": 2.0, "river_distance": 12.0,
        "historical_incidents": 0,
    }

    @requires_model
    def test_predict_returns_probability(self):
        from inference.predictor import predict
        result = predict(self.VALID_INPUT)
        assert "probability" in result
        assert "risk_level" in result

    @requires_model
    def test_probability_in_range(self):
        from inference.predictor import predict
        result = predict(self.VALID_INPUT)
        assert 0.0 <= result["probability"] <= 1.0

    @requires_model
    def test_risk_level_valid(self):
        from inference.predictor import predict
        result = predict(self.VALID_INPUT)
        assert result["risk_level"] in ("SAFE", "MODERATE", "HIGH", "CRITICAL")

    @requires_model
    def test_low_risk_input_gives_lower_probability(self):
        from inference.predictor import predict
        low  = predict(self.LOW_RISK_INPUT)
        high = predict(self.VALID_INPUT)
        # High-risk input should produce higher probability
        assert high["probability"] > low["probability"]

    @requires_model
    def test_predict_batch(self):
        from inference.predictor import predict_batch
        records = [self.VALID_INPUT, self.LOW_RISK_INPUT]
        results = predict_batch(records)
        assert len(results) == 2
        for r in results:
            assert 0.0 <= r["probability"] <= 1.0

    def test_missing_required_field_raises(self):
        from inference.predictor import predict
        incomplete = {"rainfall_1h": 88.0, "rainfall_3h": 205.0}  # missing others
        with pytest.raises(ValueError, match="Missing required fields"):
            predict(incomplete)

    def test_out_of_range_value_raises(self):
        from inference.predictor import predict
        bad = {**self.VALID_INPUT, "traffic_level": 5.0}  # must be [0, 1]
        with pytest.raises(ValueError, match="outside valid range"):
            predict(bad)

    def test_defaults_fill_optional_fields(self):
        from inference.predictor import predict
        # Should not raise — optional fields have defaults
        minimal = {
            "rainfall_1h": 10.0, "rainfall_3h": 25.0,
            "traffic_level": 0.30, "road_condition": 0.75,
            "slope": 6.0, "river_distance": 5.0,
            "historical_incidents": 1,
        }
        result = predict(minimal)
        assert "probability" in result

    @requires_model
    def test_model_loads_only_once(self):
        from inference import predictor
        predictor._model = None  # reset
        from inference.predictor import predict
        predict(self.VALID_INPUT)   # loads model
        m1 = predictor._model
        predict(self.VALID_INPUT)   # should reuse
        m2 = predictor._model
        assert m1 is m2             # same object in memory


# ---------------------------------------------------------------------------
# Tests — model file checks
# ---------------------------------------------------------------------------

class TestModelFiles:

    @requires_model
    def test_model_file_exists(self):
        assert MODEL_PATH.exists()

    @requires_model
    def test_model_can_be_loaded(self):
        import joblib
        model = joblib.load(MODEL_PATH)
        assert model is not None

    @requires_model
    def test_model_has_predict_proba(self):
        import joblib
        model = joblib.load(MODEL_PATH)
        assert hasattr(model, "predict_proba")

    def test_metadata_file_exists(self):
        meta_path = AI_ROOT / "models" / "model_metadata.json"
        assert meta_path.exists(), "model_metadata.json not found"

    @requires_model
    def test_metadata_has_disclaimer(self):
        import json
        meta_path = AI_ROOT / "models" / "model_metadata.json"
        with open(meta_path) as f:
            meta = json.load(f)
        assert "disclaimer" in meta
        assert "SYNTHETIC" in meta["disclaimer"].upper() or "synthetic" in meta["disclaimer"]
