from fastapi.testclient import TestClient

from brain.brain_core import Brain
from brain.evolution import SelfEvolution
from main import app


client = TestClient(app)


def test_root_supports_head_for_health_checks():
    response = client.head("/")
    assert response.status_code == 200


def test_brain_reports_insufficient_data_for_empty_history():
    brain = Brain()
    result = brain.think([])
    assert result is None


def test_pattern_key_stable_for_history_list():
    evo = SelfEvolution()
    history = ["TAI", "XIU", "TAI", "XIU"]
    assert evo.pattern_key(history) == "TAI|XIU|TAI|XIU"


def test_homepage_fetches_live_prediction_data():
    response = client.get("/")
    assert response.status_code == 200
    body = response.text
    assert "fetch(" in body or "/api/bot/predict" in body


def test_learning_history_endpoint_keeps_real_history_separate_from_system_log():
    response = client.get("/api/bot/learning-history")
    assert response.status_code == 200
    body = response.json()
    assert "real_history" in body
    assert "system_history" in body
    assert isinstance(body["real_history"], list)
    assert isinstance(body["system_history"], list)


def test_bot_learn_and_predict_endpoints_work():
    hist = ["TAI", "XIU", "TAI", "XIU", "TAI", "XIU"]

    learn = client.post(
        "/api/bot/learn",
        json={"history": hist, "actual": "TAI"},
    )
    assert learn.status_code == 200
    assert learn.json()["status"] == "ok"

    predict = client.post(
        "/api/bot/predict",
        json={"history": hist},
    )
    assert predict.status_code == 200
    body = predict.json()
    assert body["status"] == "ok"
    assert body["prediction"]["pred"] in {"TAI", "XIU", None}
