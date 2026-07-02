import logging
import os
from typing import Any, Dict, List

from google import genai
from google.genai import errors

from .crop_guide import load_crop_guides
from .disaster import get_rule_based_disaster_response
from .schemas import AskAIRequest, AskAIResponse, DisasterIncident

logger = logging.getLogger(__name__)

TOPIC_FIELDS = {
    "seed": ["seed_selection", "seed_rate", "nursery_or_direct_sowing", "sowing_time", "planting_steps"],
    "spacing": ["spacing", "planting_steps"],
    "plant": ["land_preparation", "nursery_or_direct_sowing", "sowing_time", "spacing", "planting_steps"],
    "irrigation": ["irrigation_schedule"],
    "water": ["irrigation_schedule"],
    "fertilizer": ["manure_and_fertilizer", "organic_fertilizer_option", "chemical_fertilizer_option", "fertilizer_schedule_by_stage"],
    "compost": ["manure_and_fertilizer", "organic_fertilizer_option"],
    "pest": ["pest_management"],
    "disease": ["disease_management"],
    "weed": ["weed_management"],
    "harvest": ["harvesting_stage", "harvesting_method", "post_harvest_handling"],
    "yield": ["expected_yield", "best_production_tips"],
    "storage": ["post_harvest_handling"],
    "soil": ["suitable_soil", "land_preparation"],
    "climate": ["suitable_climate", "sowing_time"],
}

FIELD_LABELS = {
    "suitable_climate": "Climate",
    "suitable_soil": "Soil",
    "land_preparation": "Land preparation",
    "seed_selection": "Seed selection",
    "seed_rate": "Seed rate",
    "nursery_or_direct_sowing": "Sowing method",
    "sowing_time": "Sowing time",
    "spacing": "Spacing",
    "planting_steps": "Planting steps",
    "irrigation_schedule": "Irrigation",
    "manure_and_fertilizer": "Manure and fertilizer",
    "organic_fertilizer_option": "Organic option",
    "chemical_fertilizer_option": "Chemical option",
    "fertilizer_schedule_by_stage": "Fertilizer schedule",
    "weed_management": "Weed management",
    "pest_management": "Pest management",
    "disease_management": "Disease management",
    "best_production_tips": "Production tips",
    "harvesting_stage": "Harvesting stage",
    "harvesting_method": "Harvesting method",
    "post_harvest_handling": "Post-harvest",
    "expected_yield": "Expected yield",
    "common_mistakes": "Common mistakes",
    "safety_note": "Safety",
}


def _normalize(text: str) -> str:
    return text.strip().lower()


def _detect_related_guides(question: str) -> List[Dict[str, Any]]:
    guides = load_crop_guides()
    normalized_question = _normalize(question)
    matches = []

    for guide in guides:
        crop_name = guide["crop_name"]
        crop_lower = crop_name.lower()
        crop_parts = [part.strip() for part in crop_lower.replace("-", " ").split("/")]
        search_terms = [crop_lower, *crop_parts]

        if any(term and term in normalized_question for term in search_terms):
            matches.append(guide)

    return matches


def _detect_relevant_fields(question: str) -> List[str]:
    normalized_question = _normalize(question)
    fields: List[str] = []

    for keyword, mapped_fields in TOPIC_FIELDS.items():
        if keyword in normalized_question:
            for field in mapped_fields:
                if field not in fields:
                    fields.append(field)

    if fields:
        return fields

    return [
        "suitable_soil",
        "sowing_time",
        "spacing",
        "irrigation_schedule",
        "manure_and_fertilizer",
        "pest_management",
        "harvesting_stage",
        "best_production_tips",
    ]


def _detect_disaster_type(question: str) -> str | None:
    normalized_question = _normalize(question)
    disaster_keywords = {
        "flood": ["flood", "flooding", "river overflow", "inundation"],
        "earthquake": ["earthquake", "tremor", "aftershock"],
        "cyclone": ["cyclone", "storm", "high wind", "windstorm"],
        "road_accident": ["road accident", "accident", "collision", "crash"],
        "landslide": ["landslide", "rockfall", "slope", "mudslide"],
    }

    for disaster_type, keywords in disaster_keywords.items():
        if any(keyword in normalized_question for keyword in keywords):
            return disaster_type
    return None


def _build_crop_fallback_response(request: AskAIRequest, guides: List[Dict[str, Any]]) -> AskAIResponse:
    fields = _detect_relevant_fields(request.question)
    guide = guides[0]
    crop_name = guide["crop_name"]
    lines = [f"Here is a direct answer for {crop_name}:"]

    for field in fields:
        value = guide.get(field)
        if value:
            lines.append(f"- {FIELD_LABELS.get(field, field.replace('_', ' ').title())}: {value}")

    if guide.get("common_mistakes"):
        lines.append(f"- Avoid this mistake: {guide['common_mistakes']}")

    suggested_actions = [
        f"Open the Crop Farming Guide tab and review the full {crop_name} guide.",
        "Use the Customized Recommendation tab to scale seed, manure, fertilizer, and yield to your exact land size.",
        "Confirm fertilizer and pesticide quantities with a soil test or local agriculture office before applying.",
    ]

    return AskAIResponse(
        answer="\n".join(lines),
        suggested_actions=suggested_actions,
        related_crops=[guide["crop_name"] for guide in guides[:5]],
        safety_note=(
            "This is farming guidance based on the local crop guide database. Exact fertilizer, pesticide, "
            "and irrigation decisions should be adjusted for soil test, weather, variety, and local expert advice."
        ),
        source="local_fallback",
    )


def _build_disaster_fallback_response(request: AskAIRequest, disaster_type: str) -> AskAIResponse:
    incident = DisasterIncident(
        disaster_type=disaster_type,
        location=request.location or "Nepal",
        needs_medical=any(word in _normalize(request.question) for word in ["medical", "injury", "injured", "hospital", "bleeding"]),
        current_supplies="",
    )
    response = get_rule_based_disaster_response(incident)
    answer = "\n".join(
        [
            response.assessment_summary,
            "",
            "Shelter options:",
            *[f"- {item}" for item in response.safe_shelters[:3]],
            "",
            "Road guidance:",
            *[f"- {item}" for item in response.safe_roads[:3]],
            "",
            "Medical help:",
            *[f"- {item}" for item in response.medical_help_centers[:3]],
            "",
            "Emergency supplies:",
            *[f"- {item}" for item in response.emergency_supplies_needed[:4]],
        ]
    )

    return AskAIResponse(
        answer=answer,
        suggested_actions=response.immediate_action_steps[:5],
        related_crops=[],
        safety_note=(
            "For immediate danger, call local emergency services first. Confirm any route with official responders "
            "because disaster conditions can change quickly."
        ),
        source="local_fallback",
    )


def generate_local_answer(request: AskAIRequest) -> AskAIResponse:
    disaster_type = _detect_disaster_type(request.question)
    if request.context == "disaster" or disaster_type:
        return _build_disaster_fallback_response(request, disaster_type or "flood")

    related_guides = _detect_related_guides(request.question)
    if related_guides:
        return _build_crop_fallback_response(request, related_guides)

    crops = [guide["crop_name"] for guide in load_crop_guides()]
    sample_crops = ", ".join(crops[:8])
    return AskAIResponse(
        answer=(
            "I can answer farming questions about crop selection, sowing, spacing, irrigation, fertilizer, "
            "pest and disease control, harvesting, post-harvest handling, simulation decisions, and disaster response. "
            f"Try asking about a specific crop such as {sample_crops}. For example: 'How much seed for tomato?', "
            "'When should I irrigate rice?', or 'What should I do during a flood in Kathmandu?'"
        ),
        suggested_actions=[
            "Mention the crop name and the problem you want to solve.",
            "Add your land size and unit if you need quantity estimates.",
            "Use the Disaster AI tab for structured emergency response reports.",
        ],
        related_crops=crops[:8],
        safety_note="Ask AI gives quick guidance. Use local agriculture and emergency authorities for high-risk decisions.",
        source="local_fallback",
    )


def get_ask_ai_answer(request: AskAIRequest) -> AskAIResponse:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Generating local Ask AI response.")
        return generate_local_answer(request)

    try:
        guides = load_crop_guides()
        crop_names = [guide["crop_name"] for guide in guides]
        matched_guides = _detect_related_guides(request.question)
        matched_context = "\n\n".join(
            [
                f"Crop: {guide['crop_name']}\n"
                f"Soil: {guide.get('suitable_soil', '')}\n"
                f"Sowing: {guide.get('sowing_time', '')}\n"
                f"Spacing: {guide.get('spacing', '')}\n"
                f"Irrigation: {guide.get('irrigation_schedule', '')}\n"
                f"Fertilizer: {guide.get('manure_and_fertilizer', '')}\n"
                f"Pest: {guide.get('pest_management', '')}\n"
                f"Disease: {guide.get('disease_management', '')}\n"
                f"Harvest: {guide.get('harvesting_stage', '')}"
                for guide in matched_guides[:3]
            ]
        )

        client = genai.Client(api_key=api_key)
        system_instruction = (
            "You are AgriMind Ask AI, a direct chat assistant for farmers. "
            "Answer instantly, clearly, and practically. Use short paragraphs or bullets. "
            "Support crop production, farm simulation decisions, Nepal-friendly land units, and disaster response. "
            "Do not claim fertilizer, pesticide, road, medical, or disaster advice is guaranteed perfect. "
            "For fertilizers and pesticides, remind users that soil tests, crop variety, weather, and local agriculture "
            "office guidance matter. For disasters, tell users to call emergency services first and confirm route safety "
            "with official responders."
        )
        prompt = (
            f"Question: {request.question}\n"
            f"Context selected by user: {request.context}\n"
            f"Location: {request.location}\n"
            f"Supported crops: {', '.join(crop_names)}\n\n"
            f"Matched local crop guide excerpts:\n{matched_context or 'No specific crop match.'}\n\n"
            "Return a structured AskAIResponse JSON object."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": system_instruction,
                "response_mime_type": "application/json",
                "response_schema": AskAIResponse,
                "temperature": 0.2,
            },
        )
        answer: AskAIResponse = response.parsed
        answer.source = "gemini"
        return answer
    except errors.APIError as e:
        logger.error(f"Gemini API Error in Ask AI: {e}. Falling back to local response.")
        return generate_local_answer(request)
    except Exception as e:
        logger.error(f"Unexpected Ask AI error: {e}. Falling back to local response.")
        return generate_local_answer(request)
