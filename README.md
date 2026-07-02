# AgriMind Agent - Smart Farming Instruction Web App

AgriMind Agent is a full-stack farming instruction and decision-support web app for farmers. It combines a FastAPI backend, a responsive Jinja2 web dashboard, deterministic farming rules, Google Gemini AI support, a local crop guide database, and Disaster AI emergency planning.

The app was built as a Google 5-Day AI Agents capstone-style project and focuses on practical farming support for Nepal-friendly land units, crop production guidance, simulation, recommendations, and emergency response.

## Main Purpose

Farmers often need quick answers for questions like:

- What should I do next on my farm today?
- Is the crop ready to harvest or should I wait?
- How much seed, manure, compost, or fertilizer is needed for my land size?
- What is the correct spacing, sowing time, irrigation plan, pest control plan, and harvest method for a crop?
- Can I ask a direct question and get an instant AI answer?
- During a flood, earthquake, cyclone, landslide, or accident, where are possible shelters, roads, medical help, and emergency supplies?

AgriMind Agent provides one dashboard with direct Ask AI chat, farming simulation, crop instruction, customized production recommendations, and Disaster AI emergency response assistance.

## Web App Features

### 1. Home Dashboard

The home tab introduces the full farming assistant and shows the main modules:

- Ask AI
- Farming Simulator
- Crop Farming Guide
- Customized Recommendation
- Disaster AI

It also includes a supported crop list and important safety disclaimers for fertilizer and pesticide usage.

### 2. Ask AI Direct Chat

Ask AI is a direct chat feature for instant farmer questions. It is designed for quick answers when the farmer does not want to open the full crop guide or recommendation form.

Inputs:

- Question type: general, crop, simulator, or disaster
- Location
- Farmer question

Example questions:

- How much seed and spacing is needed for tomato?
- When should I irrigate rice in the monsoon season?
- What should I do if pest risk is high in my maize field?
- What should I do during a flood near Kathmandu?

Outputs:

- Direct answer
- Suggested actions
- Related crops
- Safety note
- Answer source: Google Search AI module
- Google Search queries when returned by the API
- Grounding source citations when returned by the API

Ask AI uses Gemini with Google Search grounding. It requires either a Gemini API key (`GEMINI_API_KEY` or `GOOGLE_API_KEY`) or Google Cloud Vertex AI service-account authentication (`GOOGLE_GENAI_USE_VERTEXAI=true` with `GOOGLE_CLOUD_PROJECT`). If no Google AI credentials are configured, the Ask AI endpoint returns an error instead of generating a local fallback answer.

### 3. Farming Simulator

The simulator lets a farmer enter the current farm condition and ask the agent for the best next action.

Inputs:

- Day count
- Water level
- Soil health
- Available money/capital
- Crop stage: seed, growing, flowering, mature
- Pest risk
- Weather: sunny, cloudy, rainy, drought
- Market price: low, medium, high
- Harvested status

Outputs:

- Recommended action
- Confidence score
- Key reasons
- Risks
- Expected result
- Next step
- Agronomist-style explanation

Supported actions:

- irrigate
- fertilize
- pest_control
- wait
- harvest
- sell
- save_resources

The simulator also includes a "Run Simulation Step" workflow that applies the decision and predicts the next farm state.

### 4. Crop Farming Guide

The Crop Farming Guide provides detailed instructions for 21 crops. Each crop guide includes:

- Suitable climate
- Suitable soil
- Land preparation
- Seed selection
- Seed rate
- Nursery or direct sowing method
- Sowing time
- Spacing
- Planting steps
- Irrigation schedule
- Manure and fertilizer guidance
- Organic fertilizer option
- Chemical fertilizer option
- Fertilizer schedule by stage
- Weed management
- Pest management
- Disease management
- Best production tips
- Harvesting stage
- Harvesting method
- Post-harvest handling
- Expected yield
- Common mistakes
- Safety note

The guide search supports exact matching, case-insensitive matching, and partial crop names such as "rice" or "paddy" for "Rice / Paddy".

### 5. Customized Crop Recommendation

The recommendation module creates a tailored farming plan for the farmer's exact land size and situation.

Inputs:

- Crop name
- Land size
- Land unit
- Soil type
- Season
- Water availability
- Farming type: organic, chemical, mixed
- Budget level
- Location
- Experience level: beginner, intermediate, advanced

Supported land units:

- ropani
- katha
- bigha
- hectare
- square_meter

Outputs:

- Recommended method
- Step-by-step plan
- Required materials
- Seed quantity estimate
- Manure quantity estimate
- Fertilizer quantity estimate
- Irrigation plan
- Pest and disease warnings
- Production improvement tips
- Expected yield note
- Safety note
- AI/rule explanation

If `GEMINI_API_KEY` is configured, the app asks Gemini for a structured recommendation. If Gemini is unavailable or no API key is configured, the app uses its local rule-based agronomist engine.

### 6. Disaster AI - Emergency Response and Disaster Assistant

Disaster AI helps farmers and communities during emergencies.

Supported emergencies:

- flood
- earthquake
- cyclone
- road_accident
- landslide

Inputs:

- Disaster type
- Current location
- Whether immediate medical help is needed
- Current supplies available locally

Outputs:

- Emergency status summary
- Shelter options
- Road and access guidance
- Medical and first-aid centers
- Emergency supplies needed
- Immediate action steps
- Emergency contacts and hotlines

Important safety behavior:

- The system gives route guidance, not guaranteed live road verification.
- Farmers are told to confirm any route with police, traffic police, local government, or official responders.
- During emergencies, the app reminds users to call local emergency services first.
- The fallback engine includes Nepal emergency numbers such as 100, 102, 103, 1114, and 1149 where relevant.

## Supported Crops

### Cereals

- Rice / Paddy
- Maize
- Wheat

### Vegetables

- Potato
- Tomato
- Cauliflower
- Cabbage
- Onion
- Cucumber
- Pumpkin

### Spices

- Garlic
- Ginger
- Turmeric
- Chili

### Legumes and Oilseeds

- Mustard
- Lentil
- Soybean

### Fruits

- Banana
- Mango
- Orange
- Apple

## AI and Rule-Based Architecture

AgriMind Agent uses a hybrid architecture:

1. Pydantic schemas define safe structured inputs and outputs.
2. Deterministic rules check budget, crop stage, pest risk, water level, and impossible actions.
3. Gemini can generate structured decisions and recommendations when an API key is available.
4. Safety rules override unsafe or impossible AI suggestions.
5. Local fallback engines keep the app usable even without internet or an API key.

This makes the app useful for demos, local testing, and real farmer-facing workflows where AI may not always be available.

## Backend Modules

```text
agent/
  schemas.py          Pydantic request and response models
  rules.py            Farm action rules, cost checks, and safety overrides
  gemini_brain.py     Gemini decision engine for simulator actions
  engine.py           Decision coordinator combining Gemini and safety rules
  simulation.py       Farm state transition simulator
  ask_ai.py           Direct Ask AI chat engine with Gemini and Google Search grounding
  crop_guide.py       Crop guide loading, lookup, and search
  recommendation.py   Crop recommendation engine with Gemini and fallback logic
  disaster.py         Disaster AI emergency response engine
```

## Frontend Structure

```text
templates/index.html  Main Jinja2 dashboard with tabs and JavaScript fetch logic
static/style.css      Dark emerald dashboard styling and responsive layouts
data/crop_guides.json Local crop guide database for 21 crops
```

The frontend is a server-rendered dashboard with vanilla JavaScript. It calls the FastAPI endpoints directly with `fetch`.

## Project Structure

```text
agrimind-agent/
  agent/
    __init__.py
    schemas.py
    rules.py
    gemini_brain.py
    ask_ai.py
    crop_guide.py
    recommendation.py
    disaster.py
    engine.py
    simulation.py
  data/
    crop_guides.json
  static/
    style.css
  templates/
    index.html
  tests/
    __init__.py
    test_agent_rules.py
    test_ask_ai.py
    test_api.py
    test_crop_guide_api.py
    test_disaster.py
  .env.example
  .gitignore
  Dockerfile
  main.py
  requirements.txt
  README.md
```

## Tech Stack

- Python
- FastAPI
- Uvicorn
- Pydantic
- Jinja2
- Vanilla JavaScript
- CSS
- Google GenAI SDK (`google-genai`)
- Pytest
- Docker

## Local Setup

### Prerequisites

- Python 3.12 or newer
- Git
- Optional: Google Gemini API key

### 1. Clone the repository

```bash
git clone https://github.com/sghacker1111/farming_agent.git
cd farming_agent
```

If the repository contains the app inside `agrimind-agent`, enter that folder:

```bash
cd agrimind-agent
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file:

```bash
cp .env.example .env
```

Example `.env`:

```env
# Local developer API key option
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud / Vertex AI option
GOOGLE_GENAI_USE_VERTEXAI=false
GOOGLE_CLOUD_PROJECT=your_google_cloud_project_id
GOOGLE_CLOUD_LOCATION=us-central1
GEMINI_MODEL=gemini-2.5-flash

PORT=8080
```

If Google AI credentials are missing, the simulator, crop recommendation, crop guide, and Disaster AI modules still work using deterministic fallback engines. The Ask AI direct chat requires `GEMINI_API_KEY`, `GOOGLE_API_KEY`, or Vertex AI service-account authentication because it uses the Google AI Search module.

## Run the Web App

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open:

```text
http://localhost:8080
```

## Run Tests

```bash
python -m pytest -q
```

The test suite covers:

- Health endpoint
- Home page rendering
- Ask AI direct answer endpoint
- Agent decision endpoint
- Simulation endpoint
- Crop list endpoint
- Crop guide lookup
- Crop recommendation fallback
- Disaster AI fallback responses
- Safety rule behavior

## API Reference

### Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok"
}
```

### Ask AI Direct Chat

```http
POST /ask-ai
```

Example request:

```json
{
  "question": "How much seed and spacing is needed for tomato?",
  "context": "crop",
  "location": "Kavre, Nepal"
}
```

Response includes:

- answer
- suggested_actions
- related_crops
- safety_note
- source
- citations
- search_queries

### Agent Decision

```http
POST /agent/decide
```

Example request:

```json
{
  "day": 1,
  "water_level": 40,
  "soil_health": 60,
  "money": 100,
  "crop_stage": "seed",
  "pest_risk": 10,
  "weather": "sunny",
  "market_price": "medium",
  "harvested": false
}
```

### Farm Simulation

```http
POST /agent/simulate
```

This endpoint makes a decision and returns:

- decision
- current_state
- simulated_next_state

### Crop List

```http
GET /crops
```

Returns every crop name and category.

### Crop Guide

```http
GET /crops/{crop_name}
```

Examples:

```text
GET /crops/Tomato
GET /crops/rice
GET /crops/paddy
```

### Customized Crop Recommendation

```http
POST /crops/recommend
```

Example request:

```json
{
  "crop_name": "Rice / Paddy",
  "land_size": 2.5,
  "land_unit": "ropani",
  "soil_type": "Clayey Loam",
  "season": "Monsoon / Rainy",
  "water_availability": "high",
  "farming_type": "organic",
  "budget_level": "medium",
  "location": "Kavre, Nepal",
  "experience_level": "beginner"
}
```

### Disaster AI Emergency Response

```http
POST /disaster/assist
```

Example request:

```json
{
  "disaster_type": "flood",
  "location": "Kathmandu, Nepal",
  "needs_medical": true,
  "current_supplies": "First aid kit and dry food"
}
```

Response includes:

- disaster_type
- location
- safe_shelters
- safe_roads
- medical_help_centers
- emergency_supplies_needed
- immediate_action_steps
- emergency_contacts
- assessment_summary

## Curl Examples

### Ask AI

```bash
curl -X POST "http://localhost:8080/ask-ai" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How much seed and spacing is needed for tomato?",
    "context": "crop",
    "location": "Kavre, Nepal"
  }'
```

### Crop recommendation

```bash
curl -X POST "http://localhost:8080/crops/recommend" \
  -H "Content-Type: application/json" \
  -d '{
    "crop_name": "Rice / Paddy",
    "land_size": 2.5,
    "land_unit": "ropani",
    "soil_type": "Clayey Loam",
    "season": "Monsoon / Rainy",
    "water_availability": "high",
    "farming_type": "organic",
    "budget_level": "medium",
    "location": "Kavre, Nepal",
    "experience_level": "beginner"
  }'
```

### Disaster AI

```bash
curl -X POST "http://localhost:8080/disaster/assist" \
  -H "Content-Type: application/json" \
  -d '{
    "disaster_type": "flood",
    "location": "Kathmandu, Nepal",
    "needs_medical": true,
    "current_supplies": "First aid kit and dry food"
  }'
```

## Docker

Build:

```bash
docker build -t agrimind-agent .
```

Run:

```bash
docker run -p 8080:8080 --env-file .env agrimind-agent
```

## Deploy to Google Cloud Run

```bash
gcloud config set project YOUR_PROJECT_ID

gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com

gcloud run deploy agrimind-agent \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GOOGLE_GENAI_USE_VERTEXAI=true,GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID,GOOGLE_CLOUD_LOCATION=us-central1,GEMINI_MODEL=gemini-2.5-flash
```

Cloud Run provides the `PORT` environment variable automatically, so do not set `PORT` manually during deployment.

For API-key deployment, configure `GEMINI_API_KEY` or `GOOGLE_API_KEY` as a secret or secure environment variable instead. For service-account deployment, grant the Cloud Run runtime service account `roles/aiplatform.user`.

## Environment Variables

| Variable | Required | Description |
| --- | --- | --- |
| `GEMINI_API_KEY` | Required for Ask AI when not using Vertex AI | Enables Gemini-powered decision generation, recommendations, Disaster AI, and Ask AI Google Search grounding. Non-chat modules fall back to rules when missing. |
| `GOOGLE_API_KEY` | Optional alternative API key | Alternative Google AI API key name used by the GenAI SDK. |
| `GOOGLE_GENAI_USE_VERTEXAI` | Required for Cloud Run service-account Ask AI | Set to `true` to use Google Cloud Vertex AI credentials instead of an API key. |
| `GOOGLE_CLOUD_PROJECT` | Required with `GOOGLE_GENAI_USE_VERTEXAI=true` | Google Cloud project ID used by Vertex AI. |
| `GOOGLE_CLOUD_LOCATION` | No | Vertex AI location. Defaults to `us-central1` for the app. |
| `GEMINI_MODEL` | No | Gemini model used by Ask AI. Defaults to `gemini-2.5-flash`. |
| `PORT` | No for local only | Server port. Defaults to `8080`; Cloud Run sets this automatically. |

## Safety Notes

This project is an educational and decision-support tool. It is not a replacement for local agriculture officers, soil testing laboratories, veterinary support, disaster response teams, police, traffic police, or medical professionals.

Agriculture guidance:

- Fertilizer and pesticide amounts are estimates.
- Exact quantities depend on soil test, climate, crop variety, land condition, and local agriculture office recommendations.
- Wear gloves, masks, and protective clothing when handling fertilizers or pesticides.
- Keep agrochemicals away from children, food, drinking water, and livestock.

Disaster guidance:

- Call local emergency services first during immediate danger.
- Confirm road access with official responders before travel.
- Do not risk human life to save property, tools, crops, or livestock.
- Disaster conditions can change quickly, so use official updates whenever possible.

## Development Workflow

Useful commands:

```bash
git status
python -m pytest -q
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Commit and push:

```bash
git add .
git commit -m "your commit message"
git push origin main
```

## License

No license file is currently included. Add a license before using this project in production or distributing it publicly.

## Author

Developed by Sunil Gotame for a smart farming AI web app project.
