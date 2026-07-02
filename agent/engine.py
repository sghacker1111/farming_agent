from .schemas import FarmState, AgentDecision
from .gemini_brain import get_gemini_decision
from .rules import get_fallback_decision, apply_safety_rules

def make_decision(state: FarmState) -> AgentDecision:
    """
    Coordinating engine that receives farm state data and returns one best action.
    It:
    1. Tries Gemini-powered decision making using Gemini API if configured.
    2. Runs a deterministic safety filter to override unsafe/impossible actions.
    3. Falls back gracefully to a robust rule-based model if Gemini is offline/missing.
    """
    # 1. Attempt Gemini recommendation
    decision = get_gemini_decision(state)
    
    if decision is not None:
        # Check against deterministic safety & capability constraints
        original_action = decision.action
        safe_action = apply_safety_rules(state, original_action)
        
        if safe_action != original_action:
            # Safety override
            decision.action = safe_action
            decision.confidence_score = 1.0
            decision.reasons.insert(0, f"Safety override: Overruled AI recommended '{original_action}' with '{safe_action}'.")
            decision.risks.append(f"AI proposed impossible or unsafe action: '{original_action}'.")
            decision.expected_result = f"Safety override action '{safe_action}' executed successfully."
            decision.agent_explanation = (
                f"The AI recommended '{original_action}', which violated farm safety or budget limits. "
                f"The deterministic safety controller corrected this to '{safe_action}' to preserve farm continuity."
            )
            
        return decision
        
    # 2. Fallback to rule-based logic
    return get_fallback_decision(state)
