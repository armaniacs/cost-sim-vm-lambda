"""
Serverless cost calculation module
Unified calculator for AWS Lambda, Google Cloud Functions/Cloud Run,
Azure Functions, and OCI Functions
Following t_wada TDD principles with comprehensive provider abstraction
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ServerlessConfig:
    """Unified configuration for serverless cost calculation"""

    provider: str  # "aws_lambda", "gcp_functions", "gcp_cloudrun",
    # "azure_functions", "oci_functions"
    memory_mb: int
    execution_time_seconds: float
    monthly_executions: int
    include_free_tier: bool = True

    # Google Cloud Run specific
    cpu_count: Optional[float] = None  # vCPU count for Cloud Run

    # Common networking options
    egress_per_request_kb: float = 0.0
    internet_transfer_ratio: float = 100.0
    exchange_rate: float = 150.0

    # Provider-specific options
    include_ecosystem_benefits: bool = False  # Azure/Oracle ecosystem integration


@dataclass
class ServerlessResult:
    """Unified result for serverless cost calculation"""

    provider: str
    service_name: str  # Human-readable service name
    total_cost_usd: float
    total_cost_jpy: float

    # Detailed cost breakdown
    breakdown: Dict[
        str, float
    ]  # {"request_cost": 0.1, "compute_cost": 1.5, "memory_cost": 0.3}

    # Free tier information
    free_tier_savings: Dict[str, float]
    resource_usage: Dict[str, Any]  # actual usage numbers and limits

    # Provider-specific features
    features: Dict[str, Any]  # provider-specific information and benefits


class ServerlessProvider(ABC):
    """Abstract base class for serverless providers"""

    @abstractmethod
    def calculate_cost(self, config: ServerlessConfig) -> ServerlessResult:
        """Calculate cost for this provider"""

    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider-specific information"""

    @abstractmethod
    def validate_config(self, config: ServerlessConfig) -> List[str]:
        """Validate configuration and return list of errors"""


class AWSLambdaProvider(ServerlessProvider):
    """AWS Lambda cost calculation provider"""

    # AWS Lambda pricing constants (Tokyo region)
    REQUEST_PRICE_PER_MILLION = 0.20
    COMPUTE_PRICE_PER_GB_SECOND = 0.0000166667
    FREE_TIER_REQUESTS = 1_000_000
    FREE_TIER_GB_SECONDS = 400_000

    def calculate_cost(self, config: ServerlessConfig) -> ServerlessResult:
        """Calculate AWS Lambda costs with existing logic compatibility"""

        # Request charges
        if config.include_free_tier:
            billable_requests = max(
                0, config.monthly_executions - self.FREE_TIER_REQUESTS
            )
        else:
            billable_requests = config.monthly_executions

        request_cost = (billable_requests / 1_000_000) * self.REQUEST_PRICE_PER_MILLION

        # Compute charges
        gb_seconds = (
            (config.memory_mb / 1024)
            * config.execution_time_seconds
            * config.monthly_executions
        )

        if config.include_free_tier:
            billable_gb_seconds = max(0, gb_seconds - self.FREE_TIER_GB_SECONDS)
        else:
            billable_gb_seconds = gb_seconds

        compute_cost = billable_gb_seconds * self.COMPUTE_PRICE_PER_GB_SECOND

        total_cost_usd = request_cost + compute_cost
        total_cost_jpy = total_cost_usd * config.exchange_rate

        # Free tier savings
        free_tier_request_savings = (
            min(config.monthly_executions, self.FREE_TIER_REQUESTS)
            / 1_000_000
            * self.REQUEST_PRICE_PER_MILLION
            if config.include_free_tier
            else 0
        )
        free_tier_compute_savings = (
            min(gb_seconds, self.FREE_TIER_GB_SECONDS)
            * self.COMPUTE_PRICE_PER_GB_SECOND
            if config.include_free_tier
            else 0
        )

        return ServerlessResult(
            provider="aws_lambda",
            service_name="AWS Lambda",
            total_cost_usd=total_cost_usd,
            total_cost_jpy=total_cost_jpy,
            breakdown={
                "request_cost": request_cost,
                "compute_cost": compute_cost,
                "egress_cost": 0.0,  # Will be calculated separately
                # by egress calculator
            },
            free_tier_savings={
                "request_savings": free_tier_request_savings,
                "compute_savings": free_tier_compute_savings,
            },
            resource_usage={
                "requests_used": config.monthly_executions,
                "requests_free": (
                    self.FREE_TIER_REQUESTS if config.include_free_tier else 0
                ),
                "gb_seconds_used": gb_seconds,
                "gb_seconds_free": (
                    self.FREE_TIER_GB_SECONDS if config.include_free_tier else 0
                ),
            },
            features={
                "cold_start_optimization": True,
                "auto_scaling": True,
                "pay_per_request": True,
            },
        )

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": "AWS Lambda",
            "pricing_model": "Request + GB-second",
            "free_tier": f"{self.FREE_TIER_REQUESTS:,} requests + "
            f"{self.FREE_TIER_GB_SECONDS:,} GB-seconds/month",
            "max_execution_time": 900,  # 15 minutes
            "max_memory": 10240,
        }

    def validate_config(self, config: ServerlessConfig) -> List[str]:
        errors = []

        if not (128 <= config.memory_mb <= 10240):
            errors.append("Memory must be between 128 and 10,240 MB")

        if not (0.1 <= config.execution_time_seconds <= 900):
            errors.append("Execution time must be between 0.1 and 900 seconds")

        if not (1 <= config.monthly_executions <= 1_000_000_000):
            errors.append("Monthly executions must be between 1 and 1 billion")

        return errors


class GCPFunctionsProvider(ServerlessProvider):
    """Google Cloud Functions cost calculation provider"""

    # Google Cloud Functions pricing (asia-northeast1, 2nd gen)
    REQUEST_PRICE = 0.0000004  # $0.0000004 per request
    COMPUTE_PRICE_PER_GB_SECOND = 0.0000025  # $0.0000025 per GB-second
    FREE_TIER_REQUESTS = 2_000_000  # 2M requests/month
    FREE_TIER_GB_SECONDS = 400_000  # 400,000 GB-seconds/month

    def __init__(self) -> None:
        """Initialize GCP Functions provider with egress calculator"""
        from app.models.egress_calculator import EgressCalculator

        self.egress_calculator = EgressCalculator()

    def calculate_cost(
        self, config: ServerlessConfig, include_egress_free_tier: Optional[bool] = None
    ) -> ServerlessResult:
        """Calculate Google Cloud Functions costs"""

        # Request charges
        if config.include_free_tier:
            billable_requests = max(
                0, config.monthly_executions - self.FREE_TIER_REQUESTS
            )
        else:
            billable_requests = config.monthly_executions

        request_cost = billable_requests * self.REQUEST_PRICE

        # Compute charges
        gb_seconds = (
            (config.memory_mb / 1024)
            * config.execution_time_seconds
            * config.monthly_executions
        )

        if config.include_free_tier:
            billable_gb_seconds = max(0, gb_seconds - self.FREE_TIER_GB_SECONDS)
        else:
            billable_gb_seconds = gb_seconds

        compute_cost = billable_gb_seconds * self.COMPUTE_PRICE_PER_GB_SECOND

        # Egress charges with Internet Transfer Ratio
        egress_cost = self.calculate_egress_charges(config, include_egress_free_tier)

        total_cost_usd = request_cost + compute_cost + egress_cost
        total_cost_jpy = total_cost_usd * config.exchange_rate

        # Free tier savings
        free_tier_request_savings = (
            min(config.monthly_executions, self.FREE_TIER_REQUESTS) * self.REQUEST_PRICE
            if config.include_free_tier
            else 0
        )
        free_tier_compute_savings = (
            min(gb_seconds, self.FREE_TIER_GB_SECONDS)
            * self.COMPUTE_PRICE_PER_GB_SECOND
            if config.include_free_tier
            else 0
        )

        return ServerlessResult(
            provider="gcp_functions",
            service_name="Google Cloud Functions",
            total_cost_usd=total_cost_usd,
            total_cost_jpy=total_cost_jpy,
            breakdown={
                "request_cost": request_cost,
                "compute_cost": compute_cost,
                "egress_cost": egress_cost,
            },
            free_tier_savings={
                "request_savings": free_tier_request_savings,
                "compute_savings": free_tier_compute_savings,
            },
            resource_usage={
                "requests_used": config.monthly_executions,
                "requests_free": (
                    self.FREE_TIER_REQUESTS if config.include_free_tier else 0
                ),
                "gb_seconds_used": gb_seconds,
                "gb_seconds_free": (
                    self.FREE_TIER_GB_SECONDS if config.include_free_tier else 0
                ),
            },
            features={
                "execution_model": "function_based",
                "cold_start_minimal": True,
                "automatic_scaling": True,
                "generous_free_tier": True,
            },
        )

    def get_provider_info(self) -> Dict[str, Any]:
        return {
            "name": "Google Cloud Functions",
            "pricing_model": "Request + GB-second",
            "free_tier": f"{self.FREE_TIER_REQUESTS:,} requests + "
            f"{self.FREE_TIER_GB_SECONDS:,} GB-seconds/month",
            "max_execution_time": 540,  # 9 minutes
            "max_memory": 8192,
        }

    def validate_config(self, config: ServerlessConfig) -> List[str]:
        errors = []

        if not (128 <= config.memory_mb <= 8192):
            errors.append(
                "Memory must be between 128 and 8,192 MB for Google Cloud Functions"
            )

        if not (0.1 <= config.execution_time_seconds <= 540):
            errors.append(
                "Execution time must be between 0.1 and 540 seconds "
                "for Google Cloud Functions"
            )

        if not (1 <= config.monthly_executions <= 1_000_000_000):
            errors.append("Monthly executions must be between 1 and 1 billion")

        return errors

    def calculate_egress_charges(
        self, config: ServerlessConfig, include_egress_free_tier: Optional[bool] = None
    ) -> float:
        """
        Calculate egress transfer charges for GCP Functions executions

        Args:
            config: Serverless configuration

        Returns:
            Egress charges in USD
        """
        if config.egress_per_request_kb <= 0:
            return 0.0

        from app.models.egress_calculator import EgressConfig

        # Apply Internet Transfer Ratio to egress calculation
        effective_egress_kb = config.egress_per_request_kb * (
            config.internet_transfer_ratio / 100.0
        )

        # Use explicit egress free tier setting, fall back to general free tier setting
        use_egress_free_tier = (
            include_egress_free_tier
            if include_egress_free_tier is not None
            else config.include_free_tier
        )

        egress_config = EgressConfig(
            provider="google_cloud",
            executions_per_month=config.monthly_executions,
            transfer_kb_per_request=effective_egress_kb,
            include_free_tier=use_egress_free_tier,
        )

        return self.egress_calculator.calculate_egress_cost(egress_config)


class ServerlessCalculator:
    """Unified serverless cost calculator supporting multiple providers"""

    def __init__(self) -> None:
        """Initialize calculator with all supported providers"""
        self.providers = {
            "aws_lambda": AWSLambdaProvider(),
            "gcp_functions": GCPFunctionsProvider(),
            # Note: Other providers (gcp_cloudrun, azure_functions, oci_functions)
            # will be implemented in subsequent phases
        }

        logger.info(
            f"ServerlessCalculator initialized with providers: "
            f"{list(self.providers.keys())}"
        )

    def calculate(
        self, config: ServerlessConfig, include_egress_free_tier: Optional[bool] = None
    ) -> ServerlessResult:
        """
        Calculate serverless costs for the specified provider

        Args:
            config: Serverless configuration with provider specification

        Returns:
            ServerlessResult with detailed cost breakdown

        Raises:
            ValueError: If provider is not supported or configuration is invalid
        """
        if config.provider not in self.providers:
            available_providers = list(self.providers.keys())
            raise ValueError(
                f"Provider '{config.provider}' not supported. "
                f"Available: {available_providers}"
            )

        # Validate configuration
        provider = self.providers[config.provider]
        validation_errors = provider.validate_config(config)

        if validation_errors:
            raise ValueError(
                f"Configuration validation failed: {', '.join(validation_errors)}"
            )

        # Calculate cost
        try:
            if (
                hasattr(provider, "calculate_cost")
                and "include_egress_free_tier"
                in provider.calculate_cost.__code__.co_varnames
            ):
                result = provider.calculate_cost(config, include_egress_free_tier)
            else:
                result = provider.calculate_cost(config)
            logger.info(
                f"Calculated cost for {config.provider}: ${result.total_cost_usd:.4f}"
            )
            return result

        except Exception as e:
            logger.error(f"Cost calculation failed for {config.provider}: {str(e)}")
            raise

    def get_supported_providers(self) -> List[str]:
        """Get list of supported provider names"""
        return list(self.providers.keys())

    def get_provider_info(self, provider: str) -> Dict[str, Any]:
        """Get information about a specific provider"""
        if provider not in self.providers:
            raise ValueError(f"Provider '{provider}' not supported")

        return self.providers[provider].get_provider_info()

    def calculate_multiple(
        self, configs: List[ServerlessConfig]
    ) -> List[ServerlessResult]:
        """
        Calculate costs for multiple configurations

        Args:
            configs: List of serverless configurations

        Returns:
            List of ServerlessResult objects
        """
        results = []

        for config in configs:
            try:
                result = self.calculate(config)
                results.append(result)
            except Exception as e:
                logger.error(
                    f"Failed to calculate cost for {config.provider}: {str(e)}"
                )
                # Continue with other calculations

        return results
