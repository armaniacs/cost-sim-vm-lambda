"""
Main Flask application module
"""

import os

from flask import Flask
from flask_cors import CORS

from app.config import config
from app.security.env_validator import validate_environment_or_exit


def configure_cors(app: Flask) -> None:
    """
    Configure CORS with strict origin control based on environment
    PBI-SEC-ESSENTIAL implementation

    Args:
        app: Flask application instance
    """
    flask_env = app.config.get(
        "FLASK_ENV", os.environ.get("FLASK_ENV", "development")
    ).lower()

    if flask_env == "production":
        # Production: only specific domains
        origins_env = os.environ.get("CORS_ORIGINS", "")
        if origins_env:
            allowed_origins = [
                origin.strip() for origin in origins_env.split(",") if origin.strip()
            ]
        else:
            # Default production domains (should be configured via environment)
            allowed_origins = [
                "https://cost-simulator.example.com",
                "https://cost-calc.example.com",
            ]
    else:
        # Development: localhost only
        allowed_origins = ["http://localhost:5001", "http://127.0.0.1:5001"]

    # Configure CORS with security settings
    CORS(
        app,
        origins=allowed_origins,
        supports_credentials=False,  # Disable credentials for security
        max_age=3600,
    )  # Cache preflight for 1 hour


def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"

    # Content Security Policy for enhanced security
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    response.headers["Content-Security-Policy"] = csp
    return response


def create_app(config_name: str = "default") -> Flask:
    """
    Application factory pattern for creating Flask app instances

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Configured Flask application instance
    """
    # Validate security environment before creating app (PBI-SEC-ESSENTIAL)
    validate_environment_or_exit()

    app = Flask(__name__)

    # Determine configuration - explicit config_name takes precedence in tests
    if config_name == "testing":
        config_name_to_use = "testing"
    else:
        config_name_to_use = os.environ.get("FLASK_ENV") or config_name

    app.config.from_object(config.get(config_name_to_use, config["default"]))

    # Configure CORS with environment-based security (PBI-SEC-ESSENTIAL)
    configure_cors(app)

    # Add security headers to all responses
    app.after_request(add_security_headers)

    # Initialize monitoring integration
    from app.services.monitoring_integration import monitoring_integration

    monitoring_integration.init_app(app)

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
    # Determine configuration based on environment
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)

    # Get configuration from app config
    from app.config import Config

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
