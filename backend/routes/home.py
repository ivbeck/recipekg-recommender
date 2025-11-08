from __future__ import annotations

from typing import List

from flask import Blueprint, render_template, jsonify, request

from backend.services import fetch_recipes_by_ingredients

bp = Blueprint("home", __name__)


def _parse_ingredients(arg: str | None) -> List[str]:
    if not arg:
        return []
    items = [part.strip() for part in arg.split(",")]
    # items = [i.title() for i in items if i]

    return list(set(items))


@bp.route("/")
def index():
    ingredients = _parse_ingredients(request.args.get("ingredients"))
    recipes = fetch_recipes_by_ingredients(ingredients) if ingredients else None
    return render_template("index.html", title="Home", ingredients_query=",".join(ingredients), recipes=recipes)


@bp.route("/api/recipes")
def recipes():
    ingredients = _parse_ingredients(request.args.get("ingredients"))
    data = fetch_recipes_by_ingredients(ingredients) if ingredients else {"results": {"bindings": []}}
    bindings = data.get("results", {}).get("bindings", [])
    clean = [
        {
            "uri": r["recipe"]["value"],
            "name": r["name"]["value"].replace("\"", ""),
            "usdascore": r["usdascore"]["value"],
            "calAmount": r["calAmount"]["value"],
        }
        for r in bindings
        if "recipe" in r and "name" in r
    ]
    return jsonify(ingredients=ingredients, recipes=clean)


@bp.route("/health")
def health():
    return jsonify(status="ok")
