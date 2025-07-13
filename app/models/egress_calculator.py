"""
Egress fee calculation module for PBI09
Following t_wada TDD principles - Green Phase: Minimum implementation to pass tests

Calculates internet egress transfer costs for different cloud providers
"""
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class EgressConfig:
    """Configuration for egress cost calculation"""

    executions_per_month: int
    transfer_kb_per_request: float  # KB transferred per request
    provider: str  # "aws_lambda", "aws_ec2", "google_cloud", "sakura_cloud"
    include_free_tier: bool = True  # Include 100GB/month free tier for AWS & Google


class EgressCalculator:
    """Calculator for internet egress transfer costs"""

    # Default egress pricing rates (USD/GB for cloud providers, JPY/GB for Sakura)
    DEFAULT_EGRESS_RATES: Dict[str, float] = {
        "aws_lambda": 0.114,  # AWS Lambda egress: 0.114 USD/GB
        "aws_ec2": 0.114,  # AWS EC2 egress: 0.114 USD/GB
        "google_cloud": 0.12,  # Google Cloud egress: 0.12 USD/GB
        "sakura_cloud": 0.0,  # Sakura Cloud egress: 0.0 JPY/GB (egress free)
    }

    # Free tier limits (100GB/month for AWS and Google Cloud)
    FREE_TIER_GB_PER_MONTH = 100.0
    FREE_TIER_PROVIDERS = {"aws_lambda", "aws_ec2", "google_cloud"}

    def __init__(self, custom_rates: Optional[Dict[str, float]] = None) -> None:
        """Initialize the egress calculator with optional custom rates"""
        if custom_rates:
            self.egress_rates = custom_rates.copy()
        else:
            self.egress_rates = self.DEFAULT_EGRESS_RATES.copy()

    def calculate_egress_cost(self, config: EgressConfig) -> float:
        """
        Calculate monthly egress transfer cost

        Args:
            config: Egress configuration with executions, transfer amount, and provider

        Returns:
            Monthly egress cost in provider's currency (USD for cloud, JPY for Sakura)

        Raises:
            ValueError: If configuration is invalid
        """
        # Validation
        self._validate_config(config)

        # Handle zero cases
        if config.executions_per_month == 0 or config.transfer_kb_per_request == 0:
            return 0.0

        # Get rate for provider
        rate_per_gb = self.get_rate_for_provider(config.provider)

        # Convert KB to GB and calculate total cost
        gb_per_request = self.convert_kb_to_gb(config.transfer_kb_per_request)
        total_gb_per_month = config.executions_per_month * gb_per_request

        # Apply free tier if applicable
        billable_gb_per_month = total_gb_per_month
        if (
            config.include_free_tier
            and config.provider in self.FREE_TIER_PROVIDERS
            and total_gb_per_month > self.FREE_TIER_GB_PER_MONTH
        ):
            billable_gb_per_month = total_gb_per_month - self.FREE_TIER_GB_PER_MONTH
        elif (
            config.include_free_tier
            and config.provider in self.FREE_TIER_PROVIDERS
            and total_gb_per_month <= self.FREE_TIER_GB_PER_MONTH
        ):
            billable_gb_per_month = 0.0

        total_cost = billable_gb_per_month * rate_per_gb

        return total_cost

    def get_rate_for_provider(self, provider: str) -> float:
        """
        Get egress rate for specific provider

        Args:
            provider: Provider name

        Returns:
            Rate per GB in provider's currency

        Raises:
            ValueError: If provider is not supported
        """
        if provider not in self.egress_rates:
            raise ValueError(f"Unsupported provider: {provider}")

        return self.egress_rates[provider]

    def convert_kb_to_gb(self, kb: float) -> float:
        """
        Convert kilobytes to gigabytes

        Args:
            kb: Amount in kilobytes

        Returns:
            Amount in gigabytes
        """
        # 1 GB = 1024 MB = 1024 * 1024 KB
        return kb / (1024 * 1024)

    def _validate_config(self, config: EgressConfig) -> None:
        """
        Validate egress configuration

        Args:
            config: Configuration to validate

        Raises:
            ValueError: If configuration is invalid
        """
        if config.executions_per_month < 0:
            raise ValueError("Executions per month cannot be negative")

        if config.transfer_kb_per_request < 0:
            raise ValueError("Transfer amount per request cannot be negative")

        if config.provider not in self.egress_rates:
            raise ValueError(f"Unsupported provider: {config.provider}")
