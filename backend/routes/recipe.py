from __future__ import annotations

from flask import Blueprint, render_template, abort
from urllib.parse import unquote

from backend.services.recipe_detail_fetcher import fetch_recipe_details

bp = Blueprint("recipe", __name__)


@bp.route("/recipe/<path:recipe_uri>")
def detail(recipe_uri: str):
    """
    Display detailed information about a recipe.
    
    Args:
        recipe_uri: URL-encoded recipe URI
    """
    decoded_uri = unquote(recipe_uri)
    
    recipe = fetch_recipe_details(decoded_uri)
    
    if not recipe:
        abort(404, description="Recipe not found")
    
    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        title=recipe.get("name", "Recipe Details")
    )

