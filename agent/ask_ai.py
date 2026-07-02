import logging
import os
from contextlib import contextmanager
from typing import Any, List

from google import genai
from google.genai import errors, types

from .crop_guide import load_crop_guides
from .schemas import AskAIRequest, AskAIResponse

logger = logging.getLogger(__name__)


def _get_api_key() -> str | None:
    return os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")


def _is_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _get_cloud_project() -> str | None:
    return os.environ.get("GOOGLE_CLOUD_PROJECT") or os.environ.get("GCLOUD_PROJECT")


def _has_google_ai_credentials() -> bool:
    if _is_enabled("GOOGLE_GENAI_USE_ENTERPRISE") or _is_enabled("GOOGLE_GENAI_USE_VERTEXAI"):
        return bool(_get_cloud_project())
    return bool(_get_api_key())


def _build_client() -> genai.Client:
    if _is_enabled("GOOGLE_GENAI_USE_ENTERPRISE"):
        project = _get_cloud_project()
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "global")
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_ENTERPRISE is enabled.")
        return genai.Client(enterprise=True, project=project, location=location)

    if _is_enabled("GOOGLE_GENAI_USE_VERTEXAI"):
        project = _get_cloud_project()
        location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
        if not project:
            raise RuntimeError("GOOGLE_CLOUD_PROJECT is required when GOOGLE_GENAI_USE_VERTEXAI is enabled.")
        return genai.Client(vertexai=True, project=project, location=location)

    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY or GOOGLE_API_KEY is required for the Gemini Developer API.")

    return genai.Client(api_key=api_key)


@contextmanager
def _selected_google_ai_key():
    gemini_key = os.environ.get("GEMINI_API_KEY")
    google_key = os.environ.get("GOOGLE_API_KEY")
    selected_key = gemini_key or google_key
    original_google_key = google_key

    if gemini_key and google_key:
        # The SDK prefers GOOGLE_API_KEY when both are present. Temporarily remove
        # it so an explicit Gemini API key is not shadowed by another local value.
        os.environ.pop("GOOGLE_API_KEY", None)

    try:
        yield selected_key
    finally:
        if original_google_key is not None:
            os.environ["GOOGLE_API_KEY"] = original_google_key


def _detect_related_crops(question: str) -> List[str]:
    normalized_question = question.strip().lower()
    related = []

    for guide in load_crop_guides():
        crop_name = guide["crop_name"]
        crop_lower = crop_name.lower()
        crop_parts = [part.strip() for part in crop_lower.replace("-", " ").split("/")]
        search_terms = [crop_lower, *crop_parts]
        if any(term and term in normalized_question for term in search_terms):
            related.append(crop_name)

    return related[:5]


def _get_attr(obj: Any, *names: str) -> Any:
    for name in names:
        if isinstance(obj, dict) and name in obj:
            return obj[name]
        if hasattr(obj, name):
            return getattr(obj, name)
    return None


def _extract_grounding_metadata(response: Any) -> Any:
    candidates = _get_attr(response, "candidates")
    if not candidates:
        return None
    candidate = candidates[0]
    return _get_attr(candidate, "grounding_metadata", "groundingMetadata")


def _extract_citations(response: Any) -> List[str]:
    metadata = _extract_grounding_metadata(response)
    chunks = _get_attr(metadata, "grounding_chunks", "groundingChunks") if metadata else None
    citations = []

    for chunk in chunks or []:
        web = _get_attr(chunk, "web")
        title = _get_attr(web, "title") if web else None
        uri = _get_attr(web, "uri") if web else None
        if uri:
            label = title or uri
            citation = f"{label} - {uri}"
            if citation not in citations:
                citations.append(citation)

    return citations[:8]


def _extract_search_queries(response: Any) -> List[str]:
    metadata = _extract_grounding_metadata(response)
    queries = _get_attr(metadata, "web_search_queries", "webSearchQueries") if metadata else None
    return list(queries or [])[:8]


def _build_system_instruction() -> str:
    return (
        "You are AgriMind Ask AI, a Google Search-grounded AI assistant for farmers. "
        "Answer through the Gemini AI module with Google Search grounding. "
        "Do not say you are using local fallback knowledge. "
        "Give practical, direct answers for farming, crop production, irrigation, fertilizer, pests, harvesting, "
        "farm decisions, and emergency/disaster guidance. "
        "For fertilizer, pesticide, medical, road, or disaster advice, explain uncertainty and tell the farmer "
        "to confirm with local agriculture officers, soil tests, medical professionals, police, or official responders as appropriate. "
        "Keep answers easy to read for farmers. Use bullets when helpful."
    )


def _build_prompt(request: AskAIRequest) -> str:
    crop_names = [guide["crop_name"] for guide in load_crop_guides()]
    return (
        f"Farmer question: {request.question}\n"
        f"Selected question context: {request.context}\n"
        f"Farmer location: {request.location}\n"
        f"Crops covered by this app: {', '.join(crop_names)}\n\n"
        "Use Google Search grounding where it can improve the answer. "
        "If the question is about a crop covered by the app, include practical crop-specific advice. "
        "If the question is about a disaster or accident, prioritize immediate safety steps and official emergency contacts. "
        "End with a short 'Suggested actions' section."
    )


def _default_suggested_actions(request: AskAIRequest, related_crops: List[str]) -> List[str]:
    if request.context == "disaster":
        return [
            "Call local emergency services first if anyone is in immediate danger.",
            "Confirm road and shelter information with official responders before travel.",
            "Keep phone, water, first-aid, and dry food ready if evacuation may be needed.",
        ]

    if related_crops:
        crop_name = related_crops[0]
        return [
            f"Review the full {crop_name} guide in the Crop Farming Guide tab.",
            "Use the Customized Recommendation tab to calculate quantities for your exact land size.",
            "Confirm fertilizer and pesticide quantities with soil testing or a local agriculture office.",
        ]

    return [
        "Add crop name, land size, season, and location for a more precise answer.",
        "Use the Crop Farming Guide tab for full crop instructions.",
        "Use the Customized Recommendation tab for land-size quantity estimates.",
    ]


def get_ask_ai_answer(request: AskAIRequest) -> AskAIResponse:
    if not _has_google_ai_credentials():
        raise RuntimeError(
            "Ask AI requires Google AI Search module credentials: set GEMINI_API_KEY/GOOGLE_API_KEY, "
            "or enable GOOGLE_GENAI_USE_VERTEXAI/GOOGLE_GENAI_USE_ENTERPRISE with GOOGLE_CLOUD_PROJECT."
        )

    try:
        with _selected_google_ai_key():
            client = _build_client()
            grounding_tool = types.Tool(google_search=types.GoogleSearch())
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=_build_prompt(request),
                config=types.GenerateContentConfig(
                    system_instruction=_build_system_instruction(),
                    tools=[grounding_tool],
                    temperature=0.2,
                ),
            )

        answer_text = (response.text or "").strip()
        if not answer_text:
            raise RuntimeError("The Google AI Search module returned an empty answer.")

        related_crops = _detect_related_crops(request.question)
        return AskAIResponse(
            answer=answer_text,
            suggested_actions=_default_suggested_actions(request, related_crops),
            related_crops=related_crops,
            safety_note=(
                "This answer was generated by the Google AI Search module. Verify high-risk farming, chemical, "
                "medical, road, and disaster decisions with local experts or official responders."
            ),
            source="gemini_search",
            citations=_extract_citations(response),
            search_queries=_extract_search_queries(response),
        )
    except errors.APIError as e:
        logger.error(f"Gemini Search AI module error: {e}")
        raise RuntimeError(f"Google AI Search module failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected Ask AI module error: {e}")
        raise RuntimeError(f"Google AI Search module failed: {e}") from e
