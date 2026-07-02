import random
from .schemas import FarmState, AgentDecision

def simulate_step(state: FarmState, decision: AgentDecision) -> FarmState:
    """
    Simulates the state of the farm for the next day, given the current state and selected action.
    """
    # Create a copy of the state
    next_state = state.model_copy()
    
    # 1. Increment day
    next_state.day += 1
    
    # 2. Apply action-specific costs and effects
    action = decision.action
    
    if action == "irrigate":
        next_state.money -= 10
        next_state.water_level = min(100, next_state.water_level + 40)
    elif action == "fertilize":
        next_state.money -= 15
        next_state.soil_health = min(100, next_state.soil_health + 30)
    elif action == "pest_control":
        next_state.money -= 20
        next_state.pest_risk = max(0, next_state.pest_risk - 50)
    elif action == "harvest":
        next_state.money -= 5
        next_state.harvested = True
    elif action == "sell":
        # Gain money based on market price
        revenue = 0
        if state.market_price == "low":
            revenue = 100
        elif state.market_price == "medium":
            revenue = 200
        elif state.market_price == "high":
            revenue = 300
        
        next_state.money += revenue
        next_state.crop_stage = "seed"
        next_state.harvested = False
    elif action == "wait":
        pass
    elif action == "save_resources":
        pass
        
    # Ensure money doesn't go below 0 (safety fallback)
    next_state.money = max(0, next_state.money)
    
    # 3. Apply environmental degradation & natural processes (if crop is still in ground and not harvested)
    if not next_state.harvested and next_state.crop_stage != "seed":
        # Water level decreases based on weather
        water_loss = 10
        if state.weather == "drought":
            water_loss = 25
        elif state.weather == "sunny":
            water_loss = 15
        elif state.weather == "cloudy":
            water_loss = 8
        elif state.weather == "rainy":
            water_loss = -20 # rain replenishes soil water
            
        next_state.water_level = max(0, min(100, next_state.water_level - water_loss))
        
        # Soil health degrades slowly
        next_state.soil_health = max(0, next_state.soil_health - 5)
        
        # Pest risk grows naturally
        pest_growth = 5
        if state.weather == "sunny":
            pest_growth = 10
        elif state.weather == "cloudy":
            pest_growth = 7
        next_state.pest_risk = min(100, next_state.pest_risk + pest_growth)
        
    elif next_state.crop_stage == "seed":
        # Seeds need some water but don't deplete resources as quickly
        water_loss = 5
        if state.weather == "drought":
            water_loss = 15
        elif state.weather == "sunny":
            water_loss = 10
        elif state.weather == "rainy":
            water_loss = -15
        next_state.water_level = max(0, min(100, next_state.water_level - water_loss))
        next_state.soil_health = max(0, next_state.soil_health - 2)
        next_state.pest_risk = min(100, next_state.pest_risk + 2)
        
    # 4. Crop stage progression (only if water and soil health are decent)
    if not next_state.harvested:
        if next_state.crop_stage == "seed":
            if next_state.water_level >= 30 and next_state.soil_health >= 30:
                next_state.crop_stage = "growing"
        elif next_state.crop_stage == "growing":
            if next_state.water_level >= 40 and next_state.soil_health >= 40 and next_state.pest_risk < 50:
                next_state.crop_stage = "flowering"
        elif next_state.crop_stage == "flowering":
            if next_state.water_level >= 40 and next_state.soil_health >= 40 and next_state.pest_risk < 40:
                next_state.crop_stage = "mature"
                
    # 5. Cycle Weather and Market Price semi-randomly or deterministically to simulate a real farm experience
    # Let's cycle weather deterministically to keep tests stable and make simulation predictable:
    weathers = ["sunny", "cloudy", "rainy", "drought"]
    current_weather_idx = weathers.index(state.weather)
    # Simple transition: 20% chance to change weather
    # Let's keep weather and market price transition predictable for simple simulation
    # Weather changes sequentially: sunny -> cloudy -> rainy -> sunny -> drought -> sunny
    if state.day % 4 == 0:
        next_state.weather = "cloudy"
    elif state.day % 4 == 1:
        next_state.weather = "rainy"
    elif state.day % 4 == 2:
        next_state.weather = "sunny"
    else:
        next_state.weather = "drought"
        
    # Cycle market price
    market_prices = ["low", "medium", "high"]
    if state.day % 3 == 0:
        next_state.market_price = "low"
    elif state.day % 3 == 1:
        next_state.market_price = "medium"
    else:
        next_state.market_price = "high"
        
    return next_state
