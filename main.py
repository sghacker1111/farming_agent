import os
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from agent.schemas import (
    FarmState, AgentDecision, SimulationResult,
    CropGuide, CropRecommendationRequest, CropRecommendationResponse
)
from agent.engine import make_decision
from agent.simulation import simulate_step
from agent.crop_guide import load_crop_guides, get_crop_guide
from agent.recommendation import get_crop_recommendation
from fastapi import HTTPException, status

app = FastAPI(
    title="AgriMind Agent",
    description="Smart Farming AI Decision Agent",
    version="1.0.0"
)

# Mount static and template directories
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    Renders the interactive web dashboard for AgriMind Agent.
    """
    # Provide some default values for the web form
    default_state = {
        "day": 1,
        "water_level": 40,
        "soil_health": 55,
        "money": 100,
        "crop_stage": "seed",
        "pest_risk": 15,
        "weather": "sunny",
        "market_price": "medium",
        "harvested": False
    }
    api_key_configured = bool(os.environ.get("GEMINI_API_KEY"))
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "default_state": default_state,
            "api_key_configured": api_key_configured
        }
    )

@app.get("/health")
async def health_check():
    """
    Standard health check endpoint.
    """
    return {"status": "ok"}

@app.post("/agent/decide", response_model=AgentDecision)
async def decide_endpoint(state: FarmState):
    """
    Receives the current farm state and returns the optimal action recommendation.
    """
    decision = make_decision(state)
    return decision

@app.post("/agent/simulate", response_model=SimulationResult)
async def simulate_endpoint(state: FarmState):
    """
    Receives the current farm state, determines the action, and simulates the next day's state.
    """
    decision = make_decision(state)
    next_state = simulate_step(state, decision)
    return SimulationResult(
        decision=decision,
        current_state=state,
        simulated_next_state=next_state
    )


@app.get("/crops")
async def get_crops():
    """
    Returns a list of all available crops and their categories.
    """
    guides = load_crop_guides()
    return [{"crop_name": g["crop_name"], "category": g["category"]} for g in guides]


@app.get("/crops/{crop_name}", response_model=CropGuide)
async def get_crop_guide_endpoint(crop_name: str):
    """
    Returns the complete farming guide for a specific crop.
    """
    guide, error = get_crop_guide(crop_name)
    if error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=error
        )
    return guide


@app.post("/crops/recommend", response_model=CropRecommendationResponse)
async def recommend_crop_endpoint(request: CropRecommendationRequest):
    """
    Accepts crop name and farm conditions, returning a customized farming plan.
    """
    try:
        recommendation = get_crop_recommendation(request)
        return recommendation
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


if __name__ == "__main__":
    # Get port from environment or default to 8080 for Cloud Run
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
