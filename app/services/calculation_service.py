"""
Shared calculation service for cost computations
Reduces code duplication and provides consistent calculation logic
"""

from typing import Any, Dict, Optional

from app.services.service_container import (
    get_lambda_calculator,
    get_serverless_calculator,
    get_vm_calculator,
)


class CalculationService:
    """Centralized service for all cost calculations"""

    def __init__(self) -> None:
        """Initialize the calculation service"""

    def calculate_lambda_cost(
        self,
        data: Dict[str, Any],
        custom_egress_rates: Optional[Dict[str, float]] = None,
        include_egress_free_tier: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate AWS Lambda costs with validation

        Args:
            data: Input data dictionary
            custom_egress_rates: Optional custom egress rates
            include_egress_free_tier: Include egress free tier calculation

        Returns:
            Calculation results dictionary

        Raises:
            ValidationError: If input validation fails
        """
        from app.models.lambda_calculator import LambdaConfig
        from app.utils.validation import validate_lambda_inputs

        # Validate inputs
        validated_data = validate_lambda_inputs(data)

        # Create configuration
        config = LambdaConfig(
            memory_mb=validated_data["memory_mb"],
            execution_time_seconds=validated_data["execution_time_seconds"],
            monthly_executions=validated_data["monthly_executions"],
            include_free_tier=validated_data["include_free_tier"],
            egress_per_request_kb=validated_data.get("egress_per_request_kb", 0.0),
            internet_transfer_ratio=validated_data.get(
                "internet_transfer_ratio", 100.0
            ),
        )

        # Get calculator and perform calculation
        calculator = get_lambda_calculator()
        result = calculator.calculate_total_cost(
            config, custom_egress_rates, include_egress_free_tier
        )

        return result

    def calculate_vm_cost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate VM costs with validation

        Args:
            data: Input data dictionary

        Returns:
            Calculation results dictionary

        Raises:
            ValidationError: If input validation fails
        """
        from app.utils.validation import validate_vm_inputs

        # Validate inputs
        validated_data = validate_vm_inputs(data)

        # Get calculator and perform calculation
        calculator = get_vm_calculator()
        result = calculator.calculate_cost(validated_data)

        return result

    def calculate_serverless_cost(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate serverless costs with validation

        Args:
            data: Input data dictionary

        Returns:
            Calculation results dictionary

        Raises:
            ValidationError: If input validation fails
        """
        from app.utils.validation import validate_serverless_inputs

        # Validate inputs
        validated_data = validate_serverless_inputs(data)

        # Get calculator and perform calculation
        calculator = get_serverless_calculator()
        result = calculator.calculate(validated_data)

        return result

    def calculate_comparison(
        self,
        lambda_data: Dict[str, Any],
        vm_data: Dict[str, Any],
        include_break_even: bool = True,
    ) -> Dict[str, Any]:
        """
        Calculate cost comparison between Lambda and VM

        Args:
            lambda_data: Lambda configuration data
            vm_data: VM configuration data
            include_break_even: Include break-even analysis

        Returns:
            Comparison results dictionary
        """
        # Calculate both costs
        lambda_result = self.calculate_lambda_cost(lambda_data)
        vm_result = self.calculate_vm_cost(vm_data)

        comparison = {
            "lambda": lambda_result,
            "vm": vm_result,
            "cost_difference": lambda_result["total_cost"] - vm_result["total_cost"],
            "cheaper_option": (
                "lambda"
                if lambda_result["total_cost"] < vm_result["total_cost"]
                else "vm"
            ),
        }

        if include_break_even:
            # Calculate break-even point (simplified)
            break_even_executions = self._calculate_break_even_point(
                lambda_data, vm_data
            )
            comparison["break_even_executions"] = break_even_executions

        return comparison

    def _calculate_break_even_point(
        self, lambda_data: Dict[str, Any], vm_data: Dict[str, Any]
    ) -> Optional[int]:
        """
        Calculate break-even point between Lambda and VM costs

        Args:
            lambda_data: Lambda configuration data
            vm_data: VM configuration data

        Returns:
            Break-even execution count or None if not calculable
        """
        try:
            # Simplified break-even calculation
            # This would need more sophisticated logic for real use
            vm_monthly_cost = vm_data.get("monthly_cost", 0)
            lambda_per_execution = lambda_data.get("cost_per_execution", 0)

            if lambda_per_execution > 0:
                return int(vm_monthly_cost / lambda_per_execution)

            return None
        except (ValueError, TypeError):
            return None


# Global calculation service instance
_calculation_service = CalculationService()


def get_calculation_service() -> CalculationService:
    """Get the global calculation service instance"""
    return _calculation_service
