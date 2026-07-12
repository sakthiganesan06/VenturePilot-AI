"""
Main Routes — page renders
"""
from flask import Blueprint, render_template, redirect, url_for

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/generate")
def generate():
    return render_template("generate.html")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@main_bp.route("/resources")
def resources():
    return render_template("resources.html")


@main_bp.route("/export")
def export_center():
    return render_template("export.html")
