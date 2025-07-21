"""
Main Flask application module
"""
import os

from flask import Flask
from flask_cors import CORS  # type: ignore

from app.config import config
from app.security.env_validator import validate_environment_or_exit
from app.auth.jwt_auth import JWTAuth


def create_app(config_name: str = "default") -> Flask:
    """
    Application factory pattern for creating Flask app instances

    Args:
        config_name: Configuration name ('development', 'testing', 'production')

    Returns:
        Configured Flask application instance
    """
    # Validate security environment before creating app
    validate_environment_or_exit()
    
    app = Flask(__name__)

    # Determine configuration
    config_name_to_use = os.environ.get("FLASK_ENV") or config_name
    app.config.from_object(config.get(config_name_to_use, config["default"]))

    # Initialize JWT authentication system
    jwt_auth = JWTAuth()
    jwt_auth.init_app(app)

    # Enable secure CORS for frontend integration
    allowed_origins = os.environ.get('CORS_ORIGINS', 'http://localhost:5001,http://127.0.0.1:5001').split(',')
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    CORS(app, origins=allowed_origins, supports_credentials=True)

    # Register blueprints
    from app.api.calculator_api import calculator_bp
    from app.api.auth_api import auth_bp

    app.register_blueprint(calculator_bp, url_prefix="/api/v1/calculator")
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")

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

    # Authentication error handlers
    @app.errorhandler(401)
    def unauthorized_handler(error):
        """Handle authentication failures"""
        from flask import jsonify
        return jsonify({
            "success": False,
            "error": "Unauthorized",
            "message": "Authentication required. Please provide valid credentials."
        }), 401

    @app.errorhandler(403)
    def forbidden_handler(error):
        """Handle authorization failures"""
        from flask import jsonify
        return jsonify({
            "success": False,
            "error": "Forbidden", 
            "message": "Insufficient permissions to access this resource."
        }), 403

    return app


if __name__ == "__main__":
    # Validate security environment before starting
    validate_environment_or_exit()
    
    # Determine configuration based on environment
    env = os.environ.get("FLASK_ENV", "development")
    app = create_app(env)

    # Get configuration from app config
    from app.config import Config

    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
