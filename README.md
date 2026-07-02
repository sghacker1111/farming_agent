# AgriMind Agent - Smart Farming AI Decision Agent

AgriMind Agent is an intelligent, full-stack decision-making agent built for modern smart farming. Engineered as a capstone project for the Google 5-Day AI Agents challenge, this application showcases how deterministic safety rules, dynamic Gemini-powered reasoning, and simulation-based planning come together to solve complex agriculture orchestration challenges.

---

## 🌾 Capstone Concept & Background

In modern agricultural operations, farmers must continuously analyze a complex, multi-dimensional matrix of variables—soil moisture, nutrient levels, weather patterns, pest threats, budget limitations, and market price volatility—to select the single best action. 

**AgriMind Agent** automates this by behaving as a virtual agronomist. It receives farm state data, processes it through a hybrid pipeline (deterministic safety rules + Gemini LLM brain), and recommends the optimal action. It also simulates the next day's state, enabling users to run interactive "what-if" agricultural scenarios.

---

## ✨ Features

- **Hybrid Decision Architecture**: Combines Pydantic schemas, strict deterministic rules (for safety and budget limitations), and Google Gemini reasoning for long-term planning.
- **Safety-Critical Controller**: Ensures that the agent never proposes impossible actions, such as spending more capital than available or harvesting non-mature crops, and overrides unsafe AI suggestions.
- **Structured LLM Outputs**: Leverages the official **Google GenAI SDK** (`google-genai`) to return typed Pydantic responses matching the `AgentDecision` schema.
- **Robust Fallback**: Functions completely offline / without an API key using a comprehensive, priority-based deterministic fallback decision tree.
- **Farming Simulator**: Predicts the next-state transitions of the farm based on selected actions and environmental degradation.
- **Premium Web Dashboard**: Fully responsive, emerald-themed glassmorphic UI displaying parameters, recommendation details, and simulation steps.

---

## 📂 Project Structure

```text
agrimind-agent/
│
├── agent/
│   ├── __init__.py
│   ├── schemas.py          # Pydantic schemas (FarmState, AgentDecision, etc.)
│   ├── rules.py            # Safety controller and deterministic fallback rules
│   ├── gemini_brain.py     # Google GenAI SDK integration with structured outputs
│   ├── engine.py           # Coordinator managing Gemini calls & safety overrides
│   └── simulation.py       # State-transition simulation logic
│
├── static/
│   └── style.css           # Custom CSS for dark-mode glassmorphism styling
│
├── templates/
│   └── index.html          # Interactive Jinja2 dashboard template
│
├── tests/
│   ├── __init__.py
│   ├── test_agent_rules.py # Tests for possible actions, safety overrides, and fallback
│   └── test_api.py         # Tests for FastAPI endpoints (/health, /decide, /simulate)
│
├── .env.example            # Mock / reference env setup
├── .gitignore              # Ignores .env, virtualenvs, cache folders
├── main.py                 # FastAPI application and uvicorn runner
├── requirements.txt        # Python dependency manifest
└── README.md               # Extensive project documentation
```

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

### 1. Health Check
Checks if the API is online.
- **Endpoint**: `GET /health`
- **Response**:
  ```json
  {"status": "ok"}
  ```

### 2. Get Decision
Submits the farm state and returns the optimal action recommendation.
- **Endpoint**: `POST /agent/decide`
- **Request**:
  ```bash
  curl -X POST "http://localhost:8080/agent/decide" \
       -H "Content-Type: application/json" \
       -d '{
         "day": 1,
         "water_level": 25,
         "soil_health": 70,
         "money": 100,
         "crop_stage": "growing",
         "pest_risk": 15,
         "weather": "sunny",
         "market_price": "medium",
         "harvested": false
       }'
  ```
- **Response**:
  ```json
  {
    "action": "irrigate",
    "confidence_score": 0.85,
    "reasons": ["Soil moisture level is critically low (25%)."],
    "risks": ["Low soil moisture (25%)."],
    "expected_result": "Soil moisture restored to safe levels.",
    "next_step": "Monitor crop growth and pest threats.",
    "agent_explanation": "Recommended irrigation because water levels dropped below optimal threshold under sunny weather."
  }
  ```

### 3. Run Simulation Step
Evaluates the decision and returns the simulated next state of the farm.
- **Endpoint**: `POST /agent/simulate`
- **Request**:
  ```bash
  curl -X POST "http://localhost:8080/agent/simulate" \
       -H "Content-Type: application/json" \
       -d '{
         "day": 5,
         "water_level": 60,
         "soil_health": 80,
         "money": 15,
         "crop_stage": "mature",
         "pest_risk": 5,
         "weather": "sunny",
         "market_price": "high",
         "harvested": false
       }'
  ```

---

## ☁️ Deploying to Google Cloud Run

Deploying to Google Cloud Run takes only a few commands. Ensure you have the `gcloud` CLI installed and authenticated to your GCP project.

```bash
# 1. Configure the GCP project ID
gcloud config set project YOUR_PROJECT_ID

# 2. Build the image and deploy to Cloud Run using Buildpacks
gcloud run deploy agrimind-agent \
    --source . \
    --region us-central1 \
    --allow-unauthenticated \
    --set-env-vars GEMINI_API_KEY="YOUR_ACTUAL_GEMINI_API_KEY"
```

---

## 🖥️ Pushing to GitHub

To push the project to your GitHub repository:

```bash
# Initialize git repository
git init

# Add all files to staging area
git add .

# Create the initial commit
git commit -m "feat: init AgriMind smart farming agent with FastAPI, Gemini SDK & interactive simulation UI"

# Link to remote repository
git remote add origin https://github.com/sghacker1111/farming_agent

# Rename branch to main
git branch -M main

# Push code to GitHub
git push -u origin main
```
