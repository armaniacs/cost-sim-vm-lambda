"""
Pytest configuration and fixtures
"""
import pytest

from app.main import create_app


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app("testing")
    return app


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


# Sample data fixtures for testing
@pytest.fixture
def sample_lambda_config():
    """Sample Lambda configuration for testing"""
    return {
        "memory_mb": 512,
        "execution_time_seconds": 10,
        "monthly_executions": 1_000_000,
        "include_free_tier": True,
    }


@pytest.fixture
def sample_ec2_config():
    """Sample EC2 configuration for testing"""
    return {
        "provider": "aws_ec2",
        "instance_type": "t3.small",
        "region": "ap-northeast-1",
    }


@pytest.fixture
def sample_sakura_config():
    """Sample Sakura Cloud configuration for testing"""
    return {
        "provider": "sakura_cloud",
        "instance_type": "2core_4gb",
        "region": "tokyo",
    }
