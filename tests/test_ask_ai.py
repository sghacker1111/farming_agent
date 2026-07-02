import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_ask_ai_crop_question_fallback():
    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        response = client.post(
            "/ask-ai",
            json={
                "question": "How much seed and spacing is needed for tomato?",
                "context": "crop",
                "location": "Kavre, Nepal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "local_fallback"
        assert "Tomato" in data["answer"]
        assert "Seed rate" in data["answer"]
        assert "Spacing" in data["answer"]
        assert "Tomato" in data["related_crops"]
        assert len(data["suggested_actions"]) > 0
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key


def test_ask_ai_disaster_question_fallback():
    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]

    try:
        response = client.post(
            "/ask-ai",
            json={
                "question": "What should I do during a flood near Kathmandu?",
                "context": "disaster",
                "location": "Kathmandu, Nepal",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "local_fallback"
        assert "FLOOD WARNING" in data["answer"]
        assert "Shelter options" in data["answer"]
        assert "official responders" in data["safety_note"]
        assert len(data["suggested_actions"]) > 0
    finally:
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
