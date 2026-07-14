# AI Startup Blueprint Generator

> **India's first AI-powered startup co-pilot** — Turn any startup idea into a complete, investor-ready business blueprint in under 60 seconds using **IBM Granite AI + RAG + IBM Cloud**.

[![Deployed Link](https://venturepilot-ai-jtqc.onrender.com)

---

## ✨ Features

- 🤖 **IBM Granite AI** — Enterprise-grade LLM for structured blueprint generation
- 🔍 **RAG Pipeline** — LangChain + FAISS + Sentence Transformers + IBM COS knowledge retrieval
- ☁️ **IBM Cloud Object Storage** — Stores knowledge base, blueprints, PDFs, and resources
- 📊 **23 Interactive Dashboard Sections** — Charts, gauges, timelines, expandable AI explanations
- 🏛️ **Government Scheme Explorer** — Startup India, MSME, DPIIT, TIDE 2.0, AIM (RAG-powered)
- 💰 **Funding Recommendations** — Bootstrap → Angel → VC → Grants with eligibility details
- 📈 **Growth Simulation** — 12-month financial simulation with interactive charts
- 🚀 **Pitch Deck Generator** — 10-slide investor presentation with PDF export
- 🤖 **AI Mentor Chat** — Floating AI assistant understands your blueprint and uses RAG
- 📄 **Export Center** — Blueprint PDF, Pitch Deck PDF, JSON — all saved to IBM COS
- 🎛️ **AGENT_INSTRUCTIONS** — Editable AI personality, tone, and analysis configuration

---

## 🏗️ Architecture

```
┌──────────────┐    ┌─────────────────────────────────────────────────┐
│  Frontend    │    │                    Backend                       │
│              │    │                                                   │
│ Landing Page │───▶│  Flask App                                       │
│ Idea Form    │    │  ├── RAG Pipeline (LangChain + FAISS)            │
│ Dashboard    │    │  │   └── IBM Cloud Object Storage (knowledge)    │
│ Resources    │    │  ├── IBM Granite LLM (watsonx.ai)                │
│ Export       │    │  ├── Prompt Manager (AGENT_INSTRUCTIONS)         │
│              │    │  ├── COS Service (blueprints, reports, PDFs)     │
│ Chart.js     │    │  └── PDF Generator (ReportLab)                   │
│ Bootstrap 5  │    │                                                   │
│ AOS Anim.    │    │  APIs: /api/generate, /api/chat, /api/export      │
└──────────────┘    └─────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd startup_blueprint
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your IBM Cloud credentials
```

### 3. Run Locally

```bash
python run.py
# Open: http://localhost:5000
```

The app runs in **demo mode** (rich mock data) if IBM credentials are not configured — perfect for local development and demos.

---

## ⚙️ Configuration

### IBM watsonx.ai Setup

1. Go to [IBM Cloud](https://cloud.ibm.com) → Create a **watsonx.ai** instance
2. Create a new **Project** in watsonx.ai Studio
3. Generate an **API Key** under Manage → Access (IAM) → API Keys
4. Set `IBM_WATSONX_API_KEY`, `IBM_WATSONX_URL`, `IBM_WATSONX_PROJECT_ID` in `.env`

### IBM Cloud Object Storage Setup

1. Create a **Cloud Object Storage** instance in IBM Cloud
2. Create three buckets: `startup-knowledge-base`, `startup-reports`, `startup-resources`
3. Generate **Service Credentials** with HMAC enabled
4. Set `IBM_COS_API_KEY`, `IBM_COS_INSTANCE_CRN`, `IBM_COS_ENDPOINT` in `.env`

### Add Knowledge Base Documents

Upload `.txt` or `.json` files to your `startup-knowledge-base` COS bucket or place them in the local `knowledge_base/` directory. The RAG pipeline will automatically index them.

---

## 🎛️ AGENT_INSTRUCTIONS

Edit [`app/agent_instructions.py`](app/agent_instructions.py) to customize AI behavior:

```python
AGENT_INSTRUCTIONS = {
    "ai_personality": "Expert AI Startup Consultant",
    "tone": "professional yet approachable",
    "ecosystem_preference": "Indian startup ecosystem",
    "competitor_analysis_depth": "deep analysis",
    "budget_assumptions": { "currency": "INR", ... },
    # ... more settings
}
```

Changes take effect immediately without restarting the app.

---

## 📁 Project Structure

```
startup_blueprint/
├── run.py                          # Flask entry point
├── requirements.txt
├── .env.example
├── render.yaml                     # Render Infrastructure-as-code spec
├── app.json                        # Deployment metadata
├── RENDER_DEPLOYMENT.md            # Render deployment guide
├── DEPLOYMENT.md                   # IBM Cloud deployment guide
├── knowledge_base/                 # Local RAG knowledge base docs
├── exports/                        # Generated PDFs and JSON reports
└── app/
    ├── __init__.py                 # Flask app factory
    ├── agent_instructions.py       # 🎛️ AI configuration (EDIT THIS)
    ├── routes/
    │   ├── main.py                 # Page routes
    │   ├── api.py                  # Blueprint generation API
    │   ├── chat.py                 # AI Mentor chat API
    │   ├── export.py               # PDF/JSON export API
    │   └── resources.py            # COS resources API
    ├── services/
    │   ├── granite_service.py      # IBM Granite integration
    │   ├── cos_service.py          # IBM Cloud Object Storage
    │   ├── rag_service.py          # RAG pipeline (LangChain + FAISS)
    │   ├── prompt_manager.py       # Prompt builder
    │   └── pdf_service.py          # PDF generation (ReportLab)
    ├── templates/
    │   ├── base.html
    │   ├── index.html              # Landing page
    │   ├── generate.html           # Startup idea form
    │   ├── dashboard.html          # Interactive dashboard (23 sections)
    │   ├── resources.html          # Resource hub
    │   └── export.html             # Export center
    └── static/
        ├── css/main.css
        └── js/
            ├── main.js             # Shared JS (chat, exports, nav)
            └── dashboard.js        # All dashboard section renderers
```

---

## 🌐 Dashboard Sections

| # | Section | Visualization |
|---|---------|---------------|
| 1 | Startup Readiness Scores | Animated gauges + score bars |
| 2 | Executive Summary | Premium info cards |
| 3 | Business Model Canvas | Interactive 9-cell grid |
| 4 | Market Analysis | Bar charts + persona cards |
| 5 | Competitor Analysis | Feature comparison + bar chart |
| 6 | SWOT Analysis | 4-color expandable cards |
| 7 | Budget Estimator | Pie + bar charts |
| 8 | Revenue Model | Score cards with recommendations |
| 9 | Funding Recommendations | Expandable funding cards |
| 10 | Government Scheme Explorer | Modal-based scheme details |
| 11 | Legal Compliance Checklist | Interactive checkboxes |
| 12 | Startup Roadmap | Animated vertical timeline |
| 13 | Growth Simulation | Line charts + KPI cards |
| 14 | Risk Analysis | Risk radar + mitigation cards |
| 15 | Investor Readiness | Gauge + gap analysis |
| 16 | Startup Idea Improver | Before/after improvement cards |
| 17 | AI Name Generator | Name + tagline + domain cards |
| 18 | Elevator Pitch | 30-sec + 2-min pitch with copy |
| 19 | Pitch Deck Preview | 10-slide visual preview |
| 20 | AI Mentor Chat | Floating RAG-powered chat |
| 21 | AI Recommendation Center | Expandable action cards |

---

## ⚠️ Disclaimer

This application generates AI-powered insights using IBM Granite. All recommendations should be validated by domain experts — legal, financial, and business advisors — before making investment or business decisions.

---

## 🏆 Built With IBM Technology

| Technology | Purpose |
|-----------|---------|
| IBM watsonx.ai (Granite 3.3 8B) | Blueprint generation |
| IBM Cloud Object Storage | Knowledge base, reports, resources |
| IBM Cloud Code Engine | Serverless deployment |
| LangChain + FAISS | RAG pipeline |
| Sentence Transformers | Vector embeddings |

---

*Powered by IBM Granite AI + IBM Cloud Object Storage + RAG*
