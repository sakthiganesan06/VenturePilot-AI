"""
IBM watsonx.ai Granite Integration Service
"""

import os
import json
import re
import time
import logging
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)

try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    IBM_AVAILABLE = True
except ImportError:
    IBM_AVAILABLE = False
    logger.warning("ibm-watsonx-ai not installed — using mock Granite responses for development")


class GraniteService:
    """Wrapper around IBM watsonx.ai Granite model inference."""

    def __init__(self):
        self.url        = os.environ.get("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.api_key    = os.environ.get("IBM_WATSONX_API_KEY", "")
        self.project_id = os.environ.get("IBM_WATSONX_PROJECT_ID", "")
        self.model_id   = os.environ.get("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct")
        self._client: Optional[object] = None
        self._model:  Optional[object] = None

        if IBM_AVAILABLE and self.api_key:
            self._init_client()

    @property
    def model(self) -> Optional[object]:
        """Lazy loader for the ModelInference client."""
        if self._model is None and IBM_AVAILABLE:
            self._init_client()
        return self._model

    # ── Initialization ─────────────────────────────────────────────────────────
    def _init_client(self):
        # Reload configuration in case environment variables were loaded late
        self.url        = os.environ.get("IBM_WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
        self.api_key    = os.environ.get("IBM_WATSONX_API_KEY", "")
        self.project_id = os.environ.get("IBM_WATSONX_PROJECT_ID", "")
        self.model_id   = os.environ.get("GRANITE_MODEL_ID", "ibm/granite-3-3-8b-instruct")

        if not self.api_key:
            logger.warning("IBM_WATSONX_API_KEY not found in environment. GraniteService will remain in mock mode.")
            return

        try:
            credentials = Credentials(url=self.url, api_key=self.api_key)
            self._client = APIClient(credentials=credentials, project_id=self.project_id)
            self._model  = ModelInference(
                model_id=self.model_id,
                api_client=self._client,
                params={
                    GenParams.MAX_NEW_TOKENS: 8000,
                    GenParams.TEMPERATURE:    0.7,
                    GenParams.TOP_P:          0.95,
                    GenParams.REPETITION_PENALTY: 1.1,
                }
            )
            logger.info(f"✅ Granite model initialised: {self.model_id}")
        except Exception as e:
            logger.error(f"Failed to initialise Granite client: {e}")
            self._model = None

    # ── Public API ─────────────────────────────────────────────────────────────
    def generate(self, system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
        """Generate text using Granite. Raises RuntimeError if unavailable."""
        model = self.model
        if not model:
            raise RuntimeError("Watsonx.ai client could not be initialised. Please check your IBM_WATSONX_API_KEY and credentials in `.env`.")
        return self._generate_real(system_prompt, user_prompt, max_tokens)

    def _generate_real(self, system_prompt: str, user_prompt: str, max_tokens: int) -> str:
        prompt = f"<|system|>\n{system_prompt}\n<|user|>\n{user_prompt}\n<|assistant|>\n"
        for attempt in range(3):
            try:
                result = self._model.generate_text(prompt=prompt)
                return result
            except Exception as e:
                logger.error(f"Granite generation error (attempt {attempt+1}): {e}")
                if attempt < 2:
                    time.sleep(2 ** attempt)
        return json.dumps({"error": "Granite generation failed after 3 attempts"})

    # ── JSON Helpers ───────────────────────────────────────────────────────────
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        """Generate and parse JSON from Granite."""
        raw = self.generate(system_prompt, user_prompt)
        return self._extract_json(raw)

    @staticmethod
    def _clean_granite_json(text: str) -> str:
        """Clean common Granite JSON output issues before parsing."""
        # Slice to first '{' — removes preamble like "Here is the JSON:"
        start = text.find('{')
        if start != -1:
            text = text[start:]

        # Strip markdown fences
        text = re.sub(r"```(?:json)?", "", text)

        # Remove JS single-line comments  //...
        text = re.sub(r"//[^\n\"]*\n", "\n", text)

        # Fix broken URLs split across lines by Granite:  "https:\n        "https: → remove the line
        text = re.sub(r'"https?:\s*\n\s*"https?:', '"https://example.com",\n        "https://example.com"', text)

        # Remove any bare unquoted words that appear as invalid values
        # e.g.  "key": word,  →  "key": "word",
        text = re.sub(r':\s*([A-Za-z][A-Za-z0-9 _-]*)(\s*[,}\]])', r': "\1"\2', text)

        # Remove trailing commas before } or ]
        text = re.sub(r",\s*([}\]])", r"\1", text)

        # Remove control characters (non-printable except \n \r \t)
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

        return text

    @staticmethod
    def _extract_json(text: str) -> dict:
        text = GraniteService._clean_granite_json(text)

        # 1. Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 2. Repair truncated JSON by closing open structures
        snippet = text.rstrip().rstrip(',')
        open_braces   = snippet.count('{') - snippet.count('}')
        open_brackets = snippet.count('[') - snippet.count(']')
        closing = ']' * max(0, open_brackets) + '}' * max(0, open_braces)
        repaired = re.sub(r",\s*([}\]])", r"\1", snippet + closing)
        try:
            return json.loads(repaired)
        except Exception:
            pass

        # 3. Walk backwards to find last complete valid JSON object
        end = len(text)
        for _ in range(100):
            end = text.rfind('}', 0, end)
            if end == -1:
                break
            candidate = text[:end + 1]
            open_b  = candidate.count('{') - candidate.count('}')
            open_br = candidate.count('[') - candidate.count(']')
            candidate += ']' * max(0, open_br) + '}' * max(0, open_b)
            candidate = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(candidate)
            except Exception:
                pass

        logger.error("Could not parse JSON from Granite response")
        return {}

    # ── Mock Data ──────────────────────────────────────────────────────────────
    def _generate_mock(self, user_prompt: str) -> str:
        """Rich mock blueprint for development / demo without IBM credentials."""
        idea = user_prompt[:80] if user_prompt else "AI Startup"
        return json.dumps(self._build_mock_blueprint(idea))

    @staticmethod
    def _build_mock_blueprint(idea: str) -> dict:
        return {
            "scores": {
                "overall": 78, "innovation": 82, "market_demand": 75,
                "investment_potential": 70, "feasibility": 80, "scalability": 85,
                "why": "Strong innovation score driven by AI-first approach. Market demand is high given digital transformation trends. Scalability potential is excellent with a SaaS model."
            },
            "executive_summary": {
                "startup_names": ["NexGen AI", "BlueprintAI", "VentureForge", "IdeaVault Pro", "LaunchPad AI"],
                "tagline": "Turn Ideas Into Ventures — Instantly.",
                "industry": "AI / SaaS / B2B",
                "problem": "Early-stage founders lack access to affordable, expert-level business strategy and market intelligence.",
                "solution": f"An AI-powered platform that transforms any startup idea into a fully structured, investor-ready blueprint in minutes using IBM Granite and RAG.",
                "target_customers": "First-time entrepreneurs, solopreneurs, startup founders, MBA students, incubators",
                "estimated_budget": "₹25,00,000 – ₹50,00,000 (Seed Stage)",
                "why": "The problem is validated — 90% of startups fail due to poor planning. Our AI-driven approach democratises expert consulting."
            },
            "business_model_canvas": {
                "key_partners": ["IBM Cloud", "AWS", "Payment Gateways", "Legal Tech Partners", "Incubators"],
                "key_activities": ["AI Model Development", "RAG Pipeline Maintenance", "Customer Onboarding", "Sales & Marketing"],
                "key_resources": ["IBM Granite LLM", "Vector Database", "Engineering Team", "Brand & Domain"],
                "value_propositions": ["Instant startup blueprint", "AI-powered market insights", "Investor-ready documents", "Cost-effective consulting alternative"],
                "customer_relationships": ["Self-service SaaS", "AI Chat Mentor", "Email Support", "Community Forum"],
                "channels": ["SEO / Content Marketing", "Product Hunt", "LinkedIn Ads", "Startup Incubator Partnerships"],
                "customer_segments": ["Early-stage founders", "B-school students", "Accelerator cohorts", "SMEs pivoting to tech"],
                "cost_structure": ["LLM API Costs", "Infrastructure (IBM Cloud)", "Engineering Salaries", "Marketing & Sales"],
                "revenue_streams": ["SaaS Subscription", "Pay-per-blueprint", "White-label licensing", "Premium consulting add-ons"],
                "why": "Canvas designed for maximum asset leverage — minimal fixed costs with variable AI infrastructure scaling with usage."
            },
            "market_analysis": {
                "market_size": "₹4,200 Crore (India) | $680 Billion (Global AI SaaS)",
                "growth_rate": "34.5% CAGR",
                "tam": "₹4,200 Cr",
                "sam": "₹840 Cr",
                "som": "₹84 Cr",
                "trends": [
                    "AI adoption in SMEs accelerating post-2023",
                    "Democratisation of startup tooling",
                    "Rise of no-code / AI-first SaaS platforms",
                    "Government push for digital entrepreneurship (Startup India 2.0)",
                    "Tier-2 and Tier-3 city startup boom in India"
                ],
                "customer_personas": [
                    {"name": "Arjun — First-time Founder", "age": 27, "pain": "No business background, overwhelmed by planning", "willingness_to_pay": "₹1,500/mo"},
                    {"name": "Priya — MBA Student", "age": 24, "pain": "Needs investor-ready documents for competitions", "willingness_to_pay": "₹500/mo"},
                    {"name": "Rajesh — SME Owner Pivoting", "age": 42, "pain": "Wants to launch tech product but lacks startup knowledge", "willingness_to_pay": "₹3,000/mo"}
                ],
                "why": "India has 100,000+ startups and 50,000+ new registrations per year — a massive underserved market for AI-powered consulting tools."
            },
            "competitors": [
                {"name": "Bizplan", "pricing": "$29/mo", "strengths": ["Good templates"], "weaknesses": ["No AI", "US-focused"], "market_share": 8},
                {"name": "LivePlan", "pricing": "$20/mo", "strengths": ["Financial projections"], "weaknesses": ["Outdated UI", "Manual input heavy"], "market_share": 12},
                {"name": "Upmetrics", "pricing": "$15/mo", "strengths": ["Affordable"], "weaknesses": ["Limited AI", "No Indian context"], "market_share": 6},
                {"name": "Our Product", "pricing": "₹999/mo", "strengths": ["IBM Granite AI", "RAG", "Indian context", "Interactive dashboard"], "weaknesses": ["New entrant", "Brand recognition"], "market_share": 0}
            ],
            "competitive_advantage": "Only platform combining IBM Granite AI + RAG + Indian government scheme intelligence + interactive visual dashboard.",
            "market_gap": "No India-focused AI startup consultant exists at an accessible price point for early-stage founders.",
            "swot": {
                "strengths": ["IBM Granite AI backbone", "Unique RAG pipeline", "Deep Indian startup context", "Interactive visual output", "Fast time-to-value"],
                "weaknesses": ["New brand with no track record", "Depends on IBM API availability", "Initial limited knowledge base"],
                "opportunities": ["100K+ new Indian startups/year", "Government Startup India 2.0 push", "Global expansion potential", "White-label for incubators and accelerators"],
                "threats": ["Big Tech (Google, Microsoft) entering space", "Price competition", "AI regulatory changes", "LLM commoditisation"],
                "why": "SWOT reveals a strong opportunity window — act fast before big tech saturates the segment."
            },
            "budget": {
                "development": 800000, "infrastructure": 300000, "marketing": 500000,
                "operations": 200000, "hiring": 1200000, "legal": 150000, "miscellaneous": 100000,
                "total": 3250000,
                "why": "Budget is conservative with 18-month runway. Development costs include IBM Cloud and AI API fees. Hiring assumes 3 engineers + 1 designer + 1 salesperson."
            },
            "revenue_model": {
                "recommended": "SaaS Subscription",
                "options": [
                    {"model": "SaaS Subscription", "score": 92, "mrr_potential": "₹5L-₹20L", "recommended": True},
                    {"model": "Pay-per-Blueprint", "score": 75, "mrr_potential": "₹1L-₹5L", "recommended": False},
                    {"model": "White-label Licensing", "score": 80, "mrr_potential": "₹3L-₹15L", "recommended": False},
                    {"model": "Freemium", "score": 70, "mrr_potential": "₹2L-₹8L", "recommended": False}
                ],
                "why": "SaaS subscription provides predictable MRR and highest LTV. With a freemium tier to drive user acquisition."
            },
            "funding": [
                {"type": "Bootstrap", "amount": "₹5L-₹25L", "stage": "Pre-seed", "eligibility": "Self-funded", "advantage": "Full control, no dilution", "challenge": "Limited runway"},
                {"type": "Angel Investors", "amount": "₹25L-₹2Cr", "stage": "Pre-seed/Seed", "eligibility": "Validated idea + team", "advantage": "Mentorship + network", "challenge": "Equity dilution 10-20%"},
                {"type": "Startup India Seed Fund", "amount": "Up to ₹20L", "stage": "Pre-seed", "eligibility": "DPIIT registered startup <2 years", "advantage": "Non-dilutive grant", "challenge": "Competitive application"},
                {"type": "SIDBI SCALE", "amount": "₹10L-₹1Cr", "stage": "Early stage", "eligibility": "Tech startup with prototype", "advantage": "Low-interest loan", "challenge": "Revenue track record needed"},
                {"type": "Venture Capital", "amount": "₹5Cr+", "stage": "Series A", "eligibility": "₹1Cr+ ARR or strong growth", "advantage": "Scale fast", "challenge": "High dilution, board control"}
            ],
            "government_schemes": [
                {"name": "Startup India", "ministry": "DPIIT", "benefit": "Tax exemption, fast-track IP, funding access", "eligibility": "Indian company <10 years, <₹100Cr turnover", "docs": ["Incorporation cert", "Board resolution", "PAN card"]},
                {"name": "MSME Udyam", "ministry": "MoMSME", "benefit": "Subsidies, priority loans, government tender preference", "eligibility": "Micro/Small enterprise", "docs": ["Aadhaar", "PAN", "Bank details"]},
                {"name": "Digital India Internship", "ministry": "MeitY", "benefit": "Mentorship and government project exposure", "eligibility": "Tech-focused startups", "docs": ["Company registration", "Project proposal"]},
                {"name": "TIDE 2.0", "ministry": "MeitY", "benefit": "Up to ₹7L grant + incubation support for deeptech/ICT", "eligibility": "ICT-based startup with PoC", "docs": ["PoC demo", "Team details", "Financial projections"]}
            ],
            "legal_checklist": [
                {"item": "Private Limited Company Registration", "priority": "Critical", "estimated_cost": "₹7,000 – ₹15,000", "timeline": "7-15 days"},
                {"item": "GST Registration", "priority": "High", "estimated_cost": "Free", "timeline": "3-5 days"},
                {"item": "DPIIT Startup India Recognition", "priority": "High", "estimated_cost": "Free", "timeline": "10-20 days"},
                {"item": "Trademark Registration", "priority": "Medium", "estimated_cost": "₹4,500 per class", "timeline": "18-24 months"},
                {"item": "Founders Agreement", "priority": "Critical", "estimated_cost": "₹10,000 – ₹30,000", "timeline": "1-3 days"},
                {"item": "Privacy Policy & Terms of Service", "priority": "High", "estimated_cost": "₹5,000 – ₹15,000", "timeline": "2-5 days"},
                {"item": "MSME Udyam Registration", "priority": "Medium", "estimated_cost": "Free", "timeline": "1-2 days"},
                {"item": "Patent Filing (if applicable)", "priority": "Low", "estimated_cost": "₹8,000 – ₹40,000", "timeline": "2-3 years"}
            ],
            "roadmap": [
                {"phase": "Idea", "duration": "Month 1", "tasks": ["Market research", "Problem validation", "Competitor analysis", "Define ICP"], "milestone": "Validated problem statement"},
                {"phase": "Research", "duration": "Month 1-2", "tasks": ["Customer interviews (50+)", "Survey 200+ potential users", "Define USP", "Technology stack decision"], "milestone": "Product-Market Fit hypothesis"},
                {"phase": "Prototype", "duration": "Month 2-3", "tasks": ["Wireframes", "Design system", "Technical architecture", "PoC build"], "milestone": "Working prototype"},
                {"phase": "MVP", "duration": "Month 3-5", "tasks": ["Core feature development", "IBM Granite integration", "RAG pipeline", "Basic UI"], "milestone": "MVP ready for beta"},
                {"phase": "Beta Testing", "duration": "Month 5-6", "tasks": ["50 beta users", "Collect feedback", "Iterate rapidly", "Fix critical bugs"], "milestone": "Beta with NPS > 40"},
                {"phase": "Launch", "duration": "Month 6-7", "tasks": ["Product Hunt launch", "Press release", "Influencer partnerships", "Paid ads"], "milestone": "100 paying customers"},
                {"phase": "Scale", "duration": "Month 7-18", "tasks": ["Hire sales team", "Enterprise sales", "White-label deals", "Series A prep"], "milestone": "₹1Cr ARR"}
            ],
            "risks": [
                {"category": "Technical", "risk": "IBM API downtime or rate limiting", "level": "Medium", "probability": 35, "mitigation": "Implement fallback models and response caching"},
                {"category": "Financial", "risk": "Runway exhaustion before product-market fit", "level": "High", "probability": 45, "mitigation": "Aggressive burn rate control, early revenue focus, government grants"},
                {"category": "Market", "risk": "Big Tech (Google/Microsoft) launches competitor product", "level": "High", "probability": 55, "mitigation": "Focus on India-specific features and enterprise white-label deals"},
                {"category": "Legal", "risk": "Data privacy regulations (DPDP Act)", "level": "Medium", "probability": 40, "mitigation": "Implement privacy-by-design, appoint DPO, regular audits"},
                {"category": "Operational", "risk": "Key team member attrition", "level": "Medium", "probability": 30, "mitigation": "ESOP scheme, competitive compensation, strong culture building"}
            ],
            "investor_readiness": {
                "score": 72,
                "funding_readiness": 68,
                "investment_risks": "Medium-High",
                "funding_timeline": "6-9 months to Angel round",
                "pitch_score": 75,
                "gaps": ["Need 3+ months revenue traction", "Build advisory board", "File provisional patent"],
                "why": "Strong technology differentiation and large market but needs revenue validation and stronger team credibility signals."
            },
            "improvements": [
                {"area": "Value Proposition", "current": "AI Startup Blueprint Generator", "improved": "India's First AI-Powered Startup Co-Pilot — From Idea to Investor in 10 Minutes", "impact": "High"},
                {"area": "Pricing", "current": "₹1,500/mo flat", "improved": "Freemium + ₹999 Starter + ₹2,999 Pro + ₹9,999 Enterprise", "impact": "High"},
                {"area": "Customer Acquisition", "current": "Generic digital ads", "improved": "Partner with 50+ incubators and accelerators as their official planning tool", "impact": "Very High"},
                {"area": "Differentiation", "current": "AI-powered", "improved": "The only platform with IBM Granite + Indian government scheme intelligence + live funding database", "impact": "High"},
                {"area": "Feature", "current": "Blueprint generation only", "improved": "Add investor matchmaking, CA connect, and legal filing integrations", "impact": "Medium"}
            ],
            "startup_names": {
                "names": ["VentureForge AI", "BlueprintAI", "NexPath", "FounderOS", "IdeaEngine Pro", "LaunchIQ", "StartAI India", "VentureMap"],
                "taglines": ["From Idea to Empire.", "Your AI Co-Founder.", "Strategy at Machine Speed.", "Build Smarter. Launch Faster."],
                "domains": ["ventureforge.ai", "blueprint.ai", "nexpath.in", "founderos.com", "ideaengine.in"]
            },
            "elevator_pitch": {
                "30_sec": "We're building India's first AI-powered startup co-pilot. Founders input their idea and in under 10 minutes receive a complete, investor-ready business blueprint — market analysis, business model, roadmap, funding recommendations, and a pitch deck — all powered by IBM Granite AI. We're targeting India's 100,000+ annual startup registrations with a SaaS model starting at ₹999 per month.",
                "2_min": "Every year, over 100,000 startups are registered in India. Yet 90% fail within 5 years — not because of bad ideas, but because founders lack access to expert business strategy, market intelligence, and investor-ready documentation. Hiring a consultant costs ₹5-50 lakhs. Business schools are inaccessible to most. And generic tools like LivePlan don't understand Indian markets, government schemes, or local regulations.\n\nWe built Blueprint AI — India's first AI-powered startup co-pilot. A founder enters their startup idea, and in under 10 minutes, our platform generates a complete business blueprint: validated market analysis, business model canvas, competitor landscape, budget estimation, 18-month roadmap, government scheme recommendations, legal compliance checklist, and a 10-slide investor pitch deck.\n\nWhat makes us different? We use IBM Granite — one of the most trusted enterprise AI models — combined with a RAG pipeline built on a curated knowledge base of Indian startup data, government policies, and funding databases. Every recommendation comes with an 'AI reasoning' explanation so founders understand the why, not just the what.\n\nOur business model is SaaS at ₹999/month, with a free tier to drive acquisition and enterprise licensing for incubators and accelerators. We're targeting the 50,000+ first-time founders who register annually and have no structured support.\n\nWe're raising ₹50 lakhs in pre-seed funding to build the team and achieve 500 paying customers in 9 months."
            },
            "recommendations": [
                {"title": "Launch a Free Tier Immediately", "impact": "Very High", "effort": "Low", "detail": "Offer 1 free blueprint per user with email capture. This drives virality and builds your user database. Startups love free tools and share them in communities."},
                {"title": "Partner with 10 Incubators in Month 1", "impact": "Very High", "effort": "Medium", "detail": "Approach IIT/IIM incubators, T-Hub, NASSCOM 10K Startups. Offer free white-label access in exchange for being their official planning tool. Each incubator brings 50-200 startups."},
                {"title": "Target Tier-2 Cities First", "impact": "High", "effort": "Low", "detail": "Jaipur, Pune, Ahmedabad, Kochi have thriving startup scenes with less competition. Regional language support will be a massive differentiator."},
                {"title": "Build in Public on LinkedIn", "impact": "High", "effort": "Low", "detail": "Share your building journey. Indian startup LinkedIn community is extremely active. 1 viral post can bring 500+ signups."},
                {"title": "File for DPIIT Recognition on Day 1", "impact": "High", "effort": "Low", "detail": "Immediate tax benefits, faster IP registration, and eligibility for ₹20L Seed Fund Scheme."}
            ],
            "simulation": {
                "monthly_revenue": [0, 0, 15000, 45000, 90000, 150000, 240000, 350000, 480000, 630000, 800000, 1000000],
                "monthly_expenses": [200000, 200000, 220000, 230000, 250000, 280000, 300000, 320000, 350000, 380000, 400000, 420000],
                "customers": [0, 5, 25, 60, 120, 200, 320, 450, 600, 780, 950, 1200],
                "burn_rate": 200000,
                "cash_runway_months": 18,
                "break_even_month": 11,
                "assumptions": "Based on ₹999 avg ARPU, 5% monthly churn, 15% MoM growth rate, ₹2,000 CAC, and ₹24,000 LTV."
            }
        }

    @staticmethod
    def _build_template_blueprint(idea: str) -> dict:
        """Return a clean structural blueprint skeleton with default empty values."""
        return {
            "scores": {
                "overall": 0, "innovation": 0, "market_demand": 0,
                "investment_potential": 0, "feasibility": 0, "scalability": 0,
                "why": ""
            },
            "executive_summary": {
                "startup_names": [],
                "tagline": "",
                "industry": "",
                "problem": "",
                "solution": idea,
                "target_customers": "",
                "estimated_budget": "",
                "why": ""
            },
            "business_model_canvas": {
                "key_partners": [], "key_activities": [], "key_resources": [],
                "value_propositions": [], "customer_relationships": [], "channels": [],
                "customer_segments": [], "cost_structure": [], "revenue_streams": [],
                "why": ""
            },
            "market_analysis": {
                "market_size": "", "growth_rate": "", "tam": "", "sam": "", "som": "",
                "trends": [], "customer_personas": [], "why": ""
            },
            "competitors": [],
            "competitive_advantage": "",
            "market_gap": "",
            "swot": {
                "strengths": [], "weaknesses": [], "opportunities": [], "threats": [], "why": ""
            },
            "budget": {
                "development": 0, "infrastructure": 0, "marketing": 0, "operations": 0,
                "hiring": 0, "legal": 0, "miscellaneous": 0, "total": 0, "why": ""
            },
            "revenue_model": {
                "recommended": "", "options": [], "why": ""
            },
            "funding": [],
            "government_schemes": [],
            "legal_checklist": [],
            "roadmap": [],
            "risks": [],
            "investor_readiness": {
                "score": 0, "funding_readiness": 0, "investment_risks": "",
                "funding_timeline": "", "pitch_score": 0, "gaps": [], "why": ""
            },
            "improvements": [],
            "startup_names": {
                "names": [], "taglines": [], "domains": []
            },
            "elevator_pitch": {
                "30_sec": "", "2_min": ""
            },
            "recommendations": [],
            "simulation": {
                "monthly_revenue": [], "monthly_expenses": [], "customers": [],
                "burn_rate": 0, "cash_runway_months": 0, "break_even_month": 0, "assumptions": ""
            }
        }


# Singleton instance
granite_service = GraniteService()
