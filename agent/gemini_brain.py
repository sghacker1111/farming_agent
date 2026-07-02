import os
import logging
from typing import Optional
from google import genai
from google.genai import errors
from .schemas import FarmState, AgentDecision
from .rules import get_fallback_decision, ACTION_COSTS

logger = logging.getLogger(__name__)

def get_gemini_decision(state: FarmState) -> Optional[AgentDecision]:
    """
    Calls the Google Gemini API using the official google-genai SDK to make an agentic farming decision.
    Returns None if api key is missing or if the API call fails, so the engine can fall back.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY environment variable not set. Falling back to rule-based decision.")
        return None
        
    try:
        # Initialize client with the API key explicitly
        client = genai.Client(api_key=api_key)
        
        # Prepare system instruction and prompt context
        system_instruction = (
            "You are AgriMind, a professional AI agronomist and farming decision-making agent. "
            "Your goal is to maximize the farm's profit and maintain crop health. "
            "You must select exactly one best action from the allowed action set: "
            "['irrigate', 'fertilize', 'pest_control', 'wait', 'harvest', 'sell', 'save_resources'].\n\n"
            "Safety and financial rules you MUST follow:\n"
            "1. NEVER spend more money than available. Budget constraints (costs):\n"
            f"   - irrigate: ${ACTION_COSTS['irrigate']}\n"
            f"   - fertilize: ${ACTION_COSTS['fertilize']}\n"
            f"   - pest_control: ${ACTION_COSTS['pest_control']}\n"
            f"   - harvest: ${ACTION_COSTS['harvest']}\n"
            f"   - sell, wait, save_resources: $0\n"
            "2. If crop stage is NOT 'mature', you CANNOT 'harvest' or 'sell' (unless harvested is True, then you can 'sell').\n"
            "3. If the crop is already harvested (harvested=True), you can only 'sell' or wait/save_resources. Do not water/fertilize.\n"
            "4. Prioritize safety: If water level is critically low or pest risk is high, prioritize saving the crop."
        )
        
        prompt = (
            f"Current Farm State:\n"
            f"- Day: {state.day}\n"
            f"- Water Level: {state.water_level}%\n"
            f"- Soil Health: {state.soil_health}%\n"
            f"- Money/Budget: ${state.money}\n"
            f"- Crop Stage: {state.crop_stage}\n"
            f"- Pest Risk: {state.pest_risk}%\n"
            f"- Weather: {state.weather}\n"
            f"- Market Price: {state.market_price}\n"
            f"- Crop Harvested: {state.harvested}\n\n"
            "Please analyze this state carefully, check your safety and cost constraints, and recommend the best action."
        )
        
        # Call Gemini models (we use gemini-2.5-flash as the default fast & capable model)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'system_instruction': system_instruction,
                'response_mime_type': 'application/json',
                'response_schema': AgentDecision,
                'temperature': 0.1,  # Keep reasoning focused and deterministic
            }
        )
        
        # The official SDK parses the response automatically into the response_schema Pydantic model
        decision: AgentDecision = response.parsed
        return decision
        
    except errors.APIError as e:
        logger.error(f"Gemini API Error: {e}. Falling back to rule-based decision.")
        return None
    except Exception as e:
        logger.error(f"Unexpected error in Gemini brain: {e}. Falling back to rule-based decision.")
        return None
