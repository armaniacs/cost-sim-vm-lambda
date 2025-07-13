"""
VM cost calculation module
AWS EC2 and Sakura Cloud pricing calculator
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class VMConfig:
    """Configuration for VM cost calculation"""

    provider: str  # "aws_ec2", "sakura_cloud", or "google_cloud"
    instance_type: str
    region: str = "ap-northeast-1"  # Tokyo region


class VMCalculator:
    """Calculator for VM costs (EC2, Sakura Cloud, and Google Cloud)"""

    # AWS EC2 pricing (Tokyo region, USD per hour)
    EC2_PRICING = {
        "t3.micro": {"hourly_usd": 0.0136, "vcpu": 2, "memory_gb": 1},
        "t3.small": {"hourly_usd": 0.0272, "vcpu": 2, "memory_gb": 2},
        "t3.medium": {"hourly_usd": 0.0544, "vcpu": 2, "memory_gb": 4},
        "t3.large": {"hourly_usd": 0.1088, "vcpu": 2, "memory_gb": 8},
        "c5.large": {"hourly_usd": 0.096, "vcpu": 2, "memory_gb": 4},
        "c5.xlarge": {"hourly_usd": 0.192, "vcpu": 4, "memory_gb": 8},
    }

    # Sakura Cloud pricing (JPY per month)
    SAKURA_PRICING = {
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
    GCP_PRICING = {
        "e2-micro": {"hourly_usd": 0.0084, "vcpu": 0.25, "memory_gb": 1},
        "e2-small": {"hourly_usd": 0.0168, "vcpu": 0.5, "memory_gb": 2},
        "e2-medium": {"hourly_usd": 0.0335, "vcpu": 1, "memory_gb": 4},
        "n2-standard-1": {"hourly_usd": 0.0485, "vcpu": 1, "memory_gb": 4},
        "n2-standard-2": {"hourly_usd": 0.0970, "vcpu": 2, "memory_gb": 8},
        "c2-standard-4": {"hourly_usd": 0.2088, "vcpu": 4, "memory_gb": 16},
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
            provider: "aws_ec2", "sakura_cloud", or "google_cloud"

        Returns:
            Dictionary of available instances with their specifications
        """
        if provider == "aws_ec2":
            result = {}
            for instance_type, pricing in self.EC2_PRICING.items():
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
        elif provider == "sakura_cloud":
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
        elif provider == "google_cloud":
            result = {}
            for instance_type, pricing in self.GCP_PRICING.items():
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
        else:
            return {}

    def recommend_instance_for_lambda(
        self, lambda_memory_mb: int
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Recommend VM instances equivalent to Lambda configuration

        Args:
            lambda_memory_mb: Lambda memory size in MB

        Returns:
            Dictionary with recommendations for both providers
        """
        lambda_memory_gb = lambda_memory_mb / 1024

        recommendations: Dict[str, List[Dict[str, Any]]] = {
            "aws_ec2": [],
            "sakura_cloud": [],
            "google_cloud": [],
        }

        # EC2 recommendations
        for instance_type, pricing in self.EC2_PRICING.items():
            if float(pricing["memory_gb"]) >= lambda_memory_gb:
                ec2_cost = self.get_ec2_cost(instance_type)
                if ec2_cost:
                    recommendations["aws_ec2"].append(
                        {
                            "instance_type": instance_type,
                            "memory_ratio": pricing["memory_gb"] / lambda_memory_gb,
                            **ec2_cost,
                        }
                    )

        # Sakura Cloud recommendations
        for instance_type, pricing in self.SAKURA_PRICING.items():  # type: ignore
            if float(pricing["memory_gb"]) >= lambda_memory_gb:
                sakura_cost = self.get_sakura_cost(instance_type)
                if sakura_cost:
                    recommendations["sakura_cloud"].append(
                        {
                            "instance_type": instance_type,
                            "memory_ratio": pricing["memory_gb"] / lambda_memory_gb,
                            **sakura_cost,
                        }
                    )

        # Google Cloud recommendations
        for instance_type, pricing in self.GCP_PRICING.items():
            if float(pricing["memory_gb"]) >= lambda_memory_gb:
                gcp_cost = self.get_gcp_cost(instance_type)
                if gcp_cost:
                    recommendations["google_cloud"].append(
                        {
                            "instance_type": instance_type,
                            "memory_ratio": pricing["memory_gb"] / lambda_memory_gb,
                            **gcp_cost,
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
    ) -> float:
        """
        Calculate egress cost for VM provider

        Args:
            provider: VM provider ("aws_ec2", "google_cloud", "sakura_cloud")
            monthly_executions: Number of executions per month
            egress_per_request_kb: KB transferred per request
            custom_rates: Optional custom egress rates

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

        egress_config = EgressConfig(
            executions_per_month=monthly_executions,
            transfer_kb_per_request=egress_per_request_kb,
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
        if config.provider == "aws_ec2":
            base_cost = self.get_ec2_cost(config.instance_type)
        elif config.provider == "sakura_cloud":
            base_cost = self.get_sakura_cost(config.instance_type)
        elif config.provider == "google_cloud":
            base_cost = self.get_gcp_cost(config.instance_type)
        else:
            return None

        if base_cost is None:
            return None

        # Calculate egress cost
        egress_cost = self.calculate_vm_egress_cost(
            config.provider,
            monthly_executions,
            egress_per_request_kb,
            custom_egress_rates,
            include_egress_free_tier,
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
