"""
Resources Routes — IBM COS resource hub
"""

import logging
from flask import Blueprint, jsonify
from app.services.cos_service import cos_service

logger = logging.getLogger(__name__)
resources_bp = Blueprint("resources", __name__)


@resources_bp.route("/list", methods=["GET"])
def list_resources():
    try:
        resources = cos_service.get_resource_list()
        return jsonify({"success": True, "resources": resources})
    except Exception as e:
        logger.exception("Resources list error")
        return jsonify({"error": str(e)}), 500
