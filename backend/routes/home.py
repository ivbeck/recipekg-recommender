from __future__ import annotations

from flask import Blueprint, render_template, jsonify

from backend.services import fetch_test_data

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    print(fetch_test_data())
    return render_template("index.html", title="Home")


@bp.route("/health")
def health():
    return jsonify(status="ok")
