import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import main
from agent.schemas import AskAIResponse
from main import app

client = TestClient(app)


def test_ask_ai_endpoint_returns_google_search_ai_response(monkeypatch):
    def fake_ask_ai_answer(request):
        return AskAIResponse(
            answer="Google Search AI answer for tomato spacing.",
            suggested_actions=["Review the tomato crop guide."],
            related_crops=["Tomato"],
            safety_note="Verify fertilizer and pesticide decisions locally.",
            source="gemini_search",
            citations=["Example Source - https://example.com/tomato"],
            search_queries=["tomato spacing Nepal"],
        )

    monkeypatch.setattr(main, "get_ask_ai_answer", fake_ask_ai_answer)

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
    assert data["source"] == "gemini_search"
    assert "Google Search AI answer" in data["answer"]
    assert data["related_crops"] == ["Tomato"]
    assert data["citations"] == ["Example Source - https://example.com/tomato"]
    assert data["search_queries"] == ["tomato spacing Nepal"]


def test_ask_ai_requires_google_ai_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_CLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GCLOUD_PROJECT", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_VERTEXAI", raising=False)
    monkeypatch.delenv("GOOGLE_GENAI_USE_ENTERPRISE", raising=False)

    response = client.post(
        "/ask-ai",
        json={
            "question": "What should I do during a flood near Kathmandu?",
            "context": "disaster",
            "location": "Kathmandu, Nepal",
        },
    )

    assert response.status_code == 503
    assert "Google AI Search module" in response.json()["detail"]
