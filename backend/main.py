from __future__ import annotations

import os

from dotenv import load_dotenv
from flask import Flask

from backend.services import get_ingredient_list

INGREDIENTS = get_ingredient_list()


def create_app() -> Flask:
    load_dotenv()

    app = Flask(
        __name__.split(".")[0],
        static_folder="static",
        template_folder="templates",
    )

    # Basic config
    app.config.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "dev-secret-key"))
    app.config.setdefault(
        "SPARQL_ENDPOINT",
        os.getenv("SPARQL_ENDPOINT", "http://localhost:3030/recipes/sparql"),
    )

    # Register blueprints
    from .routes import register_blueprints

    register_blueprints(app)

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "foodkg-recommender",
            "sparql_endpoint": app.config.get("SPARQL_ENDPOINT"),
            "possible_ingredients": INGREDIENTS,
        }

    return app


# Provide an "app" for tools that import it directly (e.g., some IDE run configs)
app = create_app()
