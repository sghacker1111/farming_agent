import os
import logging
from typing import List, Optional
from google import genai
from google.genai import errors
from .schemas import DisasterIncident, DisasterResponse

logger = logging.getLogger(__name__)

def get_rule_based_disaster_response(incident: DisasterIncident) -> DisasterResponse:
    """
    Generates a high-quality, localized emergency response plan deterministically
    as a robust fallback when Gemini is unavailable.
    """
    dt = incident.disaster_type.lower()
    loc_query = incident.location.lower().strip()

    # 1. Determine local shelters, roads, and medical centers based on location
    if "kathmandu" in loc_query or "lalitpur" in loc_query or "bhaktapur" in loc_query or "valley" in loc_query:
        safe_shelters = [
            "Tundikhel Open Ground (Centrally Located Safe Evacuation Zone)",
            "Dasarath Rangasala Stadium, Tripureshwor",
            "Tribhuvan University Ground, Kirtipur",
            "Designated Community Ward Buildings & School Grounds (e.g. Durbar High School yards)"
        ]
        medical_help_centers = [
            "Tribhuvan University Teaching Hospital (TUTH), Maharajgunj (Phone: +977-1-4412404)",
            "Bir Hospital, Mahabouddha, Kathmandu (Phone: +977-1-4221119)",
            "Patan Hospital, Lagankhel, Lalitpur (Phone: +977-1-5522266)",
            "Birendra Military Hospital (Nepal Army), Chhauni, Kathmandu",
            "Nepal Red Cross Society First-Aid Center (Hotline: 102)"
        ]

        if dt == "flood":
            safe_roads = [
                "Ring Road Corridor (wide route option; expect possible water logging near Balkhu, Gongabu, and Koteshwor)",
                "Kanti Path and Durbar Marg (elevated road options; confirm current access before travel)",
                "AVOID: Corridor roads along Bagmati, Bishnumati, and Dhobikhola rivers due to flood overflow risk."
            ]
        elif dt == "earthquake" or dt == "landslide":
            safe_roads = [
                "Ring Road (wide highway option with lower building-collapse exposure than narrow alleys)",
                "Durbar Marg & Kanti Path (wide streets that may support evacuation toward Tundikhel if open)",
                "AVOID: Narrow alleys of old town Asan, Indra Chowk, Patan, and Bhaktapur Durbar Square due to high structural hazard."
            ]
        else:
            safe_roads = [
                "Main Highway Corridors (Ring Road, Araniko Highway, Tribhuvan Highway)",
                "Follow updates from Metropolitan Traffic Police Division (Hotline: 103)"
            ]

    elif "pokhara" in loc_query or "kaski" in loc_query:
        safe_shelters = [
            "Pokhara Stadium (Rangasala) Open Ground, Nayabazar",
            "Prithvi Narayan Campus Ground, Bagar",
            "Komagane Park Lakeside (wide open lakefront safety area)",
            "Local Municipality/Ward Disaster Evacuation Zones"
        ]
        medical_help_centers = [
            "Gandaki Province Hospital (Western Regional), Ramghat (Phone: +977-61-520067)",
            "Manipal Teaching Hospital, Phulbari (Phone: +977-61-526416)",
            "Charak Memorial Hospital, Pokhara (Phone: +977-61-551111)",
            "Nearest Red Cross Ambulance Posts"
        ]

        if dt == "landslide" or dt == "earthquake":
            safe_roads = [
                "New Road & Siddhartha Highway (wide sections)",
                "AVOID: Lakeside cliff corridors and mountain passes prone to minor rockfall",
                "AVOID: Pokhara-Baglung Highway (check landslide blocks near Naudanda)"
            ]
        else:
            safe_roads = [
                "Prithvi Highway (major route option; watch for Mugling-Pokhara construction blocks and verify before travel)",
                "Main city roads (New Road, Lakeside main street)"
            ]

    else:
        # General Nepal regions
        safe_shelters = [
            "Local Government Community Centers, School Yards, and Ward Offices",
            "Open fields away from power lines, tall trees, or steep slopes",
            "Red Cross temporary shelter camps"
        ]
        medical_help_centers = [
            "Nearest District Hospital, Primary Health Care Center (PHCC)",
            "Local Health Post or Nepal Red Cross Society emergency response unit",
            "Nepal Police/Army makeshift medical tents"
        ]
        safe_roads = [
            "National Highways (Mahendra Highway, Prithvi Highway) - verify with police before travel",
            "AVOID: Secondary mountain roads and river crossings without structural checks",
            "AVOID: Underpasses, bridges, or steep cliff lanes"
        ]

    # 2. Determine Disaster Specific instructions
    if dt == "flood":
        immediate_action_steps = [
            "Evacuate immediately to higher ground or upper floors of a reinforced concrete building.",
            "Do not attempt to walk, swim, or drive through moving water. Turn around, don't drown!",
            "Switch off main electricity breakers and close gas valves immediately to prevent fires.",
            "Drink only boiled, bottled, or chemical-purified water to prevent severe waterborne infections.",
            "Keep emergency contact numbers handy and signal for help using a flashlight or mobile light.",
            "If it is safe and quick, move livestock, seed, fertilizer, and tools away from riverbanks; never risk human life for property."
        ]
        emergency_supplies_needed = [
            "Water purification tablets (Piyush, Aquatabs)",
            "Bottled drinking water and dry foods (beaten rice/Chiura, noodles, biscuits)",
            "First-aid kit (antiseptic, clean bandages, rehydration salts/Jeevandal)",
            "Flashlight or solar lantern with extra charge/batteries",
            "Waterproof tarpaulin sheet or plastic covers for emergency shelter",
            "Dry clothes wrapped in plastic bags"
        ]
        emergency_contacts = [
            "National Emergency Operation Center (NEOC): 1149",
            "Nepal Police Emergency Line: 100",
            "Armed Police Force Emergency: 1114",
            "Red Cross Ambulance dispatch: 102",
            "Local Municipality/Ward Helpdesk"
        ]
        summary = (
            f"FLOOD WARNING: Localized flooding reported in/near {incident.location}. "
            "Rivers may be overflowing. Prioritize immediate evacuation to elevated safe structures. "
            "Do not consume uncooked food or raw tap water."
        )

    elif dt == "earthquake":
        immediate_action_steps = [
            "If inside, DROP, COVER, and HOLD ON under a heavy desk or bed. Stay away from glass.",
            "If outside, run to a clear open area away from buildings, brick walls, trees, and power lines.",
            "If in a vehicle, park in a clear area and stay inside. Do not stop on or under bridges.",
            "Once shaking stops, evacuate using staircases (NEVER elevators) and watch for falling plaster/tiles.",
            "Expect aftershocks. Check yourself and neighbors for injuries; apply basic bleeding control."
        ]
        emergency_supplies_needed = [
            "First-aid kit (gauze pads, antiseptic, medical tape)",
            "Sturdy shoes and thick gloves to navigate rubble",
            "Whistle or horn to signal your location to rescue teams",
            "Flashlight or headlamp with spare batteries",
            "Emergency water bottle (at least 3 liters per person)",
            "Warm clothing or thermal space blanket",
            "Essential regular personal prescriptions"
        ]
        emergency_contacts = [
            "National Disaster Risk Reduction & Management Authority (NDRRMA): 1149",
            "Nepal Police Control: 100",
            "Red Cross Ambulance Service: 102",
            "Military Rescue Coordinator: 1114 / 100"
        ]
        summary = (
            f"EARTHQUAKE ALERT: Active seismic tremors felt in/near {incident.location}. "
            "Structures may be compromised. Stay outdoors in designated open zones until aftershocks subside. "
            "Do not re-enter damaged buildings."
        )

    elif dt == "cyclone":
        immediate_action_steps = [
            "Stay indoors. Move to the center of your house (e.g. hallway, closet, bathroom) away from windows.",
            "Close and secure all doors, windows, and exterior shutters. Tape glass to prevent shattering.",
            "Bring inside loose outdoor objects (tools, trash bins, potted plants) that could act as high-speed missiles.",
            "Keep mobile phones fully charged and monitor meteorological broadcasts for weather updates.",
            "Secure farm tools, animal sheds, irrigation pumps, and loose materials only if it can be done before winds intensify.",
            "Avoid driving or walking during the peak storm wind hours due to falling trees and flying debris."
        ]
        emergency_supplies_needed = [
            "Heavy-duty waterproof tape and plastic sheets",
            "Flashlight, candles, matches, and fully charged power banks",
            "First-aid box with emergency painkillers and bandages",
            "Non-perishable canned food and manual can opener",
            "Battery-powered portable radio",
            "Emergency rope and basic tools (hammer, pliers)"
        ]
        emergency_contacts = [
            "Meteorological Forecasting Division Office: +977-1-4473382",
            "NEOC Disaster Hotline: 1149",
            "Nepal Police Command: 100",
            "Local Fire Brigade: 101"
        ]
        summary = (
            f"CYCLONIC/HIGH-WIND STORM WARNING: Extreme gale winds affecting {incident.location}. "
            "Stay indoors in structurally secure rooms. Avoid travel until wind speeds drop below safety thresholds."
        )

    elif dt == "road_accident":
        immediate_action_steps = [
            "Ensure the safety of the accident site first. Turn on hazard warnings or place caution reflectors.",
            "Call Traffic Police (103) and Ambulance (102) immediately with precise location details.",
            "Do not move victims with suspected head, neck, or spine injuries unless vehicle is on fire/sinking.",
            "Apply direct pressure to bleeding wounds using a clean cloth or sterile dressing.",
            "Keep the victim warm, calm, and conscious while waiting for professional medical teams."
        ]
        emergency_supplies_needed = [
            "Sterile gauze rolls and adhesive bandages",
            "Antiseptic wipes or hydrogen peroxide solution",
            "Disposable nitrile/latex medical gloves",
            "Scissors, medical tape, and safety pins",
            "Emergency thermal space blanket",
            "Clean bottle of water for rinsing wounds"
        ]
        emergency_contacts = [
            "Metropolitan Traffic Police Division: 103",
            "Nepal Police Control: 100",
            "Nepal Red Cross Ambulance Dispatch: 102",
            "Nearest Trauma Center / Teaching Hospital Emergency"
        ]
        summary = (
            f"ROAD ACCIDENT EMERGENCY: Accident reported in/near {incident.location}. "
            "Secure the site to prevent secondary collisions. Alert emergency responders immediately."
        )

    else: # landslide
        immediate_action_steps = [
            "Evacuate immediately if you notice warning rumblings, land cracks, or tilting trees.",
            "Run to the nearest high, stable ridge ground. Do not run downhill in the path of the slide.",
            "Avoid river beds and creek pathways downstream, as landslide debris often causes sudden flash floods.",
            "If escape is impossible, curl into a tight ball, cover your head and neck with your arms, and hold on.",
            "Once safe, alert neighbors and check for trapped persons without entering unstable mud slides.",
            "Move people and livestock away from cracked slopes, irrigation channels, and riverbeds when evacuation is still safe."
        ]
        emergency_supplies_needed = [
            "Sturdy hiking boots or boots with good traction",
            "Flashlight or headlamp and loud safety whistle",
            "First-aid medical pack (antiseptic, bandages, pain relief)",
            "Waterproof raincoat or windbreaker",
            "Emergency high-strength ropes",
            "Bottled drinking water and high-energy snacks"
        ]
        emergency_contacts = [
            "National Emergency Operation Center (NEOC): 1149",
            "Nepal Police Search & Rescue: 100",
            "Armed Police Force Rescue Command: 1114",
            "Local District Administration Office (DAO)"
        ]
        summary = (
            f"LANDSLIDE HAZARD: Active mud/rock slide occurring in/near mountain slopes of {incident.location}. "
            "Slopes are highly unstable, especially during rainfall. Evacuate immediately to safe, stable ridges."
        )

    # 3. Handle specific flags in fallback
    if incident.needs_medical:
        immediate_action_steps.insert(0, "🚨 EMERGENCY MEDICAL ALERT: Contact 102/100 immediately. Medical assistance is requested.")
        medical_help_centers.insert(0, "🆘 URGENT: Deploy first-aid and emergency ambulance transport immediately to the location.")

    if incident.current_supplies:
        summary += f" Note: Local team reports currently having: {incident.current_supplies}."

    safe_roads.append(
        "Confirm any route with Nepal Police/Traffic Police or local responders before travel; disaster road conditions can change quickly."
    )

    return DisasterResponse(
        disaster_type=incident.disaster_type,
        location=incident.location,
        safe_shelters=safe_shelters,
        safe_roads=safe_roads,
        medical_help_centers=medical_help_centers,
        emergency_supplies_needed=emergency_supplies_needed,
        immediate_action_steps=immediate_action_steps,
        emergency_contacts=emergency_contacts,
        assessment_summary=summary
    )


def get_disaster_recommendation(incident: DisasterIncident) -> DisasterResponse:
    """
    Coordinates disaster analysis. If a GEMINI_API_KEY is found, queries Gemini
    for custom emergency instructions and localized shelters/hospitals.
    Otherwise, returns rule-based fallback response.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.info("GEMINI_API_KEY not configured. Generating rule-based emergency response.")
        return get_rule_based_disaster_response(incident)

    try:
        client = genai.Client(api_key=api_key)

        system_instruction = (
            "You are Disaster AI, an Emergency Response & Disaster Assistant built for the Agents for Good track. "
            "Your role is to analyze natural disasters (floods, earthquakes, cyclones, landslides) and accidents, "
            "and generate structured, highly localized emergency response instructions for farmers, families, and communities. "
            "Provide realistic safe shelters (e.g. Tundikhel, stadiums, campus grounds for Nepal locations), "
            "road safety details, hospitals with phone numbers, supply checklists, and step-by-step action guides. "
            "Do not claim roads are live-verified or guaranteed safe. Explain that route guidance must be confirmed "
            "with police, traffic police, local government, or official responders because disaster conditions change quickly. "
            "Ensure safety numbers like 100, 102, 103, 1149 are clearly provided when applicable."
        )

        prompt = (
            f"Disaster Incident Details:\n"
            f"- Incident Type: {incident.disaster_type}\n"
            f"- Location: {incident.location}\n"
            f"- Immediate Medical Assistance Requested: {incident.needs_medical}\n"
            f"- Current Local Supplies: {incident.current_supplies or 'None reported'}\n\n"
            "Please analyze this emergency situation and return a detailed, structured disaster response report."
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config={
                'system_instruction': system_instruction,
                'response_mime_type': 'application/json',
                'response_schema': DisasterResponse,
                'temperature': 0.2,
            }
        )

        res: DisasterResponse = response.parsed
        return res

    except errors.APIError as e:
        logger.error(f"Gemini API Error in disaster assistant: {e}. Falling back to rules.")
        return get_rule_based_disaster_response(incident)
    except Exception as e:
        logger.error(f"Unexpected error in disaster assistant: {e}. Falling back to rules.")
        return get_rule_based_disaster_response(incident)
