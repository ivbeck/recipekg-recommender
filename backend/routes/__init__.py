

from __future__ import annotations

from flask import Flask


def register_blueprints(app: Flask) -> None:
    """Register all blueprints for the application."""
    
    from .home import bp as home_bp
    from .recipe import bp as recipe_bp

    app.register_blueprint(home_bp)
    app.register_blueprint(recipe_bp)
