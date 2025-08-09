"""
Configuration settings for the Cost Simulator application
"""

import os
from typing import Type


class Config:
    """Base configuration"""

    TESTING = False
    DEBUG = False

    # Flask server configuration
    PORT = int(os.environ.get("PORT", 5001))
    HOST = os.environ.get("HOST", "127.0.0.1")

    # Environment detection
    FLASK_ENV = os.environ.get("FLASK_ENV", "development")

    # Default exchange rate (JPY/USD)
    DEFAULT_EXCHANGE_RATE = 150.0
    MIN_EXCHANGE_RATE = 50.0
    MAX_EXCHANGE_RATE = 300.0

    # AWS Lambda pricing (Tokyo region)
    LAMBDA_REQUEST_PRICE_PER_MILLION = 0.20
    LAMBDA_COMPUTE_PRICE_PER_GB_SECOND = 0.0000166667
    LAMBDA_FREE_TIER_REQUESTS = 1_000_000
    LAMBDA_FREE_TIER_GB_SECONDS = 400_000


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    HOST = "127.0.0.1"  # Localhost for development


class TestingConfig(Config):
    """Testing configuration"""

    TESTING = True
    DEBUG = True
    PROPAGATE_EXCEPTIONS = False  # Ensure exceptions are converted to HTTP responses


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False


config: dict[str, Type[Config]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
