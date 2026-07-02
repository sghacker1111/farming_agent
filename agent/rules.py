from typing import List, Set
from .schemas import FarmState, AgentDecision

# Define cost for each action
ACTION_COSTS = {
    "irrigate": 10,
    "fertilize": 15,
    "pest_control": 20,
    "harvest": 5,
    "sell": 0,
    "wait": 0,
    "save_resources": 0,
}

def get_possible_actions(state: FarmState) -> Set[str]:
    """
    Returns a set of actions that are possible given the current farm state.
    Impossible actions are filtered out (e.g., lack of money, incorrect crop stage).
    """
    possible = set()
    
    # Wait and save_resources are always possible
    possible.add("wait")
    possible.add("save_resources")
    
    # If crop is already harvested, the only active action possible is to sell
    if state.harvested:
        possible.add("sell")
        return possible

    # Check cost-based actions
    if state.money >= ACTION_COSTS["irrigate"] and state.water_level < 100:
        possible.add("irrigate")
        
    if state.money >= ACTION_COSTS["fertilize"] and state.soil_health < 100:
        possible.add("fertilize")
        
    if state.money >= ACTION_COSTS["pest_control"] and state.pest_risk > 0:
        possible.add("pest_control")
        
    # Crop stage specific actions
    if state.crop_stage == "mature":
        if state.money >= ACTION_COSTS["harvest"]:
            possible.add("harvest")
        possible.add("sell")
        
    return possible


def apply_safety_rules(state: FarmState, proposed_action: str) -> str:
    """
    Validates a proposed action against safety rules.
    If the action is impossible or highly unsafe, it overrides it with a safe fallback action.
    """
    possible = get_possible_actions(state)
    
    # 1. Force the action to be one of the possible actions
    if proposed_action not in possible:
        # Fall back to a guaranteed safe/free action
        if state.crop_stage == "mature" and "sell" in possible:
            return "sell"
        return "save_resources"
        
    # 2. Safety Rule: If pest risk is extreme (e.g. > 70) and we can afford pest_control, we must prioritize it
    if state.pest_risk > 70 and "pest_control" in possible and proposed_action != "pest_control":
        # Override to pest control to save crops
        return "pest_control"
        
    # 3. Safety Rule: If water level is critically low (e.g. < 15) and we can irrigate, we must do it (unless it's rainy)
    if state.water_level < 15 and "irrigate" in possible and state.weather != "rainy" and proposed_action != "irrigate":
        return "irrigate"
        
    return proposed_action

def get_fallback_decision(state: FarmState) -> AgentDecision:
    """
    Deterministic rule-based fallback decision maker.
    Used when Gemini API is unavailable or fails.
    """
    possible = get_possible_actions(state)
    
    # Determine the action based on simple priority rules
    action = "save_resources"
    reasons = []
    risks = []
    expected_result = ""
    next_step = ""
    agent_explanation = "Rule-based safety fallback engine selected this action."
    confidence = 1.0
    
    # Add status-based risks
    if state.pest_risk > 50:
        risks.append(f"High pest risk ({state.pest_risk}%) threat to crops.")
    if state.water_level < 30:
        risks.append(f"Low soil moisture ({state.water_level}%).")
    if state.soil_health < 40:
        risks.append(f"Depleted soil nutrients ({state.soil_health}%).")
    if state.weather == "drought":
        risks.append("Drought conditions are dehydrating crops rapidly.")
    elif state.weather == "rainy":
        reasons.append("Rainy weather provides natural irrigation.")
        
    # Rule Evaluation & Decision tree
    if state.harvested:
        if "sell" in possible:
            action = "sell"
            reasons.append("Crops are harvested and stored. Selling now will secure revenue.")
            expected_result = "Crops sold, yielding cash revenue. Reset crop cycle to seed stage."
            next_step = "Plant seeds on the next day."
            confidence = 1.0
    elif state.crop_stage == "mature":
        if "sell" in possible and state.market_price == "high":
            action = "sell"
            reasons.append("Crops are mature and market price is high. Selling now yields maximum profit.")
            expected_result = "Crops sold, yielding high cash revenue. Reset crop cycle to seed stage."
            next_step = "Plant seeds on the next day."
            confidence = 0.95
        elif "harvest" in possible:
            action = "harvest"
            reasons.append("Crops are mature. Harvesting is needed to prepare for selling.")
            expected_result = "Crops harvested and stored for sale."
            next_step = "Sell the harvested crops."
            confidence = 0.90
        elif "sell" in possible:
            action = "sell"
            reasons.append("Crops are mature. Selling directly to avoid weather risks.")
            expected_result = "Crops sold. Reset crop cycle to seed stage."
            next_step = "Start the next planting cycle."
            confidence = 0.85
            
    elif state.pest_risk > 50 and "pest_control" in possible:
        action = "pest_control"
        reasons.append(f"Pest risk is high ({state.pest_risk}%). Immediate intervention is required.")
        expected_result = "Pest risk significantly reduced, preventing crop damage."
        next_step = "Monitor soil and water levels."
        confidence = 0.90
        
    elif state.water_level < 30 and "irrigate" in possible and state.weather != "rainy":
        action = "irrigate"
        reasons.append(f"Soil moisture level is critically low ({state.water_level}%).")
        expected_result = "Soil moisture restored to safe levels."
        next_step = "Monitor crop growth and pest threats."
        confidence = 0.85
        
    elif state.soil_health < 40 and "fertilize" in possible:
        action = "fertilize"
        reasons.append(f"Soil health is low ({state.soil_health}%). Crop growth may stunt.")
        expected_result = "Soil nutrient levels replenished, boosting crop vitality."
        next_step = "Monitor soil moisture levels."
        confidence = 0.80
        
    elif state.weather == "drought" and state.water_level < 60 and "irrigate" in possible:
        action = "irrigate"
        reasons.append("Drought conditions detected. Watering crops preemptively to prevent stress.")
        expected_result = "Moisture level maintained despite drought."
        next_step = "Save remaining funds for pest risks."
        confidence = 0.75
        
    elif state.soil_health < 70 and "fertilize" in possible:
        action = "fertilize"
        reasons.append("Routine soil enrichment to maintain high growth rates.")
        expected_result = "Soil health improved."
        next_step = "Check water levels."
        confidence = 0.70
        
    elif state.water_level < 60 and "irrigate" in possible and state.weather != "rainy":
        action = "irrigate"
        reasons.append("Moderate dry soil. Adding water to keep crops in optimal growth state.")
        expected_result = "Soil moisture optimal."
        next_step = "Monitor pest indicators."
        confidence = 0.70
        
    else:
        # Default choices
        if state.weather == "rainy":
            action = "wait"
            reasons.append("Rain is watering the crops. No urgent interventions needed; waiting is cost-effective.")
            expected_result = "Water level increases naturally. Soil health remains stable."
            next_step = "Re-evaluate state tomorrow."
            confidence = 0.80
        else:
            action = "save_resources"
            reasons.append("Farm parameters are stable. Conserving funds for future growth stages.")
            expected_result = "No funds spent. Current levels remain stable or decline slightly."
            next_step = "Check crop stage and pest risk tomorrow."
            confidence = 0.75
            
    # Ensure action complies with final safety/possibility checks
    final_action = apply_safety_rules(state, action)
    if final_action != action:
        # Re-align response if overridden
        action = final_action
        reasons = [f"Safety override: forced to {action} due to critical safety rules."]
        expected_result = f"Safety intervention executed: {action}."
        next_step = "Verify that farm variables have returned to safe operating bounds."
        confidence = 1.0
        agent_explanation = f"The rule-based safety engine overridden initial choice to {action} due to severe stress conditions (e.g. low water or high pests)."

    return AgentDecision(
        action=action,
        confidence_score=confidence,
        reasons=reasons,
        risks=risks if risks else ["No immediate critical risks identified."],
        expected_result=expected_result,
        next_step=next_step,
        agent_explanation=agent_explanation
    )
