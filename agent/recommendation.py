import os
import re
import logging
from typing import List, Optional
from google import genai
from google.genai import errors
from .schemas import CropRecommendationRequest, CropRecommendationResponse, CropGuide
from .crop_guide import get_crop_guide

logger = logging.getLogger(__name__)

def convert_to_hectares(size: float, unit: str) -> float:
    """
    Converts land area into hectares for standardized agricultural calculations.
    Nepal-specific units (Ropani, Katha, Bigha) are mapped accurately.
    """
    # Conversions:
    # 1 hectare = 19.6 ropani
    # 1 hectare = 30 katha (approx, 1 bigha = 20 katha)
    # 1 hectare = 1.5 bigha
    # 1 hectare = 10,000 sq meters
    conversions = {
        "hectare": 1.0,
        "ropani": 0.0509,
        "katha": 0.0338,
        "bigha": 0.6772,
        "square_meter": 0.0001
    }
    return size * conversions.get(unit.lower(), 1.0)

def generate_rule_based_recommendation(request: CropRecommendationRequest, guide: CropGuide) -> CropRecommendationResponse:
    """
    Generates a high-quality, customized agricultural recommendation deterministically.
    Scales seed, manure, and fertilizer quantities based on land size and unit.
    """
    ha_size = convert_to_hectares(request.land_size, request.land_unit)
    
    # 1. Parse and scale seed rate
    # Extract numbers from seed_rate string (e.g. "40 to 50 kg per hectare" -> [40, 50])
    seed_numbers = [float(x) for x in re.findall(r"\d+\.?\d*", guide.seed_rate)]
    if len(seed_numbers) >= 2:
        scaled_min = seed_numbers[0] * ha_size
        scaled_max = seed_numbers[1] * ha_size
        seed_estimate = f"{scaled_min:.2f} to {scaled_max:.2f} kg (based on {request.land_size} {request.land_unit})"
    elif len(seed_numbers) == 1:
        scaled = seed_numbers[0] * ha_size
        seed_estimate = f"{scaled:.2f} kg (based on {request.land_size} {request.land_unit})"
    else:
        seed_estimate = f"{guide.seed_rate} (Reference rate. Please scale to {request.land_size} {request.land_unit})"

    # 2. Parse and scale manure/compost rate (default to 10-15 tons per hectare if not parsed)
    manure_numbers = [float(x) for x in re.findall(r"\d+\.?\d*", guide.manure_and_fertilizer)]
    # Filter for values that look like manure tonnage (typically 5 to 30 tons/ha)
    manure_tons = [x for x in manure_numbers if 5 <= x <= 40]
    if len(manure_tons) >= 2:
        manure_estimate = f"{manure_tons[0] * ha_size:.2f} to {manure_tons[1] * ha_size:.2f} tons"
    elif len(manure_tons) == 1:
        manure_estimate = f"{manure_tons[0] * ha_size:.2f} tons"
    else:
        # Default fallback scaling
        manure_estimate = f"{10 * ha_size:.2f} to {15 * ha_size:.2f} tons (Compost/FYM)"

    # 3. Determine fertilizer options and estimate based on farming type
    required_materials = ["Sprouted seeds or healthy saplings", "Organic compost or farmyard manure (FYM)"]
    fertilizer_estimate = "N/A - Organic farming method selected."
    recommended_method = request.farming_type.capitalize()
    
    if request.farming_type == "organic":
        required_materials.extend(["Vermicompost", "Neem cake", "Organic liquid fertilizer (Jholmol)"])
        fertilizer_estimate = f"Apply organic alternatives: {guide.organic_fertilizer_option}"
    elif request.farming_type == "chemical":
        required_materials.extend(["Urea", "Single Super Phosphate (SSP)", "Muriate of Potash (MOP)"])
        # Scale typical chemical doses if numbers are found in chemical option
        chem_numbers = [float(x) for x in re.findall(r"\d+\.?\d*", guide.chemical_fertilizer_option)]
        if len(chem_numbers) >= 3:
            # Assumes format: Urea (217), SSP (375), MOP (67)
            scaled_urea = chem_numbers[0] * ha_size
            scaled_ssp = chem_numbers[1] * ha_size
            scaled_mop = chem_numbers[2] * ha_size
            fertilizer_estimate = (
                f"Urea: {scaled_urea:.2f} kg, SSP: {scaled_ssp:.2f} kg, MOP: {scaled_mop:.2f} kg. "
                "Note: Exact quantity depends on soil test, climate, variety, and local ag office advice."
            )
        else:
            fertilizer_estimate = f"{guide.chemical_fertilizer_option} (Base rates. Please scale by multiplying by {ha_size:.4f} hectares)"
    else: # mixed
        required_materials.extend(["Urea", "SSP", "MOP", "Neem cake", "Jholmol"])
        fertilizer_estimate = f"Mixed method combining: {guide.chemical_fertilizer_option} (scaled) and {guide.organic_fertilizer_option}"

    # 4. Customize step-by-step plan based on experience level
    experience_prefix = ""
    if request.experience_level == "beginner":
        experience_prefix = (
            "🚨 Beginner Mode Enabled: Please follow instructions carefully. "
            "Ensure you do not plant too deep, keep basins weed-free, and monitor soil water levels daily.\n\n"
        )
    elif request.experience_level == "advanced":
        experience_prefix = "⚡ Advanced mode: Focus on high-yield optimization techniques (e.g. SRI, trellis support, or pruning).\n\n"
        
    step_by_step_plan = (
        f"{experience_prefix}"
        f"Step 1 (Land Prep): {guide.land_preparation}\n"
        f"Step 2 (Seed Selection): {guide.seed_selection}\n"
        f"Step 3 (Sowing/Planting): {guide.nursery_or_direct_sowing}. Sowing schedule: {guide.sowing_time}. Spacing: {guide.spacing}. {guide.planting_steps}\n"
        f"Step 4 (Fertilization Schedule): {guide.fertilizer_schedule_by_stage}\n"
        f"Step 5 (Weed control): {guide.weed_management}\n"
        f"Step 6 (Harvesting): {guide.harvesting_method} when {guide.harvesting_stage}.\n"
        f"Step 7 (Post-Harvest): {guide.post_harvest_handling}"
    )

    # 5. Crop warnings
    pest_warning = f"Pests: {guide.pest_management}. Diseases: {guide.disease_management}."
    
    # 6. Yield note
    yield_numbers = [float(x) for x in re.findall(r"\d+\.?\d*", guide.expected_yield)]
    if len(yield_numbers) >= 2:
        yield_note = f"Estimated yield: {yield_numbers[0] * ha_size:.2f} to {yield_numbers[1] * ha_size:.2f} tons (for {request.land_size} {request.land_unit})"
    else:
        yield_note = f"{guide.expected_yield} (scaled by {ha_size:.4f} hectares)"

    # 7. Safety note disclaimer
    safety_disclaimer = (
        f"{guide.safety_note}\n\n"
        "AGRICULTURE DISCLOSURE: Fertilizer and pesticide rates provided are guidelines. "
        "Actual quantities must be scaled according to soil testing results, local weather conditions, "
        "and guidance from your local agricultural extension service (Krishi Gyan Kendra)."
    )

    return CropRecommendationResponse(
        crop_name=guide.crop_name,
        recommended_method=recommended_method,
        step_by_step_plan=step_by_step_plan,
        required_materials=required_materials,
        seed_quantity_estimate=seed_estimate,
        manure_quantity_estimate=manure_estimate,
        fertilizer_quantity_estimate=fertilizer_estimate,
        irrigation_plan=f"Water availability is {request.water_availability}. Irrigation plan: {guide.irrigation_schedule}",
        pest_disease_warning=pest_warning,
        production_improvement_tips=f"{guide.best_production_tips}. Common mistakes to avoid: {guide.common_mistakes}",
        expected_yield_note=yield_note,
        safety_note=safety_disclaimer,
        ai_explanation="Deterministic agronomist rule engine computed this customized plan based on static guides."
    )

def get_crop_recommendation(request: CropRecommendationRequest) -> CropRecommendationResponse:
    """
    Generates customized crop advice.
    1. Loads crop guide.
    2. Runs Gemini if configured.
    3. Falls back to rule-based scaled calculations if Gemini fails/absent.
    """
    # Try to load crop guide
    guide, error = get_crop_guide(request.crop_name)
    if error or not guide:
        # Fall back to a generic crop response or raise error (handled by caller)
        raise ValueError(error.get("error", "Crop guide not found."))
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not found. Generating rule-based agricultural recommendation.")
        return generate_rule_based_recommendation(request, guide)
        
    try:
        client = genai.Client(api_key=api_key)
        
        system_instruction = (
            "You are AgriMind, a professional agricultural AI agronomist. "
            "You provide customized crop cultivation recommendations. "
            "You must respond in JSON format conforming EXACTLY to the CropRecommendationResponse schema.\n\n"
            "Safety and accuracy guidelines:\n"
            "1. NEVER claim a specific fertilizer quantity is perfect for every place. State clearly that exact fertilizer quantity "
            "depends on soil tests, climate, crop variety, and local agricultural office recommendations.\n"
            "2. Provide scaled quantities of seeds, manure, and fertilizers specifically for the user's land size and unit.\n"
            "3. Support Nepal-friendly context: explain units like Ropani, Katha, Bigha if needed.\n"
            "4. Do NOT recommend dangerous chemical misuse. Provide both organic and chemical schedules based on farming_type.\n"
            "5. Always include a safety warning for pesticide/fertilizer usage."
        )
        
        prompt = (
            f"Static Crop Guide Data:\n"
            f"{guide.model_dump_json(indent=2)}\n\n"
            f"User's Specific Farm Condition:\n"
            f"- Crop Name: {request.crop_name}\n"
            f"- Land Size: {request.land_size} {request.land_unit}\n"
            f"- Soil Type: {request.soil_type}\n"
            f"- Season: {request.season}\n"
            f"- Water Availability: {request.water_availability}\n"
            f"- Farming Type: {request.farming_type}\n"
            f"- Budget Level: {request.budget_level}\n"
            f"- Location: {request.location}\n"
            f"- Experience Level: {request.experience_level}\n\n"
            "Please synthesize this information and output a highly customized, safe, and actionable recommendation response."
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'system_instruction': system_instruction,
                'response_mime_type': 'application/json',
                'response_schema': CropRecommendationResponse,
                'temperature': 0.2,
            }
        )
        
        recommendation: CropRecommendationResponse = response.parsed
        return recommendation
        
    except errors.APIError as e:
        logger.error(f"Gemini API Error in recommendation: {e}. Falling back to rule-based recommendation.")
        return generate_rule_based_recommendation(request, guide)
    except Exception as e:
        logger.error(f"Unexpected error in recommendation brain: {e}. Falling back to rule-based recommendation.")
        return generate_rule_based_recommendation(request, guide)
