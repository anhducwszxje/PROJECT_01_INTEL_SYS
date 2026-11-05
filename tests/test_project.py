import json
import math
import sqlite3

import numpy as np
import pytest

from diabetes_agent.config import ARTIFACTS, FEATURES, ROOT
from diabetes_agent.data import load_data
from diabetes_agent.evaluation import example_profile
from diabetes_agent.knowledge import KnowledgeBase
from diabetes_agent.rl import train_q, transition
from diabetes_agent.system import DiabetesSystem, MessageBus, review, safety_check, validate_profile


@pytest.fixture(scope="module")
def system():
    return DiabetesSystem()


def test_dataset_fingerprints_stay_in_one_split():
    frame = load_data()
    assert len(frame) == 24000
    assert set(frame.split) == {"train", "validation", "test"}


@pytest.mark.parametrize("field,value", [("Age", 55), ("BMI", float("nan")), ("BMI", float("inf")),
    ("HighBP", 2), ("Income", 0), ("Sex", True), ("MentHlth", 1.5)])
def test_invalid_survey_codes_are_rejected(field, value):
    assert validate_profile({**example_profile(), field: value})["status"] == "needs_input"


def test_missing_fields_are_explicit():
    result = validate_profile({"BMI": 25})
    assert "Age" in result["missing"]
    assert "BMI" not in result["missing"]


def test_mlp_reload_matches_saved_test_prediction(system):
    import pandas as pd
    frame = load_data()
    prediction = pd.read_csv(ARTIFACTS / "predictions_mlp.csv").iloc[0]
    row = frame[frame.row_id == prediction.row_id].iloc[0]
    result = system.risk.predict(row[FEATURES].to_dict(), "mlp")
    assert result["score"] == pytest.approx(prediction.score, abs=1e-6)


def test_intake_stops_inference_on_urgent_case(system):
    result = system.run("Người bệnh bất tỉnh", example_profile())
    assert result["status"] == "urgent"
    assert not any(t["receiver"] == "Risk" for t in result["trace"])


def test_low_glucose_carries_source(system):
    result = system.run("Hỏi", context={"glucose_mg_dl": 62})
    assert result["status"] == "urgent"
    assert result["safety"]["source_ids"] == ["D05"]


def test_nan_glucose_rejected():
    assert safety_check("", {"glucose_mg_dl": float("nan")})["status"] == "needs_input"


def test_medication_request_not_served(system):
    assert system.run("Tăng liều insulin cho tôi")["status"] == "out_of_scope"


def test_retrieval_handles_vietnamese_without_accents():
    assert "D06" in [d["id"] for d in KnowledgeBase().retrieve("hba1c ba thang")]


def test_unknown_query_abstains():
    assert KnowledgeBase().answer("Vệ tinh Sao Hỏa")["status"] == "insufficient_evidence"


@pytest.mark.parametrize("proposal", [
    {"kind": "medication", "status": "completed"},
    {"kind": "knowledge", "status": "completed", "evidence": []},
    {"kind": "knowledge", "status": "completed", "evidence": [{"id": "FAKE"}]},
    {"kind": "risk", "status": "completed", "score": 1.1},
    {"kind": "risk", "status": "failure"},
])
def test_council_vetoes_constructed_bad_proposal(proposal):
    assert review([proposal], {"D01"})["status"] == "rejected"


def test_message_bus_contains_specialist_failure():
    def broken(payload):
        raise ValueError("test failure")
    bus = MessageBus({"Risk": broken})
    assert bus.send("Coordinator", "Risk", "TEST", {})["status"] == "failure"
    assert bus.trace[-1]["performative"] == "FAILURE"


def test_reminder_invalid_state(system):
    assert system.reminder({"gap_days": 4})["status"] == "needs_input"


def test_q_learning_reproducible():
    a, _ = train_q(42, episodes=10)
    b, _ = train_q(42, episodes=10)
    assert np.array_equal(a, b)
    assert np.isfinite(a).all()


def test_transition_stays_in_state_space():
    rng = np.random.default_rng(1)
    for state in range(8):
        for action in range(3):
            nxt, reward, logged = transition(state, action, rng)
            assert 0 <= nxt < 8 and math.isfinite(reward)


def test_audit_round_trip_is_local(system, tmp_path):
    system.audit_path = tmp_path / "audit.sqlite3"
    result = system.run("HbA1c", task="knowledge")
    with sqlite3.connect(system.audit_path) as conn:
        restored = json.loads(conn.execute("SELECT result_json FROM runs").fetchone()[0])
    system.audit_path = None
    assert restored["run_id"] == result["run_id"]
    assert restored["trace"] == result["trace"]


def test_complete_consultation_has_review_and_trace(system):
    result = system.run("HbA1c và nhật ký", example_profile())
    assert result["status"] == "completed"
    assert result["review"]["status"] == "approved"
    assert len(result["trace"]) == 12


def test_streamlit_demo_runs_and_submits():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(ROOT / "app.py", default_timeout=120).run()
    assert not app.exception
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state["result"]["status"] == "completed"
