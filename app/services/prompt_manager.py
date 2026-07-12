"""
Prompt Manager — builds optimized Granite prompts with RAG context
Designed for ibm/granite-8b-code-instruct (Sydney region)
"""

import json
from app.agent_instructions import get_system_prompt, AGENT_INSTRUCTIONS


def _idea_block(form_data: dict) -> str:
    return f"""Startup Idea: {form_data.get('idea', '')}
Industry: {form_data.get('industry', '')}
Stage: {form_data.get('stage', '')}
Target Customers: {form_data.get('target_customers', '')}
Country: {form_data.get('country', 'India')}
Budget: {form_data.get('budget', '')}
Team Size: {form_data.get('team_size', '')}
Goals: {form_data.get('goals', '')}
Existing Product: {form_data.get('existing_product', 'None')}"""


def build_blueprint_prompt(form_data: dict, rag_context: str) -> tuple[str, str]:
    """
    Single-call blueprint prompt — compact enough for granite-8b-code-instruct.
    Returns (system_prompt, user_prompt).
    """
    system = (
        f"You are an {AGENT_INSTRUCTIONS['ai_personality']}. "
        f"Ecosystem: {AGENT_INSTRUCTIONS['ecosystem_preference']}. "
        "IMPORTANT: Your response must start with '{' and end with '}'. "
        "Output ONLY raw JSON. No introduction, no explanation, no markdown, no code fences. "
        "Start your response immediately with the opening brace '{'."
    )

    idea = _idea_block(form_data)
    country = form_data.get('country', 'India')
    currency = "INR" if country == "India" else "USD"

    user = f"""Analyse this startup and return a JSON blueprint.

{idea}

Context: {rag_context[:800]}

Return this exact JSON structure (fill every field with real analysis, not placeholders):
{{
  "scores": {{"overall": <int 0-100>, "innovation": <int>, "market_demand": <int>, "investment_potential": <int>, "feasibility": <int>, "scalability": <int>, "why": "<reasoning>"}},
  "executive_summary": {{"startup_names": ["Name1","Name2","Name3"], "tagline": "<tagline>", "industry": "<industry>", "problem": "<problem>", "solution": "<solution>", "target_customers": "<customers>", "estimated_budget": "<budget in {currency}>", "why": "<reasoning>"}},
  "business_model_canvas": {{"key_partners": ["<p1>","<p2>"], "key_activities": ["<a1>","<a2>"], "key_resources": ["<r1>","<r2>"], "value_propositions": ["<v1>","<v2>"], "customer_relationships": ["<cr1>"], "channels": ["<ch1>","<ch2>"], "customer_segments": ["<cs1>"], "cost_structure": ["<c1>","<c2>"], "revenue_streams": ["<rs1>"], "why": "<reasoning>"}},
  "market_analysis": {{"market_size": "<size>", "growth_rate": "<rate>", "tam": "<tam>", "sam": "<sam>", "som": "<som>", "trends": ["<t1>","<t2>","<t3>"], "customer_personas": [{{"name": "<name>", "age": <int>, "pain": "<pain>", "willingness_to_pay": "<wtp>"}}], "why": "<reasoning>"}},
  "competitors": [{{"name": "<name>", "pricing": "<price>", "strengths": ["<s1>"], "weaknesses": ["<w1>"], "market_share": <int>}},{{"name": "Our Product", "pricing": "<price>", "strengths": ["<s1>","<s2>"], "weaknesses": ["<w1>"], "market_share": 0}}],
  "competitive_advantage": "<advantage>",
  "market_gap": "<gap>",
  "swot": {{"strengths": ["<s1>","<s2>"], "weaknesses": ["<w1>","<w2>"], "opportunities": ["<o1>","<o2>"], "threats": ["<t1>","<t2>"], "why": "<reasoning>"}},
  "budget": {{"development": <int>, "infrastructure": <int>, "marketing": <int>, "operations": <int>, "hiring": <int>, "legal": <int>, "miscellaneous": <int>, "total": <int>, "why": "<reasoning>"}},
  "revenue_model": {{"recommended": "<model>", "options": [{{"model": "<m1>", "score": <int>, "mrr_potential": "<mrr>", "recommended": true}},{{"model": "<m2>", "score": <int>, "mrr_potential": "<mrr>", "recommended": false}}], "why": "<reasoning>"}},
  "funding": [{{"type": "<type>", "amount": "<amount>", "stage": "<stage>", "eligibility": "<eligibility>", "advantage": "<advantage>", "challenge": "<challenge>"}},{{"type": "<type>", "amount": "<amount>", "stage": "<stage>", "eligibility": "<eligibility>", "advantage": "<advantage>", "challenge": "<challenge>"}}],
  "government_schemes": [{{"name": "<name>", "ministry": "<ministry>", "benefit": "<benefit>", "eligibility": "<eligibility>", "docs": ["<d1>","<d2>"]}}],
  "legal_checklist": [{{"item": "<item>", "priority": "Critical", "estimated_cost": "<cost>", "timeline": "<time>"}},{{"item": "<item>", "priority": "High", "estimated_cost": "<cost>", "timeline": "<time>"}},{{"item": "<item>", "priority": "Medium", "estimated_cost": "<cost>", "timeline": "<time>"}}],
  "roadmap": [{{"phase": "MVP", "duration": "Month 1-3", "tasks": ["<t1>","<t2>"], "milestone": "<milestone>"}},{{"phase": "Launch", "duration": "Month 4-6", "tasks": ["<t1>","<t2>"], "milestone": "<milestone>"}},{{"phase": "Scale", "duration": "Month 7-18", "tasks": ["<t1>","<t2>"], "milestone": "<milestone>"}}],
  "risks": [{{"category": "Technical", "risk": "<risk>", "level": "Medium", "probability": <int>, "mitigation": "<mitigation>"}},{{"category": "Financial", "risk": "<risk>", "level": "High", "probability": <int>, "mitigation": "<mitigation>"}},{{"category": "Market", "risk": "<risk>", "level": "High", "probability": <int>, "mitigation": "<mitigation>"}}],
  "investor_readiness": {{"score": <int>, "funding_readiness": <int>, "investment_risks": "<level>", "funding_timeline": "<timeline>", "pitch_score": <int>, "gaps": ["<g1>","<g2>"], "why": "<reasoning>"}},
  "improvements": [{{"area": "<area>", "current": "<current>", "improved": "<improved>", "impact": "High"}},{{"area": "<area>", "current": "<current>", "improved": "<improved>", "impact": "Very High"}}],
  "startup_names": {{"names": ["<n1>","<n2>","<n3>"], "taglines": ["<t1>","<t2>","<t3>"], "domains": ["<d1>","<d2>","<d3>"]}},
  "elevator_pitch": {{"30_sec": "<30 second pitch>", "2_min": "<2 minute pitch>"}},
  "recommendations": [{{"title": "<title>", "impact": "Very High", "effort": "Low", "detail": "<detail>"}},{{"title": "<title>", "impact": "High", "effort": "Medium", "detail": "<detail>"}},{{"title": "<title>", "impact": "High", "effort": "Low", "detail": "<detail>"}}],
  "simulation": {{"monthly_revenue": [0,0,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>], "monthly_expenses": [<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>], "customers": [0,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>,<int>], "burn_rate": <int>, "cash_runway_months": <int>, "break_even_month": <int>, "assumptions": "<assumptions>"}}
}}

Evaluate each score category independently and predict realistic, varied, and distinct integer scores (0-100) based on the startup details. Do not use the same score for all categories. Replace every <placeholder> with real analysis specific to the startup idea above. Use {currency} currency. Return ONLY the JSON, nothing else."""

    return system, user


def build_chat_prompt(blueprint: dict, history: list, question: str, rag_context: str) -> tuple[str, str]:
    """Return (system_prompt, user_prompt) for AI mentor chat."""
    system = (
        f"You are an {AGENT_INSTRUCTIONS['mentor_personality']}. "
        "You know the founder's startup blueprint. Answer questions concisely and actionably. "
        "Respond in plain text, not JSON."
    )

    history_str = ""
    for msg in history[-6:]:
        role = "Founder" if msg.get("role") == "user" else "Mentor"
        history_str += f"{role}: {msg.get('content', '')}\n"

    summary = {
        "idea": blueprint.get("executive_summary", {}).get("solution", ""),
        "industry": blueprint.get("executive_summary", {}).get("industry", ""),
        "overall_score": blueprint.get("scores", {}).get("overall", 0),
        "revenue_model": blueprint.get("revenue_model", {}).get("recommended", ""),
        "total_budget": blueprint.get("budget", {}).get("total", 0),
    }

    user = f"""Startup Blueprint Summary: {json.dumps(summary)}

Knowledge Context: {rag_context[:400]}

Conversation:
{history_str}
Founder: {question}
Mentor:"""

    return system, user


def build_improve_prompt(blueprint: dict, rag_context: str) -> tuple[str, str]:
    system = "You are a startup improvement expert. Respond ONLY with valid JSON."
    user = f"""Suggest 5 improvements for this startup:
Solution: {blueprint.get('executive_summary', {}).get('solution', '')}
Industry: {blueprint.get('executive_summary', {}).get('industry', '')}
Score: {blueprint.get('scores', {}).get('overall', 0)}/100
Weaknesses: {blueprint.get('swot', {}).get('weaknesses', [])}

Return JSON: {{"improvements": [{{"area": "<area>", "current": "<current state>", "improved": "<improved version>", "impact": "High"}}]}}"""
    return system, user


def build_names_prompt(idea: str, industry: str) -> tuple[str, str]:
    system = "You are a startup branding expert. Respond ONLY with valid JSON."
    user = f"""Generate startup names for:
Idea: {idea}
Industry: {industry}

Return JSON: {{"names": ["Name1","Name2","Name3","Name4","Name5","Name6","Name7","Name8","Name9","Name10"], "taglines": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"], "domains": ["domain1.ai","domain2.io","domain3.in","domain4.com","domain5.ai","domain6.io","domain7.in","domain8.com"], "reasoning": "<why these names work>"}}"""
    return system, user
