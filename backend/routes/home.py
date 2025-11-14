from __future__ import annotations

from typing import List

from flask import Blueprint, render_template, jsonify, request

from backend.main import INGREDIENTS
from backend.services import fetch_recipes_by_ingredients, get_matched_ingredients_only, match_ingredients

bp = Blueprint("home", __name__)


def _parse_ingredients(arg: str | None) -> List[str]:
    if not arg:
        return []
    items = [part.strip() for part in arg.split(",")]
    # items = [i.title() for i in items if i]

    return list(set(items))


@bp.route("/")
def index():
    input_ingredients = _parse_ingredients(request.args.get("ingredients"))
    
    ingredient_matches = match_ingredients(
        input_ingredients, 
        INGREDIENTS, 
        cutoff=0.6, 
        high_similarity_threshold=0.8,
        max_matches=2
    ) if input_ingredients else []
    
    ingredient_groups = [matched_list for _, matched_list in ingredient_matches if matched_list]
    
    matched_ingredients = []
    for matched_list in ingredient_groups:
        matched_ingredients.extend(matched_list)
    
    recipes = fetch_recipes_by_ingredients(ingredient_groups) if ingredient_groups else None
    
    return render_template(
        "index.html",
        title="Home",
        ingredients_query=",".join(input_ingredients),
        recipes=recipes,
        ingredient_groups=", ".join(["[" + ",".join(x) + "]" for x in ingredient_groups])
    )


@bp.route("/health")
def health():
    return jsonify(status="ok")
