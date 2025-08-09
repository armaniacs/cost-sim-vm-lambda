"""
Unit tests for Lambda cost calculation
Following t_wada TDD: Red -> Green -> Refactor

This test file drives the implementation of LambdaCalculator class
"""

import pytest

from app.models.lambda_calculator import LambdaCalculator, LambdaConfig


class TestLambdaCalculator:
    """Test AWS Lambda cost calculation logic"""

    def test_lambda_calculator_initialization(self):
        """Test LambdaCalculator can be initialized"""
        calculator = LambdaCalculator()
        assert calculator is not None

    def test_lambda_config_creation(self):
        """Test LambdaConfig data class creation"""
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=1_000_000,
            include_free_tier=True,
        )
        assert config.memory_mb == 512
        assert config.execution_time_seconds == 10
        assert config.monthly_executions == 1_000_000
        assert config.include_free_tier is True

    def test_calculate_request_charges_without_free_tier(self):
        """Test request charges calculation without free tier"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,
            include_free_tier=False,
        )

        # 2M executions * $0.20 / 1M = $0.40
        expected_charges = 0.40
        actual_charges = calculator.calculate_request_charges(config)
        assert actual_charges == pytest.approx(expected_charges, rel=1e-3)

    def test_calculate_request_charges_with_free_tier(self):
        """Test request charges calculation with free tier applied"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,
            include_free_tier=True,
        )

        # (2M - 1M free) executions * $0.20 / 1M = $0.20
        expected_charges = 0.20
        actual_charges = calculator.calculate_request_charges(config)
        assert actual_charges == pytest.approx(expected_charges, rel=1e-3)

    def test_calculate_request_charges_within_free_tier(self):
        """Test request charges when executions are within free tier"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=500_000,
            include_free_tier=True,
        )

        # Within free tier, should be $0
        expected_charges = 0.0
        actual_charges = calculator.calculate_request_charges(config)
        assert actual_charges == expected_charges

    def test_calculate_gb_seconds(self):
        """Test GB-seconds calculation"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=1_000_000,
            include_free_tier=True,
        )

        # (512MB / 1024) * 10s * 1M executions = 5,000,000 GB-seconds
        expected_gb_seconds = 5_000_000.0
        actual_gb_seconds = calculator.calculate_gb_seconds(config)
        assert actual_gb_seconds == expected_gb_seconds

    def test_calculate_compute_charges_without_free_tier(self):
        """Test compute charges calculation without free tier"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=1024,
            execution_time_seconds=5,
            monthly_executions=1_000_000,
            include_free_tier=False,
        )

        # 1GB * 5s * 1M executions = 5M GB-seconds
        # 5M * $0.0000166667 = $83.33
        gb_seconds = 5_000_000.0
        expected_charges = gb_seconds * 0.0000166667
        actual_charges = calculator.calculate_compute_charges(config)
        assert actual_charges == pytest.approx(expected_charges, rel=1e-3)

    def test_calculate_compute_charges_with_free_tier(self):
        """Test compute charges calculation with free tier applied"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=1,
            monthly_executions=1_000_000,
            include_free_tier=True,
        )

        # 0.5GB * 1s * 1M executions = 500K GB-seconds
        # (500K - 400K free) = 100K GB-seconds
        # 100K * $0.0000166667 = $1.67
        billable_gb_seconds = 100_000.0
        expected_charges = billable_gb_seconds * 0.0000166667
        actual_charges = calculator.calculate_compute_charges(config)
        assert actual_charges == pytest.approx(expected_charges, rel=1e-3)

    def test_calculate_total_cost(self):
        """Test total cost calculation combining request and compute charges"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=512,
            execution_time_seconds=10,
            monthly_executions=2_000_000,
            include_free_tier=True,
        )

        # Request: (2M - 1M) * $0.20 / 1M = $0.20
        # Compute: (5M - 400K) GB-seconds * $0.0000166667 = $76.67
        # Total: $76.87
        result = calculator.calculate_total_cost(config)

        assert "request_charges" in result
        assert "compute_charges" in result
        assert "total_cost" in result
        assert "gb_seconds" in result
        assert "configuration" in result

        expected_total = result["request_charges"] + result["compute_charges"]
        assert result["total_cost"] == expected_total

    def test_calculate_total_cost_structure(self):
        """Test that calculate_total_cost returns proper structure"""
        calculator = LambdaCalculator()
        config = LambdaConfig(
            memory_mb=128,
            execution_time_seconds=1,
            monthly_executions=100_000,
            include_free_tier=True,
        )

        result = calculator.calculate_total_cost(config)

        # Verify result structure
        assert isinstance(result, dict)
        assert "request_charges" in result
        assert "compute_charges" in result
        assert "total_cost" in result
        assert "gb_seconds" in result
        assert "configuration" in result

        # Verify types
        assert isinstance(result["request_charges"], (int, float))
        assert isinstance(result["compute_charges"], (int, float))
        assert isinstance(result["total_cost"], (int, float))
        assert isinstance(result["gb_seconds"], (int, float))
        assert isinstance(result["configuration"], dict)
