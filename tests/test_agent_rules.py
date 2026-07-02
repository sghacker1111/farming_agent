import pytest
from agent.schemas import FarmState, AgentDecision
from agent.rules import get_possible_actions, apply_safety_rules, get_fallback_decision

def test_possible_actions_filtering():
    # If money is 0, we can't irrigate, fertilize, pest_control, or harvest. Only wait, save_resources, or sell (cost 0)
    state = FarmState(
        day=5,
        water_level=20,
        soil_health=50,
        money=0,
        crop_stage="growing",
        pest_risk=10,
        weather="sunny",
        market_price="medium",
        harvested=False
    )
    possible = get_possible_actions(state)
    assert "irrigate" not in possible
    assert "fertilize" not in possible
    assert "pest_control" not in possible
    assert "harvest" not in possible
    assert "wait" in possible
    assert "save_resources" in possible

    # If crop is mature and money is enough, harvest and sell should be possible
    state_mature = FarmState(
        day=10,
        water_level=60,
        soil_health=60,
        money=100,
        crop_stage="mature",
        pest_risk=10,
        weather="sunny",
        market_price="high",
        harvested=False
    )
    possible_mature = get_possible_actions(state_mature)
    assert "harvest" in possible_mature
    assert "sell" in possible_mature

    # If crop is already harvested, cannot harvest again
    state_harvested = FarmState(
        day=11,
        water_level=60,
        soil_health=60,
        money=100,
        crop_stage="mature",
        pest_risk=10,
        weather="sunny",
        market_price="high",
        harvested=True
    )
    possible_harvested = get_possible_actions(state_harvested)
    assert "harvest" not in possible_harvested
    assert "sell" in possible_harvested


def test_safety_rules_override():
    # High pest risk (> 70) and enough money should force pest_control
    state_pests = FarmState(
        day=6,
        water_level=50,
        soil_health=50,
        money=100,
        crop_stage="growing",
        pest_risk=80,
        weather="sunny",
        market_price="medium",
        harvested=False
    )
    # Even if proposed action is "wait", safety rule overrides to "pest_control"
    action = apply_safety_rules(state_pests, "wait")
    assert action == "pest_control"

    # Critically low water (< 15) and enough money should force irrigate (weather sunny)
    state_dry = FarmState(
        day=7,
        water_level=10,
        soil_health=60,
        money=50,
        crop_stage="growing",
        pest_risk=10,
        weather="sunny",
        market_price="medium",
        harvested=False
    )
    action = apply_safety_rules(state_dry, "wait")
    assert action == "irrigate"


def test_fallback_decision():
    # When Gemini is absent, fallback logic generates a correct AgentDecision structure
    state = FarmState(
        day=12,
        water_level=20,
        soil_health=70,
        money=100,
        crop_stage="growing",
        pest_risk=10,
        weather="sunny",
        market_price="medium",
        harvested=False
    )
    decision = get_fallback_decision(state)
    assert isinstance(decision, AgentDecision)
    # Low water level (20) should trigger irrigate decision in fallback
    assert decision.action == "irrigate"
    assert decision.confidence_score > 0
    assert len(decision.reasons) > 0
