# AgriMind Agent - Smart Farming AI Decision & Production Guide

AgriMind Agent is an intelligent, full-stack decision-making agent and production guide system built for modern smart farming. Developed as a capstone project for the Google 5-Day AI Agents challenge, this application showcases how deterministic safety rules, dynamic Gemini-powered reasoning, scaled land calculations, and simulation-based planning come together to solve complex agriculture orchestration challenges.

---

## 🌾 Capstone Concept & Background

In modern agricultural operations, farmers must continuously analyze a complex, multi-dimensional matrix of variables—soil moisture, nutrient levels, weather patterns, pest threats, budget limitations, and market price volatility—to select the single best action. 

**AgriMind Agent** automates this by behaving as a virtual agronomist. It provides two main modes of operations:
1. **Farming Simulator & Decision Engine**: Evaluates current farm state and recommends the single best action, with safety overrides.
2. **Crop Farming Guide & Tailored Recommender**: Exposes comprehensive, step-by-step farming guides for **21 crops** and dynamically generates custom agronomist recommendations scaled to user land parameters (with Nepal-specific unit conversions).

---

## ✨ Features

- **Hybrid Decision Architecture**: Combines Pydantic schemas, strict deterministic rules (for safety and budget limitations), and Google Gemini reasoning.
- **Safety-Critical Controller**: Prevents impossible actions, such as spending more capital than available or harvesting non-mature crops, and overrides unsafe AI suggestions.
- **Crop Farming Guide**: Step-by-step guides for 21 crops covering growing methods, seed rates, spacing, fertilization, weed/pest/disease care, expected yield, and storage.
- **Customized Recommendation Engine**: Dynamically scales quantities of seeds, compost, and chemical fertilizers to the exact land size and unit, customized by experience level and organic vs. chemical preference.
- **Nepal-Friendly Spacing & Units**: Supports local land units—**Ropani** (hills), **Katha** (Terai), **Bigha** (Terai), as well as standard Hectares and Square Meters.
- **Structured LLM Outputs**: Leverages the official **Google GenAI SDK** (`google-genai`) to return typed Pydantic responses matching `AgentDecision` and `CropRecommendationResponse` schemas.
- **Robust Fallback**: Functions completely offline/without an API key using local JSON databases and a priority-based deterministic scaling recommendation engine.
- **Premium Web Dashboard**: Responsive, emerald-themed glassmorphic UI featuring tabbed navigation for Simulator, Crop Guide, and Custom Recommendation forms.

---

## 📂 Project Structure

```text
agrimind-agent/
│
├── agent/
│   ├── __init__.py
│   ├── schemas.py          # Pydantic schemas (FarmState, CropGuide, etc.)
│   ├── rules.py            # Safety controller and deterministic fallback rules
│   ├── gemini_brain.py     # Google GenAI SDK integration for decisions
│   ├── crop_guide.py       # Crop guide matching and search algorithms
│   ├── recommendation.py   # Scaled recommendation generator (Gemini + Fallback)
│   ├── engine.py           # Coordinator managing Gemini calls & safety overrides
│   └── simulation.py       # State-transition simulation logic
│
├── data/
│   └── crop_guides.json    # Extensive database containing guide details for 21 crops
│
├── static/
│   └── style.css           # Custom CSS for dark-mode glassmorphic styling & grids
│
├── templates/
│   └── index.html          # Interactive Jinja2 dashboard template
│
├── tests/
│   ├── __init__.py
│   ├── test_agent_rules.py # Tests for possible actions, safety overrides, and fallback
│   ├── test_api.py         # Tests for FastAPI endpoints (/health, /decide, /simulate)
│   └── test_crop_guide_api.py # Tests for crop list, guides, search, and recommendation
│
├── .env                    # Environment configuration file (secret)
├── .env.example            # Mock / reference env setup
├── .gitignore              # Ignores .env, virtualenvs, cache folders
├── Dockerfile              # Docker containerization config
├── main.py                 # FastAPI application and uvicorn runner
├── requirements.txt        # Python dependency manifest
└── README.md               # Extensive project documentation
```

---

## 🌽 Available Crop Guides (21 Crops)
- **Cereals**: Rice / Paddy, Maize, Wheat
- **Vegetables**: Potato, Tomato, Cauliflower, Cabbage, Onion, Cucumber, Pumpkin
- **Spices**: Garlic, Ginger, Turmeric, Chili
- **Legumes & Oilseeds**: Mustard, Lentil, Soybean
- **Fruits**: Banana, Mango, Orange, Apple

---

## ⚙️ Local Setup & Configuration

### Prerequisites
- Python 3.12+
- Standard terminal shell

### 1. Clone & Set Up Directory
Ensure you are inside the `agrimind-agent` directory:
```bash
cd agrimind-agent
```

### 2. Create Virtual Environment & Install Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file by copying the template:
```bash
cp .env.example .env
```
Inside your `.env` file, populate your **Google Gemini API Key**:
```env
GEMINI_API_KEY=YOUR_ACTUAL_GEMINI_API_KEY
PORT=8080
```
*Note: If `GEMINI_API_KEY` is omitted or empty, AgriMind Agent runs automatically in deterministic rule-based fallback mode.*

---

## 🚀 Running the Application

To launch the FastAPI dev server:
```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```
Once started, open your browser and navigate to:
**`http://localhost:8080`**

---

## 🧪 Running Automated Tests

We use `pytest` to execute our unit tests:
```bash
pytest -v
```

---

## 📡 API Reference & Curl Examples

### 1. Get Crops List
- **Endpoint**: `GET /crops`
- **Response**:
  ```json
  [
    {"crop_name": "Rice / Paddy", "category": "Cereal"},
    {"crop_name": "Maize", "category": "Cereal"}
  ]
  ```

### 2. Get Crop Guide
- **Endpoint**: `GET /crops/{crop_name}` (Case-insensitive)
- **Response**:
  ```json
  {
    "crop_name": "Tomato",
    "category": "Vegetable",
    "suitable_climate": "Warm-season crop...",
    "suitable_soil": "Well-drained sandy loam...",
    "expected_yield": "25 to 40 tons per hectare...",
    "safety_note": "Always wash harvested tomatoes..."
  }
  ```

### 3. Get Customized Recommendation
- **Endpoint**: `POST /crops/recommend`
- **Request**:
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

---

## ☁️ Deploying to Google Cloud Run

Deploying to Google Cloud Run takes only a few commands. Ensure you have the `gcloud` CLI installed and authenticated.

```bash
# 1. Configure the GCP project ID
gcloud config set project YOUR_PROJECT_ID

# 2. Build and deploy using Google Cloud Build / Buildpacks
gcloud run deploy agrimind-agent \
    --source . \
    --region asia-south1 \
    --allow-unauthenticated \
    --set-secrets GEMINI_API_KEY=GEMINI_API_KEY:latest
```

---

## 🖥️ Pushing to GitHub

To push the project to your GitHub repository:

```bash
# Verify status
git status

# Add all files to staging area
git add .

# Create a commit
git commit -m "Add crop farming guide and production recommendation features"

# Push code to GitHub
git push
```

---

## ⚠️ Agriculture Safety Note & Disclaimer

Do not claim that one fertilizer quantity is perfect for every place. **Exact fertilizer and pesticide quantity depends on soil test, climate, crop variety, land condition, and local agriculture office recommendations.** 

Ensure proper protective gear (mask, gloves) when handling chemical fertilizers or spraying pesticides. Keep all agro-chemicals out of reach of children and animals.
