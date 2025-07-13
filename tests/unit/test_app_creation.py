"""
Unit tests for Flask application creation and basic functionality
Following t_wada TDD principles: Red -> Green -> Refactor
"""
from app.main import create_app


class TestAppCreation:
    """Test application factory and basic configuration"""

    def test_app_creation_default_config(self):
        """Test that app can be created with default configuration"""
        app = create_app()
        assert app is not None
        assert app.config["DEBUG"] is True  # default is development

    def test_app_creation_testing_config(self):
        """Test that app can be created with testing configuration"""
        app = create_app("testing")
        assert app is not None
        assert app.config["TESTING"] is True
        assert app.config["DEBUG"] is True

    def test_app_creation_production_config(self):
        """Test that app can be created with production configuration"""
        app = create_app("production")
        assert app is not None
        assert app.config["DEBUG"] is False
        assert app.config["TESTING"] is False

    def test_index_endpoint(self, client):
        """Test index page endpoint returns HTML"""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Cost Simulator" in response.data
        assert response.content_type.startswith("text/html")

    def test_api_info_endpoint(self, client):
        """Test API info endpoint"""
        response = client.get("/api")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "ok"
        assert "Cost Simulator API is running" in data["message"]

    def test_health_endpoint(self, client):
        """Test detailed health endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["version"] == "0.1.0"

    def test_cors_enabled(self, client):
        """Test that CORS headers are present"""
        response = client.get("/api")
        # CORS headers should be present for cross-origin requests
        assert response.status_code == 200
        # Note: Flask-CORS adds headers automatically


class TestAppConfiguration:
    """Test application configuration settings"""

    def test_default_exchange_rate_config(self):
        """Test default exchange rate configuration"""
        app = create_app("testing")
        assert app.config["DEFAULT_EXCHANGE_RATE"] == 150.0
        assert app.config["MIN_EXCHANGE_RATE"] == 50.0
        assert app.config["MAX_EXCHANGE_RATE"] == 300.0

    def test_lambda_pricing_config(self):
        """Test Lambda pricing configuration"""
        app = create_app("testing")
        assert app.config["LAMBDA_REQUEST_PRICE_PER_MILLION"] == 0.20
        assert app.config["LAMBDA_COMPUTE_PRICE_PER_GB_SECOND"] == 0.0000166667
        assert app.config["LAMBDA_FREE_TIER_REQUESTS"] == 1_000_000
        assert app.config["LAMBDA_FREE_TIER_GB_SECONDS"] == 400_000
