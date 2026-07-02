import sys
import os

# Append the project root to sys.path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "AgriMind Agent" in response.text
    assert "Ask AI" in response.text
    assert "Disaster AI" in response.text
    assert "Emergency Response & Disaster Assistant" in response.text
    assert "<form" in response.text


def test_decide_endpoint():
    payload = {
        "day": 1,
        "water_level": 40,
        "soil_health": 60,
        "money": 100,
        "crop_stage": "seed",
        "pest_risk": 10,
        "weather": "sunny",
        "market_price": "medium",
        "harvested": False
    }
    response = client.post("/agent/decide", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "action" in data
    assert "confidence_score" in data
    assert "reasons" in data
    assert "risks" in data
    assert "expected_result" in data
    assert "next_step" in data
    assert "agent_explanation" in data


def test_simulate_endpoint():
    payload = {
        "day": 2,
        "water_level": 30,
        "soil_health": 50,
        "money": 80,
        "crop_stage": "growing",
        "pest_risk": 20,
        "weather": "sunny",
        "market_price": "medium",
        "harvested": False
    }
    response = client.post("/agent/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "decision" in data
    assert "current_state" in data
    assert "simulated_next_state" in data
    
    # Check that day incremented in the simulated state
    assert data["simulated_next_state"]["day"] == 3
