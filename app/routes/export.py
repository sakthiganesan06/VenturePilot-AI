"""
Export Routes — PDF, JSON exports stored in IBM COS
"""

import os
import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, session

from app.services.pdf_service import pdf_generator
from app.services.cos_service import cos_service

logger = logging.getLogger(__name__)
export_bp = Blueprint("export", __name__)

EXPORTS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "exports"
)


@export_bp.route("/blueprint-pdf", methods=["POST"])
def export_blueprint_pdf():
    try:
        data      = request.get_json(force=True)
        blueprint = data.get("blueprint", {})
        if not blueprint:
            blueprint_key = session.get("blueprint_key")
            if blueprint_key:
                blueprint = cos_service.download_json(cos_service.bucket_reports, blueprint_key) or {}
            else:
                bp_json   = session.get("blueprint")
                blueprint = json.loads(bp_json) if bp_json else {}

        ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"blueprint_{ts}.pdf"
        filepath = pdf_generator.generate_blueprint_pdf(blueprint, filename)

        # Upload to COS
        with open(filepath, "rb") as f:
            cos_service.upload_file(cos_service.bucket_reports, f"pdfs/{filename}", f.read(), "application/pdf")

        return send_file(filepath, as_attachment=True, download_name=filename, mimetype="application/pdf")

    except Exception as e:
        logger.exception("Blueprint PDF export error")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/pitch-deck-pdf", methods=["POST"])
def export_pitch_deck():
    try:
        data      = request.get_json(force=True)
        blueprint = data.get("blueprint", {})
        if not blueprint:
            blueprint_key = session.get("blueprint_key")
            if blueprint_key:
                blueprint = cos_service.download_json(cos_service.bucket_reports, blueprint_key) or {}
            else:
                bp_json   = session.get("blueprint")
                blueprint = json.loads(bp_json) if bp_json else {}

        ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"pitch_deck_{ts}.pdf"
        filepath = pdf_generator.generate_pitch_deck_pdf(blueprint, filename)

        with open(filepath, "rb") as f:
            cos_service.upload_file(cos_service.bucket_reports, f"pdfs/{filename}", f.read(), "application/pdf")

        return send_file(filepath, as_attachment=True, download_name=filename, mimetype="application/pdf")

    except Exception as e:
        logger.exception("Pitch deck PDF export error")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/json", methods=["POST"])
def export_json():
    try:
        data      = request.get_json(force=True)
        blueprint = data.get("blueprint", {})
        if not blueprint:
            blueprint_key = session.get("blueprint_key")
            if blueprint_key:
                blueprint = cos_service.download_json(cos_service.bucket_reports, blueprint_key) or {}
            else:
                bp_json   = session.get("blueprint")
                blueprint = json.loads(bp_json) if bp_json else {}

        ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"blueprint_{ts}.json"
        filepath = os.path.join(EXPORTS_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(blueprint, f, indent=2, ensure_ascii=False)

        cos_service.upload_json(cos_service.bucket_reports, f"json/{filename}", blueprint)
        return send_file(filepath, as_attachment=True, download_name=filename, mimetype="application/json")

    except Exception as e:
        logger.exception("JSON export error")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/download/<path:filename>")
def download_file(filename):
    """Fallback download for files stored locally."""
    try:
        filepath = os.path.join(EXPORTS_DIR, filename)
        if os.path.exists(filepath):
            return send_file(filepath, as_attachment=True)
        return jsonify({"error": "File not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
