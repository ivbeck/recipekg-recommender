from __future__ import annotations

from flask import Blueprint, render_template, jsonify

bp = Blueprint("home", __name__)


@bp.route("/")
def index():
    return render_template("index.html", title="Home")


@bp.route("/health")
def health():
    return jsonify(status="ok")
