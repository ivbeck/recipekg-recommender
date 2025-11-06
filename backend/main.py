from __future__ import annotations

import os
from flask import Flask
from dotenv import load_dotenv


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
        "FOODKG_SPARQL_ENDPOINT",
        os.getenv("FOODKG_SPARQL_ENDPOINT", "https://foodkg.rpi.edu/sparql"),
    )

    # Register blueprints
    from .routes import register_blueprints

    register_blueprints(app)

    @app.context_processor
    def inject_globals():
        return {
            "app_name": "foodkg-recommender",
            "sparql_endpoint": app.config.get("FOODKG_SPARQL_ENDPOINT"),
        }

    return app


# Provide an "app" for tools that import it directly (e.g., some IDE run configs)
app = create_app()
