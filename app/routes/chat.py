"""
Chat Routes — AI Mentor chat with conversation history
"""

import json
import logging
from flask import Blueprint, request, jsonify, session

from app.services.granite_service import granite_service
from app.services.rag_service import rag_pipeline
from app.services.cos_service import cos_service
from app.services.prompt_manager import build_chat_prompt

logger = logging.getLogger(__name__)
chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/message", methods=["POST"])
def chat_message():
    """AI Mentor chat endpoint."""
    try:
        data = request.get_json(force=True)
        question = data.get("message", "").strip()
        if not question:
            return jsonify({"error": "Message is required"}), 400

        # Load blueprint from session or request body
        blueprint = data.get("blueprint", {})
        if not blueprint:
            blueprint_key = session.get("blueprint_key")
            if blueprint_key:
                blueprint = cos_service.download_json(cos_service.bucket_reports, blueprint_key) or {}
            else:
                bp_json = session.get("blueprint")
                if bp_json:
                    try:
                        blueprint = json.loads(bp_json)
                    except Exception:
                        blueprint = {}

        # Load/update conversation history
        history = data.get("history", [])
        if not history:
            history = session.get("chat_history", [])

        # RAG retrieval on the question
        rag_context = rag_pipeline.retrieve(question, k=4)

        # Build and call Granite
        system_prompt, user_prompt = build_chat_prompt(blueprint, history, question, rag_context)
        response_text = granite_service.generate(system_prompt, user_prompt, max_tokens=1024)

        # If Granite returned JSON accidentally, stringify it
        if isinstance(response_text, dict):
            response_text = json.dumps(response_text)

        # Strip any leading/trailing whitespace
        response_text = response_text.strip()

        # Update history
        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": response_text})
        # Keep last 20 messages
        history = history[-20:]
        session["chat_history"] = history

        return jsonify({
            "success": True,
            "response": response_text,
            "history": history
        })

    except Exception as e:
        logger.exception("Chat endpoint error")
        return jsonify({"error": str(e)}), 500


@chat_bp.route("/clear", methods=["POST"])
def clear_history():
    session.pop("chat_history", None)
    return jsonify({"success": True})
