"""
AI Startup Blueprint Generator - Flask Application Factory
IBM watsonx.ai (Granite) + RAG + IBM Cloud Object Storage
"""

from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS
import logging
import os
from logging.handlers import RotatingFileHandler


def create_app(config_name=None):
    app = Flask(__name__)

    # ── Configuration ──────────────────────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ── Logging ────────────────────────────────────────────────────────────────
    _setup_logging(app)

    # ── Register Blueprints ────────────────────────────────────────────────────
    from app.routes.main import main_bp
    from app.routes.api import api_bp
    from app.routes.chat import chat_bp
    from app.routes.export import export_bp
    from app.routes.resources import resources_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp,       url_prefix='/api')
    app.register_blueprint(chat_bp,      url_prefix='/api/chat')
    app.register_blueprint(export_bp,    url_prefix='/api/export')
    app.register_blueprint(resources_bp, url_prefix='/api/resources')

    app.logger.info("✅ VenturPilot AI started successfully")
    return app


def _setup_logging(app: Flask):
    log_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    handler = RotatingFileHandler(
        os.path.join(log_dir, 'app.log'),
        maxBytes=10_000_000,
        backupCount=5
    )
    handler.setFormatter(logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    ))
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
