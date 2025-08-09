"""
VM cost calculation module
AWS EC2, Sakura Cloud, Google Cloud, Azure, and OCI pricing calculator
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VMConfig:
    """Configuration for VM cost calculation"""

    provider: str  # "aws_ec2", "sakura_cloud", "google_cloud", "azure", "oci"
    instance_type: str
    region: str = "ap-northeast-1"  # Tokyo region


class VMCalculator:
    """Calculator for VM costs (EC2, Sakura Cloud, Google Cloud, Azure, and OCI)"""

    # AWS EC2 pricing (Tokyo region, USD per hour)
    EC2_PRICING: Dict[str, Dict[str, Any]] = {
        "t3.micro": {"hourly_usd": 0.0136, "vcpu": 2, "memory_gb": 1},
        "t3.small": {"hourly_usd": 0.0272, "vcpu": 2, "memory_gb": 2},
        "t3.medium": {"hourly_usd": 0.0544, "vcpu": 2, "memory_gb": 4},
        "t3.large": {"hourly_usd": 0.1088, "vcpu": 2, "memory_gb": 8},
        "c5.large": {"hourly_usd": 0.096, "vcpu": 2, "memory_gb": 4},
        "c5.xlarge": {"hourly_usd": 0.192, "vcpu": 4, "memory_gb": 8},
    }

    # Sakura Cloud pricing (JPY per month)
    SAKURA_PRICING: Dict[str, Dict[str, Any]] = {
        "1core_1gb": {"monthly_jpy": 1595, "vcpu": 1, "memory_gb": 1, "storage_gb": 20},
        "2core_2gb": {"monthly_jpy": 3190, "vcpu": 2, "memory_gb": 2, "storage_gb": 20},
        "2core_4gb": {"monthly_jpy": 4180, "vcpu": 2, "memory_gb": 4, "storage_gb": 20},
        "4core_8gb": {"monthly_jpy": 7370, "vcpu": 4, "memory_gb": 8, "storage_gb": 40},
        "6core_12gb": {
            "monthly_jpy": 11560,
            "vcpu": 6,
            "memory_gb": 12,
            "storage_gb": 60,
        },
    }

    # Google Cloud Compute Engine pricing (Tokyo region, USD per hour)
    GCP_PRICING: Dict[str, Dict[str, Any]] = {
        "e2-micro": {"hourly_usd": 0.0084, "vcpu": 0.25, "memory_gb": 1},
        "e2-small": {"hourly_usd": 0.0168, "vcpu": 0.5, "memory_gb": 2},
        "e2-medium": {"hourly_usd": 0.0335, "vcpu": 1, "memory_gb": 4},
        "n2-standard-1": {"hourly_usd": 0.0485, "vcpu": 1, "memory_gb": 4},
        "n2-standard-2": {"hourly_usd": 0.0970, "vcpu": 2, "memory_gb": 8},
        "c2-standard-4": {"hourly_usd": 0.2088, "vcpu": 4, "memory_gb": 16},
    }

    # Azure pricing (Japan East, USD per hour)
    AZURE_PRICING: Dict[str, Dict[str, Any]] = {
        "B1ls": {"hourly_usd": 0.0092, "vcpu": 1, "memory_gb": 0.5},
        "B1s": {"hourly_usd": 0.0104, "vcpu": 1, "memory_gb": 1},
        "B1ms": {"hourly_usd": 0.0208, "vcpu": 1, "memory_gb": 2},
        "B2s": {"hourly_usd": 0.0416, "vcpu": 2, "memory_gb": 4},
        "B2ms": {"hourly_usd": 0.0832, "vcpu": 2, "memory_gb": 8},
        "A1_Basic": {"hourly_usd": 0.016, "vcpu": 1, "memory_gb": 1.75},
        "D3": {"hourly_usd": 0.308, "vcpu": 4, "memory_gb": 14},
        "D4": {"hourly_usd": 0.616, "vcpu": 8, "memory_gb": 28},
    }

    # OCI pricing (Tokyo, USD per hour)
    OCI_PRICING: Dict[str, Dict[str, Any]] = {
        "VM.Standard.E2.1.Micro": {"hourly_usd": 0.005, "vcpu": 1, "memory_gb": 1},
        "VM.Standard.A1.Flex_1_6": {"hourly_usd": 0.015, "vcpu": 1, "memory_gb": 6},
        "VM.Standard.A1.Flex_2_12": {"hourly_usd": 0.030, "vcpu": 2, "memory_gb": 12},
        "VM.Standard.E4.Flex_1_8": {"hourly_usd": 0.025, "vcpu": 1, "memory_gb": 8},
        "VM.Standard.E4.Flex_2_16": {"hourly_usd": 0.049, "vcpu": 2, "memory_gb": 16},
        "VM.Standard.E2.1.Micro_Free": {"hourly_usd": 0.0, "vcpu": 1, "memory_gb": 1},
        "VM.Standard.A1.Flex_Free": {"hourly_usd": 0.0, "vcpu": 4, "memory_gb": 24},
    }

    # Hours per month (average)
    HOURS_PER_MONTH = 730

    def __init__(self) -> None:
        """Initialize the calculator"""
        # Import here to avoid circular imports
        from app.models.egress_calculator import EgressCalculator

        self.egress_calculator = EgressCalculator()

    def get_ec2_cost(self, instance_type: str) -> Optional[Dict[str, Any]]:
        """
        Get EC2 instance cost information

        Args:
            instance_type: EC2 instance type

        Returns:
            Dictionary with cost and spec information, or None if not found
        """
        if instance_type not in self.EC2_PRICING:
            return None

        pricing = self.EC2_PRICING[instance_type]
        monthly_cost = pricing["hourly_usd"] * self.HOURS_PER_MONTH

        return {
            "provider": "aws_ec2",
            "instance_type": instance_type,
            "hourly_cost_usd": pricing["hourly_usd"],
            "monthly_cost_usd": monthly_cost,
            "specs": {
                "vcpu": pricing["vcpu"],
                "memory_gb": pricing["memory_gb"],
            },
        }

    def get_sakura_cost(self, instance_type: str) -> Optional[Dict[str, Any]]:
        """
        Get Sakura Cloud instance cost information

        Args:
            instance_type: Sakura Cloud instance type

        Returns:
            Dictionary with cost and spec information, or None if not found
        """
        if instance_type not in self.SAKURA_PRICING:
            return None

        pricing = self.SAKURA_PRICING[instance_type]

        return {
            "provider": "sakura_cloud",
            "instance_type": instance_type,
            "monthly_cost_jpy": pricing["monthly_jpy"],
            "specs": {
                "vcpu": pricing["vcpu"],
                "memory_gb": pricing["memory_gb"],
                "storage_gb": pricing["storage_gb"],
            },
        }

    def get_gcp_cost(self, instance_type: str) -> Optional[Dict[str, Any]]:
        """
        Get Google Cloud Compute Engine instance cost information

        Args:
            instance_type: Google Cloud instance type

        Returns:
            Dictionary with cost and spec information, or None if not found
        """
        if instance_type not in self.GCP_PRICING:
            return None

        pricing = self.GCP_PRICING[instance_type]
        monthly_cost = pricing["hourly_usd"] * self.HOURS_PER_MONTH

        return {
            "provider": "google_cloud",
            "instance_type": instance_type,
            "hourly_cost_usd": pricing["hourly_usd"],
            "monthly_cost_usd": monthly_cost,
            "specs": {
                "vcpu": pricing["vcpu"],
                "memory_gb": pricing["memory_gb"],
            },
        }

    def get_azure_cost(self, instance_type: str) -> Optional[Dict[str, Any]]:
        """
        Get Azure instance cost information

        Args:
            instance_type: Azure instance type

        Returns:
            Dictionary with cost and spec information, or None if not found
        """
        if instance_type not in self.AZURE_PRICING:
            return None

        pricing = self.AZURE_PRICING[instance_type]
        monthly_cost = pricing["hourly_usd"] * self.HOURS_PER_MONTH

        return {
            "provider": "azure",
            "instance_type": instance_type,
            "hourly_cost_usd": pricing["hourly_usd"],
            "monthly_cost_usd": monthly_cost,
            "specs": {
                "vcpu": pricing["vcpu"],
                "memory_gb": pricing["memory_gb"],
            },
        }

    def get_oci_cost(self, instance_type: str) -> Optional[Dict[str, Any]]:
        """
        Get OCI instance cost information

        Args:
            instance_type: OCI instance type

        Returns:
            Dictionary with cost and spec information, or None if not found
        """
        if instance_type not in self.OCI_PRICING:
            return None

        pricing = self.OCI_PRICING[instance_type]
        monthly_cost = pricing["hourly_usd"] * self.HOURS_PER_MONTH

        return {
            "provider": "oci",
            "instance_type": instance_type,
            "hourly_cost_usd": pricing["hourly_usd"],
            "monthly_cost_usd": monthly_cost,
            "specs": {
                "vcpu": pricing["vcpu"],
                "memory_gb": pricing["memory_gb"],
            },
        }

    def calculate_vm_cost(self, config: VMConfig) -> Optional[Dict[str, Any]]:
        """
        Calculate VM cost based on configuration

        Args:
            config: VM configuration

        Returns:
            Dictionary containing cost breakdown and specifications
        """
        if config.provider == "aws_ec2":
            result = self.get_ec2_cost(config.instance_type)
        elif config.provider == "sakura_cloud":
            result = self.get_sakura_cost(config.instance_type)
        elif config.provider == "google_cloud":
            result = self.get_gcp_cost(config.instance_type)
        elif config.provider == "azure":
            result = self.get_azure_cost(config.instance_type)
        elif config.provider == "oci":
            result = self.get_oci_cost(config.instance_type)
        else:
            return None

        if result is None:
            return None

        # Add configuration info
        result["configuration"] = {
            "provider": config.provider,
            "instance_type": config.instance_type,
            "region": config.region,
        }

        return result

    def get_available_instances(self, provider: str) -> Dict[str, Dict[str, Any]]:
        """
        Get list of available instances for a provider

        Args:
            provider: "aws_ec2", "sakura_cloud", "google_cloud", "azure", or "oci"

        Returns:
            Dictionary of available instances with their specifications
        """
        if provider == "sakura_cloud":
            return {
                instance_type: {
                    "monthly_cost_jpy": pricing["monthly_jpy"],
                    "specs": {
                        "vcpu": pricing["vcpu"],
                        "memory_gb": pricing["memory_gb"],
                        "storage_gb": pricing["storage_gb"],
                    },
                }
                for instance_type, pricing in self.SAKURA_PRICING.items()
            }

        pricing_data: Dict[str, Any]
        if provider == "aws_ec2":
            pricing_data = self.EC2_PRICING
        elif provider == "google_cloud":
            pricing_data = self.GCP_PRICING
        elif provider == "azure":
            pricing_data = self.AZURE_PRICING
        elif provider == "oci":
            pricing_data = self.OCI_PRICING
        else:
            return {}

        result = {}
        for instance_type, pricing in pricing_data.items():
            monthly_cost = pricing["hourly_usd"] * self.HOURS_PER_MONTH
            result[instance_type] = {
                "hourly_cost_usd": pricing["hourly_usd"],
                "monthly_cost_usd": monthly_cost,
                "specs": {
                    "vcpu": pricing["vcpu"],
                    "memory_gb": pricing["memory_gb"],
                },
            }
        return result

    def recommend_instance_for_lambda(
        self, lambda_memory_mb: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recommend VM instances equivalent to Lambda configuration

        Args:
            lambda_memory_mb: Lambda memory size in MB

        Returns:
            Dictionary with recommendations for all providers
        """
        lambda_memory_gb = lambda_memory_mb / 1024

        recommendations: Dict[str, List[Dict[str, Any]]] = {
            "aws_ec2": [],
            "sakura_cloud": [],
            "google_cloud": [],
            "azure": [],
            "oci": [],
        }

        provider_map = {
            "aws_ec2": (self.EC2_PRICING, self.get_ec2_cost),
            "google_cloud": (self.GCP_PRICING, self.get_gcp_cost),
            "azure": (self.AZURE_PRICING, self.get_azure_cost),
            "oci": (self.OCI_PRICING, self.get_oci_cost),
            "sakura_cloud": (self.SAKURA_PRICING, self.get_sakura_cost),
        }

        for provider, (pricing_data, cost_func) in provider_map.items():
            for instance_type, pricing in pricing_data.items():
                if float(pricing["memory_gb"]) >= lambda_memory_gb:
                    cost = cost_func(instance_type)
                    if cost:
                        recommendations[provider].append(
                            {
                                "instance_type": instance_type,
                                "memory_ratio": pricing["memory_gb"] / lambda_memory_gb,
                                **cost,
                            }
                        )

        # Sort by memory ratio (closest match first)
        for provider in recommendations:
            recommendations[provider].sort(key=lambda x: x["memory_ratio"])

        return recommendations

    def convert_currency(
        self, amount_usd: float, exchange_rate: float = 150.0
    ) -> float:
        """
        Convert USD to JPY

        Args:
            amount_usd: Amount in USD
            exchange_rate: JPY per USD rate

        Returns:
            Amount in JPY
        """
        return amount_usd * exchange_rate

    def calculate_vm_egress_cost(
        self,
        provider: str,
        monthly_executions: int,
        egress_per_request_kb: float,
        custom_rates: Optional[Dict[str, float]] = None,
        include_egress_free_tier: bool = True,
        internet_transfer_ratio: float = 100.0,  # PBI10: % of traffic to internet
    ) -> float:
        """
        Calculate egress cost for VM provider

        Args:
            provider: VM provider ("aws_ec2", "google_cloud", "sakura_cloud",
            "azure", "oci")
            monthly_executions: Number of executions per month
            egress_per_request_kb: KB transferred per request
            custom_rates: Optional custom egress rates
            internet_transfer_ratio: % of traffic going to internet (PBI10)

        Returns:
            Monthly egress cost in provider's currency
        """
        if egress_per_request_kb <= 0 or monthly_executions <= 0:
            return 0.0

        from app.models.egress_calculator import EgressCalculator, EgressConfig

        # Use custom calculator with custom rates if provided
        if custom_rates:
            egress_calculator = EgressCalculator(custom_rates)
        else:
            egress_calculator = self.egress_calculator

        # PBI10: Apply internet transfer ratio to egress calculation
        effective_egress_kb = egress_per_request_kb * (internet_transfer_ratio / 100.0)

        egress_config = EgressConfig(
            executions_per_month=monthly_executions,
            transfer_kb_per_request=effective_egress_kb,
            provider=provider,
            include_free_tier=include_egress_free_tier,
        )

        return egress_calculator.calculate_egress_cost(egress_config)

    def get_monthly_cost_with_egress(
        self,
        config: VMConfig,
        monthly_executions: int = 0,
        egress_per_request_kb: float = 0.0,
        custom_egress_rates: Optional[Dict[str, float]] = None,
        include_egress_free_tier: bool = True,
        internet_transfer_ratio: float = 100.0,  # PBI10: % of traffic to internet
    ) -> Optional[Dict[str, Any]]:
        """
        Get VM monthly cost including egress charges

        Args:
            config: VM configuration
            monthly_executions: Number of executions per month
            egress_per_request_kb: KB transferred per request
            custom_egress_rates: Optional custom egress rates

        Returns:
            Dictionary with cost breakdown including egress
        """
        # Get base VM cost
        base_cost = self.calculate_vm_cost(config)

        if base_cost is None:
            return None

        # Calculate egress cost
        egress_cost = self.calculate_vm_egress_cost(
            config.provider,
            monthly_executions,
            egress_per_request_kb,
            custom_egress_rates,
            include_egress_free_tier,
            internet_transfer_ratio,  # PBI10
        )

        # Add egress cost to base cost
        result = base_cost.copy()

        # Add egress costs in appropriate currency
        if config.provider == "sakura_cloud":
            result["egress_cost_jpy"] = egress_cost
            result["total_monthly_cost_jpy"] = result["monthly_cost_jpy"] + egress_cost
        else:
            result["egress_cost_usd"] = egress_cost
            result["total_monthly_cost_usd"] = result["monthly_cost_usd"] + egress_cost

        return result
