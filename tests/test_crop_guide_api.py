import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_get_crops_list():
    response = client.get("/crops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 21
    
    # Check that some expected crops are present
    crop_names = [c["crop_name"] for c in data]
    assert "Rice / Paddy" in crop_names
    assert "Tomato" in crop_names
    assert "Apple" in crop_names


def test_get_crop_guide_success():
    # Exact match
    response = client.get("/crops/Tomato")
    assert response.status_code == 200
    data = response.json()
    assert data["crop_name"] == "Tomato"
    assert data["category"] == "Vegetable"
    assert "seed_rate" in data

    # Case-insensitive match and partial match
    response_lower = client.get("/crops/rice")
    assert response_lower.status_code == 200
    data_lower = response_lower.json()
    assert data_lower["crop_name"] == "Rice / Paddy"
    assert data_lower["category"] == "Cereal"


def test_get_crop_guide_not_found():
    response = client.get("/crops/unknowncrop")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data["detail"]
    assert "available_crops" in data["detail"]


def test_crops_recommend_fallback():
    # This test verifies that the recommendation engine runs successfully
    # even when the Gemini API key is absent/not validated.
    payload = {
        "crop_name": "Rice / Paddy",
        "land_size": 2.5,
        "land_unit": "ropani",
        "soil_type": "Clayey Loam",
        "season": "Monsoon / Rainy",
        "water_availability": "high",
        "farming_type": "organic",
        "budget_level": "medium",
        "location": "Kathmandu Valley",
        "experience_level": "beginner"
    }
    
    # Temporarily remove GEMINI_API_KEY from environment to force rule-based fallback
    old_key = os.environ.get("GEMINI_API_KEY")
    if "GEMINI_API_KEY" in os.environ:
        del os.environ["GEMINI_API_KEY"]
        
    try:
        response = client.post("/crops/recommend", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["crop_name"] == "Rice / Paddy"
        assert "organic" in data["recommended_method"].lower()
        # Check that the seed and manure estimates are scaled correctly
        assert "kg" in data["seed_quantity_estimate"]
        assert "tons" in data["manure_quantity_estimate"]
        # In beginner mode, check for warning prefix
        assert "Beginner Mode" in data["step_by_step_plan"]
    finally:
        # Restore GEMINI_API_KEY
        if old_key is not None:
            os.environ["GEMINI_API_KEY"] = old_key
