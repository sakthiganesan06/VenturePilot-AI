from app.services.prompt_manager import build_blueprint_prompt
from app.services.rag_service import rag_pipeline

data = {
    "idea": "An AI-powered smart agriculture drone system for pesticide spraying and soil health monitoring in India.",
    "industry": "AgriTech",
    "stage": "Idea",
    "target_customers": "Indian farmers and cooperatives",
    "country": "India",
    "budget": "₹5L - ₹25L",
    "team_size": "2 co-founders",
    "goals": "Deploy 10 drones in 3 villages in 6 months",
    "existing_product": "None"
}

query = f"{data.get('idea','')} {data.get('industry','')} {data.get('country','India')} startup"
rag_context = rag_pipeline.retrieve(query, k=6)
system_prompt, user_prompt = build_blueprint_prompt(data, rag_context)

print("--- USER PROMPT START ---")
print(user_prompt)
print("--- USER PROMPT END ---")
