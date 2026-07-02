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
