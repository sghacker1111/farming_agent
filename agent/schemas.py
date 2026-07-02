from typing import List, Literal
from pydantic import BaseModel, Field

# Input schema representing the state of the farm
class FarmState(BaseModel):
    day: int = Field(..., description="Current day of the simulation", ge=0)
    water_level: int = Field(..., description="Soil water level percentage (0 to 100)", ge=0, le=100)
    soil_health: int = Field(..., description="Soil health/nutrient level percentage (0 to 100)", ge=0, le=100)
    money: int = Field(..., description="Available cash/budget", ge=0)
    crop_stage: Literal["seed", "growing", "flowering", "mature"] = Field(..., description="Growth stage of the crop")
    pest_risk: int = Field(..., description="Pest threat risk percentage (0 to 100)", ge=0, le=100)
    weather: Literal["sunny", "cloudy", "rainy", "drought"] = Field(..., description="Current weather condition")
    market_price: Literal["low", "medium", "high"] = Field(..., description="Current market price status")
    harvested: bool = Field(False, description="Whether the mature crop has been harvested")


# Output schema for agent's recommended decision
class AgentDecision(BaseModel):
    action: Literal["irrigate", "fertilize", "pest_control", "wait", "harvest", "sell", "save_resources"] = Field(
        ..., description="The recommended action for the farm"
    )
    confidence_score: float = Field(..., description="Confidence score from 0.0 to 1.0", ge=0.0, le=1.0)
    reasons: List[str] = Field(..., description="Key reasons backing up the recommended action")
    risks: List[str] = Field(..., description="Potential risks associated with this action or current situation")
    expected_result: str = Field(..., description="The expected outcome of performing this action")
    next_step: str = Field(..., description="The recommended action or strategy for the next day")
    agent_explanation: str = Field(..., description="Deep synthesis explanation of the agent's logic")

# Response schema for the simulate endpoint
class SimulationResult(BaseModel):
    decision: AgentDecision = Field(..., description="The decision made by the agent for the current state")
    current_state: FarmState = Field(..., description="The initial state before taking action")
    simulated_next_state: FarmState = Field(..., description="The predicted state after taking the recommended action")


# New crop-related schemas
class CropGuide(BaseModel):
    crop_name: str = Field(..., description="Name of the crop")
    category: str = Field(..., description="Crop category (e.g. Cereal, Vegetable, Fruit)")
    suitable_climate: str = Field(..., description="Optimal climate conditions")
    suitable_soil: str = Field(..., description="Optimal soil conditions")
    land_preparation: str = Field(..., description="Steps for land preparation")
    seed_selection: str = Field(..., description="Guide to seed selection")
    seed_rate: str = Field(..., description="Estimated seed rate per unit land")
    nursery_or_direct_sowing: str = Field(..., description="Sowing method (nursery or direct)")
    sowing_time: str = Field(..., description="Best time for sowing")
    spacing: str = Field(..., description="Recommended plant spacing")
    planting_steps: str = Field(..., description="Step-by-step planting instructions")
    irrigation_schedule: str = Field(..., description="Irrigation recommendations")
    manure_and_fertilizer: str = Field(..., description="General fertilizer/manure instructions")
    organic_fertilizer_option: str = Field(..., description="Organic fertilization options")
    chemical_fertilizer_option: str = Field(..., description="Chemical fertilization options")
    fertilizer_schedule_by_stage: str = Field(..., description="Fertilizing timeline by growth stage")
    weed_management: str = Field(..., description="Weed control guidelines")
    pest_management: str = Field(..., description="Pest control guidelines")
    disease_management: str = Field(..., description="Disease control guidelines")
    best_production_tips: str = Field(..., description="Best practices for higher yield")
    harvesting_stage: str = Field(..., description="Indicators for crop readiness")
    harvesting_method: str = Field(..., description="Harvesting guidelines")
    post_harvest_handling: str = Field(..., description="Post-harvest management")
    expected_yield: str = Field(..., description="Expected crop yield ranges")
    common_mistakes: str = Field(..., description="Common farming mistakes to avoid")
    safety_note: str = Field(..., description="Safety precautions during farming operations")


class FarmCondition(BaseModel):
    crop_name: str = Field(..., description="Name of the crop to grow")
    land_size: float = Field(..., description="Size of the land", gt=0.0)
    land_unit: Literal["ropani", "katha", "bigha", "hectare", "square_meter"] = Field(..., description="Land measurement unit")
    soil_type: str = Field(..., description="Type of soil (e.g. Clay, Loam, Sandy)")
    season: str = Field(..., description="Current/target farming season")
    water_availability: Literal["low", "medium", "high"] = Field(..., description="Water availability level")
    farming_type: Literal["organic", "chemical", "mixed"] = Field(..., description="Farming methodology type")
    budget_level: Literal["low", "medium", "high"] = Field(..., description="Available budget level")
    location: str = Field(..., description="Geographical location")
    experience_level: Literal["beginner", "intermediate", "advanced"] = Field(..., description="Farmer experience level")


class CropRecommendationRequest(FarmCondition):
    pass


class CropRecommendationResponse(BaseModel):
    crop_name: str = Field(..., description="Name of the crop")
    recommended_method: str = Field(..., description="Recommended farming method (organic, chemical, mixed)")
    step_by_step_plan: str = Field(..., description="Tailored step-by-step farming plan")
    required_materials: List[str] = Field(..., description="Required materials for the plan")
    seed_quantity_estimate: str = Field(..., description="Scaled seed quantity estimate")
    manure_quantity_estimate: str = Field(..., description="Scaled manure/compost quantity estimate")
    fertilizer_quantity_estimate: str = Field(..., description="Scaled chemical fertilizer estimate (if applicable)")
    irrigation_plan: str = Field(..., description="Tailored irrigation guidelines")
    pest_disease_warning: str = Field(..., description="Disease/pest warnings based on season/experience")
    production_improvement_tips: str = Field(..., description="Yield improvement advice")
    expected_yield_note: str = Field(..., description="Tailored expected yield description")
    safety_note: str = Field(..., description="Critical agronomist safety warning")
    ai_explanation: str = Field(..., description="Synthesis explanation of how this custom advice was generated")


class AskAIRequest(BaseModel):
    question: str = Field(..., description="Farmer's direct question for the Ask AI assistant", min_length=3)
    context: Literal["general", "crop", "simulator", "disaster"] = Field(
        "general", description="Optional topic context selected in the web app"
    )
    location: str = Field("Nepal", description="Optional location for localized farming or disaster guidance")


class AskAIResponse(BaseModel):
    answer: str = Field(..., description="Direct answer to the farmer's question")
    suggested_actions: List[str] = Field(..., description="Short follow-up actions the farmer can take")
    related_crops: List[str] = Field(..., description="Crop names found or relevant to the answer")
    safety_note: str = Field(..., description="Important safety or uncertainty note")
    source: Literal["gemini", "local_fallback"] = Field(..., description="Whether the answer came from Gemini or local fallback logic")


class DisasterIncident(BaseModel):
    disaster_type: Literal["flood", "earthquake", "cyclone", "road_accident", "landslide"] = Field(
        ..., description="The type of emergency or natural disaster for Disaster AI to assess"
    )
    location: str = Field(..., description="The name of the location or area affected")
    needs_medical: bool = Field(False, description="Whether immediate medical help is needed")
    current_supplies: str = Field("", description="Supplies currently available locally")


class DisasterResponse(BaseModel):
    disaster_type: str = Field(..., description="The type of disaster")
    location: str = Field(..., description="The area analyzed")
    safe_shelters: List[str] = Field(..., description="Likely evacuation spots and shelter options nearby")
    safe_roads: List[str] = Field(..., description="Road access guidance and route safety cautions")
    medical_help_centers: List[str] = Field(..., description="Hospitals, clinics, and first-aid response spots")
    emergency_supplies_needed: List[str] = Field(..., description="Vital emergency items recommended to obtain")
    immediate_action_steps: List[str] = Field(..., description="Urgent step-by-step safety measures to take right now")
    emergency_contacts: List[str] = Field(..., description="Critical emergency phone numbers and hotlines")
    assessment_summary: str = Field(..., description="Summary explanation and advice from the AI assistant")
