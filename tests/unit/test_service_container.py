"""
Unit tests for service container
Tests the dependency injection container functionality
"""
import pytest
from unittest.mock import patch, mock_open
import json

from app.services.service_container import (
    ServiceContainer,
    get_container,
    register_services,
    get_lambda_calculator,
    get_vm_calculator,
    get_serverless_calculator,
    get_egress_calculator
)


class TestServiceContainer:
    """Test the ServiceContainer class"""
    
    def test_container_initialization(self):
        """Test container initializes with empty services"""
        container = ServiceContainer()
        assert container._services == {}
        assert container._singletons == {}
        assert container._pricing_configs == {}
    
    def test_register_singleton(self):
        """Test singleton registration"""
        container = ServiceContainer()
        service_instance = "test_service"
        container.register_singleton("test", service_instance)
        assert container._singletons["test"] == service_instance
    
    def test_register_service(self):
        """Test service class registration"""
        container = ServiceContainer()
        container.register_service("test", dict)
        assert container._services["test"] == dict
    
    def test_get_singleton_service(self):
        """Test getting a singleton service"""
        container = ServiceContainer()
        service_instance = {"key": "value"}
        container.register_singleton("test", service_instance)
        
        result = container.get_service("test")
        assert result == service_instance
    
    def test_get_registered_service(self):
        """Test getting a service from registered class"""
        container = ServiceContainer()
        container.register_service("list", list)
        
        result = container.get_service("list", [1, 2, 3])
        assert isinstance(result, list)
        assert result == [1, 2, 3]
    
    def test_get_service_not_registered(self):
        """Test error when service not registered"""
        container = ServiceContainer()
        
        with pytest.raises(ValueError, match="Service 'unknown' not registered"):
            container.get_service("unknown")
    
    @patch("builtins.open", mock_open(read_data='{"test_provider": {"price": 0.5}}'))
    def test_get_pricing_config_success(self):
        """Test successful pricing config loading"""
        container = ServiceContainer()
        
        config = container.get_pricing_config("test")
        assert config == {"test_provider": {"price": 0.5}}
        assert container._pricing_configs["test"] == {"test_provider": {"price": 0.5}}
    
    @patch("builtins.open", side_effect=FileNotFoundError())
    def test_get_pricing_config_file_not_found(self, mock_file):
        """Test pricing config when file not found"""
        container = ServiceContainer()
        
        with pytest.raises(ValueError, match="Failed to load pricing config"):
            container.get_pricing_config("nonexistent")
    
    @patch("builtins.open", mock_open(read_data='invalid json'))
    def test_get_pricing_config_invalid_json(self):
        """Test pricing config with invalid JSON"""
        container = ServiceContainer()
        
        with pytest.raises(ValueError, match="Failed to load pricing config"):
            container.get_pricing_config("invalid")
    
    def test_get_pricing_config_cached(self):
        """Test pricing config caching"""
        container = ServiceContainer()
        test_config = {"cached": True}
        container._pricing_configs["test"] = test_config
        
        result = container.get_pricing_config("test")
        assert result == test_config


class TestGlobalFunctions:
    """Test global container functions"""
    
    def test_get_container(self):
        """Test getting global container"""
        container = get_container()
        assert isinstance(container, ServiceContainer)
    
    def test_register_services(self):
        """Test services registration"""
        # This should not raise an error
        register_services()
        
        container = get_container()
        assert "lambda_calculator" in container._services
        assert "vm_calculator" in container._services
        assert "serverless_calculator" in container._services
        assert "egress_calculator" in container._services
    
    @patch("app.services.service_container.get_container")
    def test_get_lambda_calculator_with_config(self, mock_get_container):
        """Test getting lambda calculator with custom config"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        # Mock service
        mock_calculator = "mock_calculator"
        mock_container.register_service("lambda_calculator", lambda pricing_config=None: mock_calculator)
        
        config = {"price": 0.1}
        result = get_lambda_calculator(config)
        assert result == mock_calculator
    
    @patch("app.services.service_container.get_container")
    @patch("app.services.service_container.ServiceContainer.get_pricing_config")
    def test_get_lambda_calculator_default_config(self, mock_get_pricing, mock_get_container):
        """Test getting lambda calculator with default config"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        mock_get_pricing.return_value = {"aws_lambda": {"price": 0.2}}
        
        # Mock service
        mock_calculator = "mock_calculator"
        mock_container.register_service("lambda_calculator", lambda pricing_config=None: mock_calculator)
        
        result = get_lambda_calculator()
        assert result == mock_calculator
        mock_get_pricing.assert_called_once_with("lambda")
    
    @patch("app.services.service_container.get_container")
    @patch("app.services.service_container.ServiceContainer.get_pricing_config", side_effect=ValueError())
    def test_get_lambda_calculator_fallback(self, mock_get_pricing, mock_get_container):
        """Test lambda calculator fallback when config fails"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        # Mock service
        mock_calculator = "mock_calculator"
        mock_container.register_service("lambda_calculator", lambda: mock_calculator)
        
        result = get_lambda_calculator()
        assert result == mock_calculator
    
    @patch("app.services.service_container.get_container")
    def test_get_vm_calculator(self, mock_get_container):
        """Test getting VM calculator"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        mock_calculator = "mock_vm_calculator"
        mock_container.register_service("vm_calculator", lambda: mock_calculator)
        
        result = get_vm_calculator()
        assert result == mock_calculator
    
    @patch("app.services.service_container.get_container")
    def test_get_serverless_calculator(self, mock_get_container):
        """Test getting serverless calculator"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        mock_calculator = "mock_serverless_calculator"
        mock_container.register_service("serverless_calculator", lambda: mock_calculator)
        
        result = get_serverless_calculator()
        assert result == mock_calculator
    
    @patch("app.services.service_container.get_container")
    def test_get_egress_calculator_with_custom_rates(self, mock_get_container):
        """Test getting egress calculator with custom rates"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        mock_calculator = "mock_egress_calculator"
        mock_container.register_service("egress_calculator", lambda custom_rates=None: mock_calculator)
        
        custom_rates = {"aws": 0.1}
        result = get_egress_calculator(custom_rates)
        assert result == mock_calculator
    
    @patch("app.services.service_container.get_container")
    def test_get_egress_calculator_default(self, mock_get_container):
        """Test getting egress calculator with defaults"""
        mock_container = ServiceContainer()
        mock_get_container.return_value = mock_container
        
        mock_calculator = "mock_egress_calculator"
        mock_container.register_service("egress_calculator", lambda: mock_calculator)
        
        result = get_egress_calculator()
        assert result == mock_calculator