from brain.brain_core import Brain
from brain.evolution import SelfEvolution


def test_brain_fallback_prediction_for_empty_history():
    brain = Brain()
    result = brain.think([])
    assert result["algorithm"] == "fallback"
    assert result["prediction"] in {"TAI", "XIU"}


def test_pattern_key_stable_for_history_list():
    evo = SelfEvolution()
    history = ["TAI", "XIU", "TAI", "XIU"]
    assert evo.pattern_key(history) == "TAI|XIU|TAI|XIU"
