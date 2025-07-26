"""
Unit tests for Serverless cost calculation
Following t_wada TDD: Red -> Green -> Refactor

This test file drives the implementation of ServerlessCalculator class
Focusing on GCP Functions provider implementation (Phase 1A)
"""
import pytest

from app.models.serverless_calculator import (
    ServerlessCalculator,
    ServerlessConfig,
    ServerlessResult,
    GCPFunctionsProvider,
    AWSLambdaProvider,
)


class TestServerlessConfig:
    """Test ServerlessConfig data class"""

    def test_serverless_config_creation_minimal(self):
        """Test ServerlessConfig creation with minimal required fields"""
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=5.0,
            monthly_executions=1_000_000
        )
        
        assert config.provider == "gcp_functions"
        assert config.memory_mb == 512
        assert config.execution_time_seconds == 5.0
        assert config.monthly_executions == 1_000_000
        assert config.include_free_tier is True  # Default value
        assert config.cpu_count is None
        assert config.egress_per_request_kb == 0.0
        assert config.internet_transfer_ratio == 100.0
        assert config.exchange_rate == 150.0
        assert config.include_ecosystem_benefits is False

    def test_serverless_config_creation_full(self):
        """Test ServerlessConfig creation with all fields specified"""
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=1024,
            execution_time_seconds=10.0,
            monthly_executions=2_000_000,
            include_free_tier=False,
            cpu_count=1.0,
            egress_per_request_kb=50.0,
            internet_transfer_ratio=80.0,
            exchange_rate=145.0,
            include_ecosystem_benefits=True
        )
        
        assert config.provider == "gcp_functions"
        assert config.memory_mb == 1024
        assert config.execution_time_seconds == 10.0
        assert config.monthly_executions == 2_000_000
        assert config.include_free_tier is False
        assert config.cpu_count == 1.0
        assert config.egress_per_request_kb == 50.0
        assert config.internet_transfer_ratio == 80.0
        assert config.exchange_rate == 145.0
        assert config.include_ecosystem_benefits is True


class TestGCPFunctionsProvider:
    """Test Google Cloud Functions provider implementation"""

    def test_gcp_functions_provider_initialization(self):
        """Test GCPFunctionsProvider can be initialized"""
        provider = GCPFunctionsProvider()
        assert provider is not None

    def test_gcp_functions_calculate_cost_without_free_tier(self):
        """Test GCP Functions cost calculation without free tier"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=5.0,
            monthly_executions=3_000_000,  # Above 2M free tier
            include_free_tier=False,
            exchange_rate=150.0
        )
        
        result = provider.calculate_cost(config)
        
        # Verify result structure
        assert isinstance(result, ServerlessResult)
        assert result.provider == "gcp_functions"
        assert result.service_name == "Google Cloud Functions"
        
        # Calculate expected costs
        # Request: 3M * $0.0000004 = $1.20
        expected_request_cost = 3_000_000 * 0.0000004
        # Compute: (512/1024) * 5.0 * 3M = 7.5M GB-seconds * $0.0000025 = $18.75
        gb_seconds = (512 / 1024) * 5.0 * 3_000_000
        expected_compute_cost = gb_seconds * 0.0000025
        expected_total_usd = expected_request_cost + expected_compute_cost
        expected_total_jpy = expected_total_usd * 150.0
        
        assert result.total_cost_usd == pytest.approx(expected_total_usd, rel=1e-3)
        assert result.total_cost_jpy == pytest.approx(expected_total_jpy, rel=1e-3)
        assert result.breakdown["request_cost"] == pytest.approx(expected_request_cost, rel=1e-3)
        assert result.breakdown["compute_cost"] == pytest.approx(expected_compute_cost, rel=1e-3)

    def test_gcp_functions_calculate_cost_with_free_tier(self):
        """Test GCP Functions cost calculation with free tier applied"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=2.0,
            monthly_executions=3_000_000,  # Above 2M free tier
            include_free_tier=True,
            exchange_rate=150.0
        )
        
        result = provider.calculate_cost(config)
        
        # Calculate expected costs with free tier
        # Request: (3M - 2M free) * $0.0000004 = $0.40
        billable_requests = 3_000_000 - 2_000_000
        expected_request_cost = billable_requests * 0.0000004
        
        # Compute: (512/1024) * 2.0 * 3M = 3M GB-seconds, (3M - 400K free) * $0.0000025
        total_gb_seconds = (512 / 1024) * 2.0 * 3_000_000
        billable_gb_seconds = max(0, total_gb_seconds - 400_000)
        expected_compute_cost = billable_gb_seconds * 0.0000025
        
        expected_total_usd = expected_request_cost + expected_compute_cost
        
        assert result.total_cost_usd == pytest.approx(expected_total_usd, rel=1e-3)
        assert result.breakdown["request_cost"] == pytest.approx(expected_request_cost, rel=1e-3)
        assert result.breakdown["compute_cost"] == pytest.approx(expected_compute_cost, rel=1e-3)
        
        # Check free tier savings
        assert "request_savings" in result.free_tier_savings
        assert "compute_savings" in result.free_tier_savings
        assert result.free_tier_savings["request_savings"] > 0
        assert result.free_tier_savings["compute_savings"] > 0

    def test_gcp_functions_calculate_cost_within_free_tier(self):
        """Test GCP Functions cost calculation when usage is within free tier"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=128,
            execution_time_seconds=1.0,
            monthly_executions=1_000_000,  # Within 2M free tier
            include_free_tier=True,
            exchange_rate=150.0
        )
        
        result = provider.calculate_cost(config)
        
        # Should be $0 for both request and compute (within free tier)
        assert result.total_cost_usd == 0.0
        assert result.total_cost_jpy == 0.0
        assert result.breakdown["request_cost"] == 0.0
        assert result.breakdown["compute_cost"] == 0.0

    def test_gcp_functions_get_provider_info(self):
        """Test GCP Functions provider information"""
        provider = GCPFunctionsProvider()
        info = provider.get_provider_info()
        
        assert isinstance(info, dict)
        assert info["name"] == "Google Cloud Functions"
        assert info["pricing_model"] == "Request + GB-second"
        assert "2,000,000 requests" in info["free_tier"]
        assert "400,000 GB-seconds" in info["free_tier"]
        assert info["max_execution_time"] == 540  # 9 minutes
        assert info["max_memory"] == 8192

    def test_gcp_functions_validate_config_valid(self):
        """Test GCP Functions configuration validation for valid config"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=300.0,
            monthly_executions=1_000_000
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 0

    def test_gcp_functions_validate_config_invalid_memory(self):
        """Test GCP Functions configuration validation for invalid memory"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=64,  # Below minimum
            execution_time_seconds=300.0,
            monthly_executions=1_000_000
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert "Memory must be between 128 and 8,192 MB" in errors[0]

    def test_gcp_functions_validate_config_invalid_execution_time(self):
        """Test GCP Functions configuration validation for invalid execution time"""
        provider = GCPFunctionsProvider()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=1000.0,  # Above maximum
            monthly_executions=1_000_000
        )
        
        errors = provider.validate_config(config)
        assert len(errors) == 1
        assert "Execution time must be between 0.1 and 540 seconds" in errors[0]


class TestServerlessCalculator:
    """Test unified ServerlessCalculator class"""

    def test_serverless_calculator_initialization(self):
        """Test ServerlessCalculator can be initialized"""
        calculator = ServerlessCalculator()
        assert calculator is not None
        
        # Should have both AWS Lambda and GCP Functions providers
        supported_providers = calculator.get_supported_providers()
        assert "aws_lambda" in supported_providers
        assert "gcp_functions" in supported_providers

    def test_calculate_gcp_functions_success(self):
        """Test successful calculation for GCP Functions"""
        calculator = ServerlessCalculator()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=512,
            execution_time_seconds=5.0,
            monthly_executions=2_500_000,  # Above free tier
            include_free_tier=True,
            exchange_rate=150.0
        )
        
        result = calculator.calculate(config)
        
        assert isinstance(result, ServerlessResult)
        assert result.provider == "gcp_functions"
        assert result.service_name == "Google Cloud Functions"
        assert result.total_cost_usd > 0  # Should have cost above free tier
        assert result.total_cost_jpy > result.total_cost_usd  # JPY should be higher

    def test_calculate_aws_lambda_success(self):
        """Test successful calculation for AWS Lambda (existing functionality)"""
        calculator = ServerlessCalculator()
        config = ServerlessConfig(
            provider="aws_lambda",
            memory_mb=512,
            execution_time_seconds=10.0,
            monthly_executions=2_000_000,
            include_free_tier=True,
            exchange_rate=150.0
        )
        
        result = calculator.calculate(config)
        
        assert isinstance(result, ServerlessResult)
        assert result.provider == "aws_lambda"
        assert result.service_name == "AWS Lambda"
        assert result.total_cost_usd > 0

    def test_calculate_unsupported_provider(self):
        """Test calculation with unsupported provider raises error"""
        calculator = ServerlessCalculator()
        config = ServerlessConfig(
            provider="azure_functions",  # Not implemented yet
            memory_mb=512,
            execution_time_seconds=5.0,
            monthly_executions=1_000_000
        )
        
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate(config)
        
        assert "Provider 'azure_functions' not supported" in str(exc_info.value)

    def test_calculate_invalid_config(self):
        """Test calculation with invalid configuration raises error"""
        calculator = ServerlessCalculator()
        config = ServerlessConfig(
            provider="gcp_functions",
            memory_mb=64,  # Invalid - below minimum
            execution_time_seconds=5.0,
            monthly_executions=1_000_000
        )
        
        with pytest.raises(ValueError) as exc_info:
            calculator.calculate(config)
        
        assert "Configuration validation failed" in str(exc_info.value)

    def test_get_provider_info_gcp_functions(self):
        """Test getting provider info for GCP Functions"""
        calculator = ServerlessCalculator()
        info = calculator.get_provider_info("gcp_functions")
        
        assert isinstance(info, dict)
        assert info["name"] == "Google Cloud Functions"

    def test_get_provider_info_unsupported(self):
        """Test getting provider info for unsupported provider raises error"""
        calculator = ServerlessCalculator()
        
        with pytest.raises(ValueError) as exc_info:
            calculator.get_provider_info("azure_functions")
        
        assert "Provider 'azure_functions' not supported" in str(exc_info.value)

    def test_calculate_multiple_providers(self):
        """Test calculating costs for multiple configurations"""
        calculator = ServerlessCalculator()
        configs = [
            ServerlessConfig(
                provider="aws_lambda",
                memory_mb=512,
                execution_time_seconds=5.0,
                monthly_executions=1_000_000
            ),
            ServerlessConfig(
                provider="gcp_functions",
                memory_mb=512,
                execution_time_seconds=5.0,
                monthly_executions=1_000_000
            )
        ]
        
        results = calculator.calculate_multiple(configs)
        
        assert len(results) == 2
        assert results[0].provider == "aws_lambda"
        assert results[1].provider == "gcp_functions"
        assert all(isinstance(result, ServerlessResult) for result in results)


class TestServerlessResult:
    """Test ServerlessResult data class"""

    def test_serverless_result_creation(self):
        """Test ServerlessResult creation with all fields"""
        result = ServerlessResult(
            provider="gcp_functions",
            service_name="Google Cloud Functions",
            total_cost_usd=10.50,
            total_cost_jpy=1575.0,
            breakdown={"request_cost": 2.0, "compute_cost": 8.5},
            free_tier_savings={"request_savings": 0.8, "compute_savings": 1.0},
            resource_usage={
                "requests_used": 2_000_000,
                "requests_free": 2_000_000,
                "gb_seconds_used": 1_000_000,
                "gb_seconds_free": 400_000
            },
            features={
                "execution_model": "function_based",
                "cold_start_minimal": True,
                "automatic_scaling": True,
                "generous_free_tier": True
            }
        )
        
        assert result.provider == "gcp_functions"
        assert result.service_name == "Google Cloud Functions"
        assert result.total_cost_usd == 10.50
        assert result.total_cost_jpy == 1575.0
        assert result.breakdown["request_cost"] == 2.0
        assert result.breakdown["compute_cost"] == 8.5
        assert result.free_tier_savings["request_savings"] == 0.8
        assert result.free_tier_savings["compute_savings"] == 1.0
        assert result.resource_usage["requests_used"] == 2_000_000
        assert result.features["execution_model"] == "function_based"