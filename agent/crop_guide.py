import os
import json
import logging
from typing import List, Dict, Any, Optional, Tuple
from .schemas import CropGuide

logger = logging.getLogger(__name__)

# Path to the crop guides JSON database
DATA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(DATA_DIR, "data", "crop_guides.json")

def load_crop_guides() -> List[Dict[str, Any]]:
    """
    Loads and returns raw crop guides from the JSON database.
    """
    if not os.path.exists(DB_PATH):
        logger.error(f"Crop guides database not found at {DB_PATH}. Exiting with empty list.")
        return []
        
    try:
        with open(DB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading crop guides database: {e}")
        return []

def get_crop_guide(crop_name: str) -> Tuple[Optional[CropGuide], Optional[Dict[str, Any]]]:
    """
    Finds a crop guide matching crop_name case-insensitively.
    Also supports partial/keyword matching (e.g., 'paddy' matching 'Rice / Paddy').
    
    Returns:
        (CropGuide, None) if found.
        (None, error_details) if not found, where error_details contains a list of available crops.
    """
    raw_guides = load_crop_guides()
    if not raw_guides:
        return None, {"error": "Crop database is empty or unavailable.", "available_crops": []}
        
    normalized_input = crop_name.strip().lower()
    
    # 1. Look for exact case-insensitive match
    for guide in raw_guides:
        name = guide["crop_name"].lower()
        if name == normalized_input:
            return CropGuide(**guide), None
            
    # 2. Look for split match (e.g. 'Rice / Paddy' -> matches 'rice' or 'paddy')
    for guide in raw_guides:
        name = guide["crop_name"].lower()
        parts = [p.strip() for p in name.split("/")]
        if normalized_input in parts or any(normalized_input == p for p in parts):
            return CropGuide(**guide), None
            
    # 3. Look for substring match
    for guide in raw_guides:
        name = guide["crop_name"].lower()
        if normalized_input in name:
            return CropGuide(**guide), None
            
    # 4. If not found, prepare a helpful list of available crop names
    available_crops = [g["crop_name"] for g in raw_guides]
    
    # Simple fuzzy scoring to suggest close matches
    suggestions = []
    for crop in available_crops:
        # Check if characters or words overlap
        crop_lower = crop.lower()
        if any(word in crop_lower for word in normalized_input.split()):
            suggestions.append(crop)
            
    error_response = {
        "error": f"Crop '{crop_name}' not found in database.",
        "suggestions": suggestions if suggestions else None,
        "available_crops": available_crops
    }
    return None, error_response
