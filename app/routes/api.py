"""
API Routes — Blueprint generation, dashboard data, AI features
"""

import json
import uuid
import logging
from flask import Blueprint, request, jsonify, session

from app.services.granite_service import granite_service
from app.services.rag_service import rag_pipeline
from app.services.cos_service import cos_service
from app.services.prompt_manager import (
    build_blueprint_prompt, build_improve_prompt, build_names_prompt
)

logger = logging.getLogger(__name__)
api_bp = Blueprint("api", __name__)


def _deep_merge(base: dict, override: dict) -> dict:
    """Merge override into base in-place. Override values win; base fills missing keys."""
    for key, val in override.items():
        if val is None:
            continue
        if isinstance(val, dict) and isinstance(base.get(key), dict):
            _deep_merge(base[key], val)
        elif isinstance(val, list) and len(val) > 0:
            base[key] = val  # replace lists wholesale when Granite provides them
        elif isinstance(val, (str, int, float, bool)) and val not in ("", "<reasoning>", "<placeholder>"):
            base[key] = val
    return base


@api_bp.route("/generate", methods=["POST"])
def generate_blueprint():
    """Main endpoint: receives form data → RAG → Granite → returns blueprint JSON."""
    try:
        data = request.get_json(force=True)
        if not data or not data.get("idea"):
            return jsonify({"error": "Startup idea is required"}), 400

        # Build RAG query
        query = f"{data.get('idea','')} {data.get('industry','')} {data.get('country','India')} startup"
        rag_context = rag_pipeline.retrieve(query, k=6)

        # Build prompts and call Granite
        system_prompt, user_prompt = build_blueprint_prompt(data, rag_context)
        granite_result = granite_service.generate_json(system_prompt, user_prompt)

        if not granite_result:
            return jsonify({"error": "AI Generation Failed: Watsonx AI was unable to generate a valid response. Please check your credentials in your `.env` file."}), 500

        # Always start from clean template so every field is populated
        blueprint = granite_service._build_template_blueprint(data.get("idea", ""))

        # Deep-merge Granite result on top — real AI data wins
        _deep_merge(blueprint, granite_result)

        # Generate session ID and persist to COS
        session_id = str(uuid.uuid4())[:8]
        blueprint["_session_id"] = session_id
        blueprint["_form_data"] = data
        key = cos_service.save_blueprint(session_id, blueprint)

        # Store key in session for chat/improve fallback (prevents cookie overflow)
        session["blueprint_key"] = key
        session["session_id"] = session_id

        return jsonify({"success": True, "blueprint": blueprint, "session_id": session_id})

    except Exception as e:
        logger.exception("Blueprint generation error")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/improve", methods=["POST"])
def improve_idea():
    """Startup Idea Improver endpoint."""
    try:
        data = request.get_json(force=True)
        blueprint = data.get("blueprint", {})
        if not blueprint:
            blueprint_key = session.get("blueprint_key")
            if blueprint_key:
                blueprint = cos_service.download_json(cos_service.bucket_reports, blueprint_key) or {}
            else:
                bp_json = session.get("blueprint")
                blueprint = json.loads(bp_json) if bp_json else {}

        query = blueprint.get("executive_summary", {}).get("solution", "startup improvement")
        rag_context = rag_pipeline.retrieve(query, k=4)
        system_prompt, user_prompt = build_improve_prompt(blueprint, rag_context)
        result = granite_service.generate_json(system_prompt, user_prompt)

        improvements = result.get("improvements", blueprint.get("improvements", []))
        return jsonify({"success": True, "improvements": improvements})

    except Exception as e:
        logger.exception("Improve endpoint error")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/names", methods=["POST"])
def generate_names():
    """Startup Name Generator endpoint."""
    try:
        data = request.get_json(force=True)
        idea     = data.get("idea", "")
        industry = data.get("industry", "")
        system_prompt, user_prompt = build_names_prompt(idea, industry)
        result = granite_service.generate_json(system_prompt, user_prompt)
        return jsonify({"success": True, "data": result})
    except Exception as e:
        logger.exception("Names endpoint error")
        return jsonify({"error": str(e)}), 500


@api_bp.route("/schemes", methods=["GET"])
def get_schemes():
    """Return government schemes with RAG context."""
    query = request.args.get("q", "Indian government startup schemes DPIIT MSME")
    context = rag_pipeline.retrieve(query, k=4)
    return jsonify({"success": True, "context": context})


@api_bp.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "granite": granite_service.model is not None,
        "rag": rag_pipeline._docs_loaded,
        "cos": cos_service.client is not None
    })
