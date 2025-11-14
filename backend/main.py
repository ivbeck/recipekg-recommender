from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from flask import Flask


load_dotenv()
log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)
if not isinstance(log_level, int):
    log_level = logging.INFO


logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    force=True
)

from backend.services import get_ingredient_list

INGREDIENTS = get_ingredient_list()


def create_app() -> Flask:

    app = Flask(
        __name__.split(".")[0],
        static_folder="static",
        template_folder="templates",
    )

    
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



app = create_app()
