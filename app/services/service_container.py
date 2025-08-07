"""
Service container for dependency injection
Resolves circular import issues and provides centralized service management
"""
from typing import Any, Dict, Optional, TypeVar, Type
import json
import os

T = TypeVar('T')


class ServiceContainer:
    """Dependency injection container for managing services and their dependencies"""
    
    def __init__(self) -> None:
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._pricing_configs: Dict[str, Any] = {}
        
    def register_singleton(self, service_name: str, service_instance: Any) -> None:
        """Register a singleton service instance"""
        self._singletons[service_name] = service_instance
        
    def register_service(self, service_name: str, service_class: Type[T]) -> None:
        """Register a service class for lazy instantiation"""
        self._services[service_name] = service_class
        
    def get_service(self, service_name: str, **kwargs: Any) -> Any:
        """Get a service instance, creating it if necessary"""
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
            
        # Create new instance from registered class
        if service_name in self._services:
            service_class = self._services[service_name]
            instance = service_class(**kwargs)
            return instance
            
        raise ValueError(f"Service '{service_name}' not registered")
    
    def get_pricing_config(self, provider: str) -> Dict[str, Any]:
        """Get pricing configuration for a specific provider"""
        if provider in self._pricing_configs:
            return self._pricing_configs[provider]
            
        # Load pricing config from file
        config_file = f"{provider}_pricing.json"
        config_path = os.path.join(
            os.path.dirname(__file__), 
            "..", 
            "pricing_config", 
            config_file
        )
        
        try:
            with open(config_path, "r") as f:
                config_data = json.load(f)
                # Cache the loaded config
                self._pricing_configs[provider] = config_data
                return config_data
        except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
            raise ValueError(f"Failed to load pricing config for {provider}: {e}")


# Global service container instance
_container = ServiceContainer()


def get_container() -> ServiceContainer:
    """Get the global service container instance"""
    return _container


def register_services() -> None:
    """Register all application services with the container"""
    from app.models.lambda_calculator import LambdaCalculator
    from app.models.vm_calculator import VMCalculator
    from app.models.serverless_calculator import ServerlessCalculator
    from app.models.egress_calculator import EgressCalculator
    
    # Register services for lazy instantiation
    _container.register_service("lambda_calculator", LambdaCalculator)
    _container.register_service("vm_calculator", VMCalculator)
    _container.register_service("serverless_calculator", ServerlessCalculator)
    _container.register_service("egress_calculator", EgressCalculator)


def get_lambda_calculator(pricing_config: Optional[Dict[str, Any]] = None) -> Any:
    """Get a Lambda calculator instance with optional custom pricing config"""
    if pricing_config:
        return _container.get_service("lambda_calculator", pricing_config=pricing_config)
    else:
        # Load default pricing config
        try:
            config = _container.get_pricing_config("lambda")
            lambda_config = config.get("aws_lambda", {})
            return _container.get_service("lambda_calculator", pricing_config=lambda_config)
        except ValueError:
            # Fallback to default constructor
            return _container.get_service("lambda_calculator")


def get_vm_calculator() -> Any:
    """Get a VM calculator instance"""
    return _container.get_service("vm_calculator")


def get_serverless_calculator() -> Any:
    """Get a serverless calculator instance"""
    return _container.get_service("serverless_calculator")


def get_egress_calculator(custom_rates: Optional[Dict[str, float]] = None) -> Any:
    """Get an egress calculator instance with optional custom rates"""
    if custom_rates:
        return _container.get_service("egress_calculator", custom_rates=custom_rates)
    else:
        return _container.get_service("egress_calculator")