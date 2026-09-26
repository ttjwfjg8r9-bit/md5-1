from fastapi.testclient import TestClient

from brain.brain_core import Brain
from brain.evolution import SelfEvolution
from main import app


client = TestClient(app)


def test_root_supports_head_for_health_checks():
    response = client.head("/")
    assert response.status_code == 200


def test_brain_fallback_prediction_for_empty_history():
    brain = Brain()
    result = brain.think([])
    assert result["algorithm"] == "fallback"
    assert result["prediction"] in {"TAI", "XIU"}


def test_pattern_key_stable_for_history_list():
    evo = SelfEvolution()
    history = ["TAI", "XIU", "TAI", "XIU"]
    assert evo.pattern_key(history) == "TAI|XIU|TAI|XIU"
