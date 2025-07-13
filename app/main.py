"""
Main Flask application module
"""
from flask import Flask
from flask_cors import CORS  # type: ignore

from app.config import config


def create_app(config_name: str = "default") -> Flask:
    """
    Application factory pattern for creating Flask app instances

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Enable CORS for frontend integration
    CORS(app)

    # Register blueprints
    from app.api.calculator_api import calculator_bp

    app.register_blueprint(calculator_bp, url_prefix="/api/v1/calculator")

    # Frontend routes
    @app.route("/")
    def index() -> str:
        import time

        from flask import render_template

        return render_template("index.html", timestamp=int(time.time()))

    @app.route("/api")
    def api_info() -> dict[str, str]:
        return {"status": "ok", "message": "Cost Simulator API is running"}

    @app.route("/health")
    def health() -> dict[str, str]:
        return {"status": "healthy", "version": "0.1.0"}

    @app.route("/favicon.ico")
    def favicon() -> tuple[str, int]:
        # Return 204 No Content instead of 404
        return "", 204

    @app.route("/.well-known/appspecific/com.chrome.devtools.json")
    def chrome_devtools() -> tuple[str, int]:
        # Return 204 No Content for Chrome DevTools
        return "", 204

    # Handle other common browser requests
    @app.route("/robots.txt")
    def robots() -> tuple[str, int, dict[str, str]]:
        return "User-agent: *\nDisallow:", 200, {"Content-Type": "text/plain"}

    @app.route("/sitemap.xml")
    def sitemap() -> tuple[str, int]:
        return "", 204

    @app.route("/apple-touch-icon.png")
    @app.route("/apple-touch-icon-precomposed.png")
    def apple_touch_icon() -> tuple[str, int]:
        return "", 204

    return app


if __name__ == "__main__":
    import os

    # Determine configuration based on environment
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)

    # Get configuration from app config
    from app.config import Config

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
