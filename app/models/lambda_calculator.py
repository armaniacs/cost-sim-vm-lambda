"""
AWS Lambda cost calculation module
Following t_wada TDD principles - Green Phase: Minimum implementation to pass tests
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class LambdaConfig:
    """Configuration for Lambda cost calculation"""

    memory_mb: int
    execution_time_seconds: int
    monthly_executions: int
    include_free_tier: bool
    egress_per_request_kb: float = 0.0  # KB transferred per request (default: 0)
    internet_transfer_ratio: float = (
        100.0  # PBI10: % of traffic to internet (default: 100%)
    )


class LambdaCalculator:
    """Calculator for AWS Lambda costs"""

    # AWS Lambda pricing constants (Tokyo region)
    REQUEST_PRICE_PER_MILLION = 0.20
    COMPUTE_PRICE_PER_GB_SECOND = 0.0000166667
    FREE_TIER_REQUESTS = 1_000_000
    FREE_TIER_GB_SECONDS = 400_000

    def __init__(self, pricing_config: Optional[Dict[str, Any]] = None) -> None:
        """Initialize the calculator"""
        # Import here to avoid circular imports
        from app.models.egress_calculator import EgressCalculator

        # Store pricing configuration
        self.pricing_config = pricing_config or {}

        # Apply custom pricing if provided
        if pricing_config and "request_price_per_million" in pricing_config:
            self.REQUEST_PRICE_PER_MILLION = pricing_config["request_price_per_million"]
        if pricing_config and "compute_price_per_gb_second" in pricing_config:
            self.COMPUTE_PRICE_PER_GB_SECOND = pricing_config[
                "compute_price_per_gb_second"
            ]
        if pricing_config and "free_tier_requests" in pricing_config:
            self.FREE_TIER_REQUESTS = pricing_config["free_tier_requests"]
        if pricing_config and "free_tier_gb_seconds" in pricing_config:
            self.FREE_TIER_GB_SECONDS = pricing_config["free_tier_gb_seconds"]

        self.egress_calculator = EgressCalculator()

    def calculate_request_charges(self, config: LambdaConfig) -> float:
        """
        Calculate request charges for Lambda executions

        Args:
            config: Lambda configuration

        Returns:
            Request charges in USD
        """
        if config.include_free_tier:
            billable_requests = max(
                0, config.monthly_executions - self.FREE_TIER_REQUESTS
            )
        else:
            billable_requests = config.monthly_executions

        return (billable_requests * self.REQUEST_PRICE_PER_MILLION) / 1_000_000

    def calculate_gb_seconds(self, config: LambdaConfig) -> float:
        """
        Calculate total GB-seconds for Lambda executions

        Args:
            config: Lambda configuration

        Returns:
            Total GB-seconds
        """
        gb_memory = config.memory_mb / 1024
        return gb_memory * config.execution_time_seconds * config.monthly_executions

    def calculate_compute_charges(self, config: LambdaConfig) -> float:
        """
        Calculate compute charges for Lambda executions

        Args:
            config: Lambda configuration

        Returns:
            Compute charges in USD
        """
        total_gb_seconds = self.calculate_gb_seconds(config)

        if config.include_free_tier:
            billable_gb_seconds = max(0, total_gb_seconds - self.FREE_TIER_GB_SECONDS)
        else:
            billable_gb_seconds = total_gb_seconds

        return billable_gb_seconds * self.COMPUTE_PRICE_PER_GB_SECOND

    def calculate_egress_charges(
        self,
        config: LambdaConfig,
        custom_rates: Optional[Dict[str, float]] = None,
        include_egress_free_tier: bool = True,
    ) -> float:
        """
        Calculate egress transfer charges for Lambda executions

        Args:
            config: Lambda configuration
            custom_rates: Optional custom egress rates

        Returns:
            Egress charges in USD
        """
        if config.egress_per_request_kb <= 0:
            return 0.0

        from app.models.egress_calculator import EgressCalculator, EgressConfig

        # Use custom calculator with custom rates if provided
        if custom_rates:
            egress_calculator = EgressCalculator(custom_rates)
        else:
            egress_calculator = self.egress_calculator

        # PBI10: Apply internet transfer ratio to egress calculation
        effective_egress_kb = config.egress_per_request_kb * (
            config.internet_transfer_ratio / 100.0
        )

        egress_config = EgressConfig(
            executions_per_month=config.monthly_executions,
            transfer_kb_per_request=effective_egress_kb,
            provider="aws_lambda",
            include_free_tier=include_egress_free_tier,
        )

        return egress_calculator.calculate_egress_cost(egress_config)

    def calculate_total_cost(
        self,
        config: LambdaConfig,
        custom_egress_rates: Optional[Dict[str, float]] = None,
        include_egress_free_tier: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate total cost including request and compute charges

        Args:
            config: Lambda configuration
            custom_egress_rates: Optional custom egress rates

        Returns:
            Dictionary containing detailed cost breakdown
        """
        request_charges = self.calculate_request_charges(config)
        compute_charges = self.calculate_compute_charges(config)
        egress_charges = self.calculate_egress_charges(
            config, custom_egress_rates, include_egress_free_tier
        )
        total_cost = request_charges + compute_charges + egress_charges
        gb_seconds = self.calculate_gb_seconds(config)

        return {
            "request_charges": request_charges,
            "compute_charges": compute_charges,
            "egress_charges": egress_charges,
            "total_cost": total_cost,
            "gb_seconds": gb_seconds,
            "configuration": {
                "memory_mb": config.memory_mb,
                "execution_time_seconds": config.execution_time_seconds,
                "monthly_executions": config.monthly_executions,
                "include_free_tier": config.include_free_tier,
                "egress_per_request_kb": config.egress_per_request_kb,
                "internet_transfer_ratio": config.internet_transfer_ratio,  # PBI10
            },
        }
