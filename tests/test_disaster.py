import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_disaster_assist_flood_kathmandu():
    payload = {
        "disaster_type": "flood",
        "location": "Kathmandu, Nepal",
        "needs_medical": True,
        "current_supplies": "First aid kit and some dry beaten rice"
    }

    # Temporarily remove GEMINI_API_KEY to force rule-based fallback
    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        response = client.post("/disaster/assist", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["disaster_type"] == "flood"
        assert "Kathmandu" in data["location"]

        # Test location-based custom shelters
        assert any("Tundikhel" in s for s in data["safe_shelters"])

        # Test location-based medical centers
        assert any("Teaching Hospital" in m for m in data["medical_help_centers"])

        # Test emergency contacts
        assert any("1149" in c for c in data["emergency_contacts"])

        # Test farmer-facing supplies and route safety caution
        assert any("Water purification" in s for s in data["emergency_supplies_needed"])
        assert any("Confirm any route" in r for r in data["safe_roads"])

        # Test action steps contain medical warning due to needs_medical=True
        assert any("MEDICAL ALERT" in step for step in data["immediate_action_steps"])
        assert any("livestock" in step.lower() for step in data["immediate_action_steps"])

    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key


def test_disaster_assist_earthquake_pokhara():
    payload = {
        "disaster_type": "earthquake",
        "location": "Pokhara",
        "needs_medical": False,
        "current_supplies": ""
    }

    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        response = client.post("/disaster/assist", json=payload)
        assert response.status_code == 200
        data = response.json()

        assert data["disaster_type"] == "earthquake"
        assert any("Pokhara Stadium" in s for s in data["safe_shelters"])
        assert any("Gandaki Province Hospital" in m for m in data["medical_help_centers"])
        assert any("100" in c for c in data["emergency_contacts"])
        assert any("Confirm any route" in r for r in data["safe_roads"])

    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
