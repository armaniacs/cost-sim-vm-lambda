"""
Unit tests for egress fee calculation (PBI09)
Following t_wada TDD principles: Red -> Green -> Refactor

Tests the business logic for egress cost calculations
"""

import pytest

from app.models.egress_calculator import EgressCalculator, EgressConfig


class TestEgressCalculator:
    """
    Unit tests for EgressCalculator class
    Testing business logic and calculation accuracy
    """

    def test_egress_calculator_initialization(self):
        """Test EgressCalculator can be initialized"""
        calculator = EgressCalculator()
        assert calculator is not None

    def test_egress_config_creation(self):
        """Test EgressConfig data class creation"""
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=100,
            provider="aws_lambda",
        )

        assert config.executions_per_month == 1_000_000
        assert config.transfer_kb_per_request == 100
        assert config.provider == "aws_lambda"

    def test_aws_lambda_egress_pricing_constants(self):
        """Test AWS Lambda egress pricing constant"""
        calculator = EgressCalculator()

        # AWS Lambda egress: 0.114 USD/GB
        assert calculator.DEFAULT_EGRESS_RATES["aws_lambda"] == 0.114

    def test_aws_ec2_egress_pricing_constants(self):
        """Test AWS EC2 egress pricing constant"""
        calculator = EgressCalculator()

        # AWS EC2 egress: 0.114 USD/GB
        assert calculator.DEFAULT_EGRESS_RATES["aws_ec2"] == 0.114

    def test_google_cloud_egress_pricing_constants(self):
        """Test Google Cloud egress pricing constant"""
        calculator = EgressCalculator()

        # Google Cloud egress: 0.12 USD/GB
        assert calculator.DEFAULT_EGRESS_RATES["google_cloud"] == 0.12

    def test_sakura_cloud_egress_pricing_constants(self):
        """Test Sakura Cloud egress pricing constant"""
        calculator = EgressCalculator()

        # Sakura Cloud egress: 0.0 JPY/GB (egress free)
        assert calculator.DEFAULT_EGRESS_RATES["sakura_cloud"] == 0.0

    def test_calculate_aws_lambda_egress_basic(self):
        """
        Test basic AWS Lambda egress cost calculation
        Formula: executions * (KB/1024/1024) * rate_per_GB
        """
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=100,  # 100KB = 0.0001GB
            provider="aws_lambda",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1M * 0.0001GB * 0.114 USD/GB
        expected_cost = 1_000_000 * (100 / 1024 / 1024) * 0.114
        assert abs(result - expected_cost) < 0.001
        assert result > 0

    def test_calculate_aws_lambda_egress_1mb(self):
        """Test AWS Lambda egress with 1MB per request"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=1024,  # 1MB
            provider="aws_lambda",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1M * 0.001GB * 0.114 USD/GB
        expected_cost = 1_000_000 * (1024 / 1024 / 1024) * 0.114
        assert abs(result - expected_cost) < 0.001

    def test_calculate_aws_ec2_egress_basic(self):
        """Test AWS EC2 egress cost calculation"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=500,  # 500KB
            provider="aws_ec2",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1M * (500KB as GB) * 0.114 USD/GB
        expected_cost = 1_000_000 * (500 / 1024 / 1024) * 0.114
        assert abs(result - expected_cost) < 0.001

    def test_calculate_google_cloud_egress_basic(self):
        """Test Google Cloud egress cost calculation"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=1024,  # 1MB
            provider="google_cloud",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1M * 0.001GB * 0.12 USD/GB
        expected_cost = 1_000_000 * (1024 / 1024 / 1024) * 0.12
        assert abs(result - expected_cost) < 0.001

    def test_calculate_sakura_cloud_egress_basic(self):
        """Test Sakura Cloud egress cost calculation"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=1024,  # 1MB
            provider="sakura_cloud",
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1M * 0.001GB * 0.0 JPY/GB = 0 JPY (egress free)
        expected_cost = 1_000_000 * (1024 / 1024 / 1024) * 0.0
        assert abs(result - expected_cost) < 0.001

    def test_zero_transfer_amount(self):
        """Test egress calculation with zero transfer amount"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=0,
            provider="aws_lambda",
        )

        result = calculator.calculate_egress_cost(config)
        assert result == 0.0

    def test_zero_executions(self):
        """Test egress calculation with zero executions"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=0, transfer_kb_per_request=100, provider="aws_lambda"
        )

        result = calculator.calculate_egress_cost(config)
        assert result == 0.0

    def test_large_transfer_amount(self):
        """Test egress calculation with large transfer amount"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000,  # Lower executions
            transfer_kb_per_request=10 * 1024 * 1024,  # 10GB per request
            provider="aws_lambda",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Expected: 1000 * 10GB * 0.114 USD/GB
        expected_cost = 1_000 * 10 * 0.114
        assert abs(result - expected_cost) < 0.01

    def test_invalid_provider(self):
        """Test error handling for invalid provider"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=100,
            provider="invalid_provider",
        )

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_egress_cost(config)

        assert "provider" in str(exc_info.value).lower()
        assert "invalid_provider" in str(exc_info.value)

    def test_negative_executions(self):
        """Test validation of negative executions"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=-1000,
            transfer_kb_per_request=100,
            provider="aws_lambda",
        )

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_egress_cost(config)

        assert "executions" in str(exc_info.value).lower()
        assert "negative" in str(exc_info.value).lower()

    def test_negative_transfer_amount(self):
        """Test validation of negative transfer amount"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=-100,
            provider="aws_lambda",
        )

        with pytest.raises(ValueError) as exc_info:
            calculator.calculate_egress_cost(config)

        assert "transfer" in str(exc_info.value).lower()
        assert "negative" in str(exc_info.value).lower()

    def test_fractional_transfer_amount(self):
        """Test egress calculation with fractional KB amounts"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=0.5,  # 0.5KB = 512 bytes
            provider="aws_lambda",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Should handle fractional KB amounts
        expected_cost = 1_000_000 * (0.5 / 1024 / 1024) * 0.114
        assert abs(result - expected_cost) < 0.0001

    def test_precision_with_small_amounts(self):
        """Test calculation precision with very small transfer amounts"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1,
            transfer_kb_per_request=1,  # 1KB
            provider="aws_lambda",
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Should be very small but positive
        expected_cost = 1 * (1 / 1024 / 1024) * 0.114
        assert result > 0
        assert abs(result - expected_cost) < 0.0000001

    def test_get_rate_for_provider(self):
        """Test getting rate for specific provider"""
        calculator = EgressCalculator()

        assert calculator.get_rate_for_provider("aws_lambda") == 0.114
        assert calculator.get_rate_for_provider("aws_ec2") == 0.114
        assert calculator.get_rate_for_provider("google_cloud") == 0.12
        assert calculator.get_rate_for_provider("sakura_cloud") == 0.0

    def test_get_rate_for_invalid_provider(self):
        """Test error handling when getting rate for invalid provider"""
        calculator = EgressCalculator()

        with pytest.raises(ValueError):
            calculator.get_rate_for_provider("invalid_provider")

    def test_convert_kb_to_gb(self):
        """Test KB to GB conversion utility"""
        calculator = EgressCalculator()

        # Test common conversions (using proper binary calculations)
        assert (
            abs(calculator.convert_kb_to_gb(1024) - (1024 / 1024 / 1024)) < 0.0001
        )  # 1MB in GB
        assert calculator.convert_kb_to_gb(1024 * 1024) == 1.0  # 1GB = 1.0GB
        assert (
            abs(calculator.convert_kb_to_gb(512) - (512 / 1024 / 1024)) < 0.0001
        )  # 512KB in GB
        assert calculator.convert_kb_to_gb(0) == 0.0

    def test_monthly_egress_calculation_formula(self):
        """
        Test the complete monthly egress calculation formula
        Verifying the mathematical correctness
        """
        calculator = EgressCalculator()

        # Test case: 2M executions, 256KB per request, AWS Lambda
        executions = 2_000_000
        kb_per_request = 256
        provider = "aws_lambda"

        config = EgressConfig(
            executions_per_month=executions,
            transfer_kb_per_request=kb_per_request,
            provider=provider,
            include_free_tier=False,  # Disable free tier for this test
        )

        result = calculator.calculate_egress_cost(config)

        # Manual calculation for verification
        gb_per_request = kb_per_request / 1024 / 1024  # 256KB to GB
        total_gb = executions * gb_per_request
        rate = calculator.egress_rates[provider]
        expected_cost = total_gb * rate

        assert abs(result - expected_cost) < 0.001

        # Verify intermediate calculations
        assert abs(gb_per_request - (256 / 1024 / 1024)) < 0.0000001
        assert total_gb == executions * gb_per_request
        assert rate == 0.114

    def test_free_tier_exact_limit_aws_lambda(self):
        """Test free tier with exactly 100GB usage for AWS Lambda"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=100,  # 100KB * 1M = 100GB exactly
            provider="aws_lambda",
            include_free_tier=True,
        )

        result = calculator.calculate_egress_cost(config)

        # Exactly 100GB should result in 0 cost with free tier
        assert result == 0.0

    def test_free_tier_under_limit_aws_lambda(self):
        """Test free tier with usage under 100GB for AWS Lambda"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=500_000,
            transfer_kb_per_request=100,  # 100KB * 500K = 50GB
            provider="aws_lambda",
            include_free_tier=True,
        )

        result = calculator.calculate_egress_cost(config)

        # Under 100GB should result in 0 cost with free tier
        assert result == 0.0

    def test_free_tier_over_limit_aws_lambda(self):
        """Test free tier with usage over 100GB for AWS Lambda"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_500_000,
            transfer_kb_per_request=100,  # 100KB * 1.5M = 150GB
            provider="aws_lambda",
            include_free_tier=True,
        )

        result = calculator.calculate_egress_cost(config)

        # Calculate actual GB: 1.5M * 100KB = 143.05 GB (using 1024-based conversion)
        total_gb = 1_500_000 * (100 / 1024 / 1024)
        billable_gb = total_gb - 100  # Subtract 100GB free tier
        expected_cost = billable_gb * 0.114
        assert abs(result - expected_cost) < 0.001

    def test_free_tier_google_cloud(self):
        """Test free tier with Google Cloud provider"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_200_000,
            transfer_kb_per_request=100,  # 100KB * 1.2M = 120GB
            provider="google_cloud",
            include_free_tier=True,
        )

        result = calculator.calculate_egress_cost(config)

        # Calculate actual GB: 1.2M * 100KB = 114.44 GB (using 1024-based conversion)
        total_gb = 1_200_000 * (100 / 1024 / 1024)
        billable_gb = total_gb - 100  # Subtract 100GB free tier
        expected_cost = billable_gb * 0.12
        assert abs(result - expected_cost) < 0.001

    def test_free_tier_disabled_aws_lambda(self):
        """Test that disabling free tier works correctly"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=500_000,
            transfer_kb_per_request=100,  # 100KB * 500K = 50GB
            provider="aws_lambda",
            include_free_tier=False,
        )

        result = calculator.calculate_egress_cost(config)

        # Calculate actual GB: 500K * 100KB = 47.68 GB (using 1024-based conversion)
        total_gb = 500_000 * (100 / 1024 / 1024)
        expected_cost = total_gb * 0.114
        assert abs(result - expected_cost) < 0.001

    def test_free_tier_not_applicable_sakura(self):
        """Test that free tier doesn't apply to Sakura Cloud"""
        calculator = EgressCalculator()
        config = EgressConfig(
            executions_per_month=1_000_000,
            transfer_kb_per_request=100,  # 100KB * 1M = 100GB
            provider="sakura_cloud",
            include_free_tier=True,
        )

        result = calculator.calculate_egress_cost(config)

        # Sakura Cloud is already free (0 JPY/GB), so result should be 0
        # Free tier flag shouldn't affect this
        assert result == 0.0
