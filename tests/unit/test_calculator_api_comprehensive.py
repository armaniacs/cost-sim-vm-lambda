"""
Comprehensive unit tests for Calculator API
Tests all endpoints with success and error paths for maximum coverage
"""

import json
from unittest.mock import Mock, patch

import pytest

# Import what we can from the actual implementation
try:
    from app.models.lambda_calculator import LambdaConfig
    from app.models.vm_calculator import VMConfig
    from app.utils.validation import ValidationError
except ImportError as e:
    # Skip tests if imports fail
    pytest.skip(f"Calculator API module not available: {e}", allow_module_level=True)


class TestLambdaCostEndpoint:
    """Test /api/v1/calculator/lambda endpoint comprehensively"""

    def test_lambda_cost_success_minimal(self, client):
        """Test successful Lambda cost calculation with minimal data"""
        payload = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
        }

        # Mock the calculator to return predictable results
        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.return_value = {
                "total_cost_usd": 0.02,
                "total_cost_jpy": 3.0,
                "compute_cost_usd": 0.01,
                "request_cost_usd": 0.01,
            }

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "data" in data
            assert data["data"]["total_cost_usd"] == 0.02

            # Verify calculator was called with correct config
            mock_calc.calculate_total_cost.assert_called_once()
            call_args = mock_calc.calculate_total_cost.call_args
            config = call_args[0][0]
            assert isinstance(config, LambdaConfig)
            assert config.memory_mb == 512

    def test_lambda_cost_success_with_egress(self, client):
        """Test Lambda cost calculation with egress parameters"""
        payload = {
            "memory_mb": 1024,
            "execution_time_seconds": 2.5,
            "monthly_executions": 100000,
            "include_free_tier": False,
            "egress_per_request_kb": 50.0,
            "internet_transfer_ratio": 75.0,
        }

        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.return_value = {
                "total_cost_usd": 15.45,
                "compute_cost_usd": 12.30,
                "request_cost_usd": 2.00,
                "egress_cost_usd": 1.15,
            }

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["egress_cost_usd"] == 1.15

    def test_lambda_cost_with_custom_egress_rates(self, client):
        """Test Lambda cost with custom egress rates"""
        payload = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 10000,
            "include_free_tier": True,
            "custom_egress_rates": {"us-east-1": 0.09, "ap-northeast-1": 0.12},
            "include_egress_free_tier": False,
        }

        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.return_value = {
                "total_cost_usd": 5.23,
                "total_cost_jpy": 785.0,
            }

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

            # Verify custom egress rates were passed
            call_args = mock_calc.calculate_total_cost.call_args
            custom_rates = (
                call_args[0][1]
                if len(call_args[0]) > 1
                else call_args[1].get("custom_egress_rates")
            )
            assert custom_rates == payload["custom_egress_rates"]

    def test_lambda_cost_validation_error(self, client):
        """Test Lambda endpoint with validation error"""
        payload = {
            "memory_mb": 50,  # Below minimum
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
        }

        # Mock validation to raise ValidationError
        with patch("app.api.calculator_api.validate_lambda_inputs") as mock_validate:
            mock_validate.side_effect = ValidationError(
                "Memory size must be between 128MB and 10240MB"
            )

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Memory size must be between" in data["error"]

    def test_lambda_cost_calculator_exception(self, client):
        """Test Lambda endpoint with calculator exception"""
        payload = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
        }

        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.side_effect = Exception("Calculator error")

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "Internal server error" in data["error"]


class TestVMCostEndpoint:
    """Test /api/v1/calculator/vm endpoint comprehensively"""

    def test_vm_cost_success_basic(self, client):
        """Test successful VM cost calculation (basic)"""
        payload = {
            "provider": "aws_ec2",
            "instance_type": "t3.micro",
            "region": "us-east-1",
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.calculate_vm_cost.return_value = {
                "hourly_cost_usd": 0.0104,
                "monthly_cost_usd": 7.59,
                "monthly_cost_jpy": 1138.0,
            }

            response = client.post(
                "/api/v1/calculator/vm",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["hourly_cost_usd"] == 0.0104

            # Verify calculator was called with correct config
            mock_calc.calculate_vm_cost.assert_called_once()
            call_args = mock_calc.calculate_vm_cost.call_args
            config = call_args[0][0]
            assert isinstance(config, VMConfig)
            assert config.provider == "aws_ec2"
            assert config.instance_type == "t3.micro"

    def test_vm_cost_success_with_egress(self, client):
        """Test VM cost calculation with egress"""
        payload = {
            "provider": "sakura_cloud",
            "instance_type": "1core-1gb",
            "region": "is1b",
            "monthly_executions": 50000,
            "egress_per_request_kb": 25.0,
            "internet_transfer_ratio": 80.0,
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.get_monthly_cost_with_egress.return_value = {
                "monthly_cost_usd": 25.40,
                "vm_cost_usd": 23.50,
                "egress_cost_usd": 1.90,
            }

            response = client.post(
                "/api/v1/calculator/vm",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["egress_cost_usd"] == 1.90

            # Verify egress method was called
            mock_calc.get_monthly_cost_with_egress.assert_called_once()

    def test_vm_cost_google_cloud_success(self, client):
        """Test VM cost for Google Cloud"""
        payload = {
            "provider": "google_cloud",
            "instance_type": "e2-micro",
            "region": "asia-northeast1",
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.calculate_vm_cost.return_value = {
                "hourly_cost_usd": 0.006,
                "monthly_cost_usd": 4.38,
            }

            response = client.post(
                "/api/v1/calculator/vm",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_vm_cost_invalid_provider_result(self, client):
        """Test VM endpoint when calculator returns None"""
        payload = {
            "provider": "invalid_provider",
            "instance_type": "invalid.type",
            "region": "invalid-region",
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.calculate_vm_cost.return_value = None

            response = client.post(
                "/api/v1/calculator/vm",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Invalid provider" in data["error"]

    def test_vm_cost_with_custom_egress_rates(self, client):
        """Test VM cost with custom egress rates"""
        payload = {
            "provider": "aws_ec2",
            "instance_type": "t3.small",
            "region": "ap-northeast-1",
            "monthly_executions": 25000,
            "egress_per_request_kb": 40.0,
            "custom_egress_rates": {"ap-northeast-1": 0.114},
            "include_egress_free_tier": True,
            "internet_transfer_ratio": 90.0,
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.get_monthly_cost_with_egress.return_value = {
                "monthly_cost_usd": 18.75
            }

            response = client.post(
                "/api/v1/calculator/vm",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestComparisonEndpoint:
    """Test /api/v1/calculator/comparison endpoint"""

    def test_comparison_success(self, client):
        """Test successful cost comparison"""
        payload = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 2.0,
                "monthly_executions": 100000,
                "include_free_tier": True,
            },
            "vm_config": {
                "provider": "aws_ec2",
                "instance_type": "t3.micro",
                "region": "us-east-1",
            },
        }

        with (
            patch("app.api.calculator_api.lambda_calc") as mock_lambda,
            patch("app.api.calculator_api.vm_calc") as mock_vm,
        ):

            mock_lambda.calculate_total_cost.return_value = {"total_cost_usd": 12.34}
            mock_vm.calculate_vm_cost.return_value = {"monthly_cost_usd": 7.59}

            response = client.post(
                "/api/v1/calculator/comparison",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "lambda_cost" in data["data"]
            assert "vm_cost" in data["data"]
            assert "breakeven_analysis" in data["data"]

    def test_comparison_vm_calculator_returns_none(self, client):
        """Test comparison when VM calculator returns None"""
        payload = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 1.0,
                "monthly_executions": 10000,
                "include_free_tier": True,
            },
            "vm_config": {
                "provider": "invalid_provider",
                "instance_type": "invalid.type",
                "region": "invalid-region",
            },
        }

        with patch("app.api.calculator_api.vm_calc") as mock_vm:
            mock_vm.calculate_vm_cost.return_value = None

            response = client.post(
                "/api/v1/calculator/comparison",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Invalid VM configuration" in data["error"]


class TestCSVExportEndpoint:
    """Test /api/v1/calculator/export_csv endpoint"""

    def test_csv_export_success_lambda(self, client):
        """Test successful CSV export for Lambda calculations"""
        payload = {
            "calculations": [
                {
                    "type": "lambda",
                    "memory_mb": 512,
                    "execution_time_seconds": 1.0,
                    "monthly_executions": 10000,
                    "total_cost_usd": 2.15,
                    "total_cost_jpy": 322.5,
                }
            ],
            "filename": "lambda_costs",
        }

        response = client.post(
            "/api/v1/calculator/export_csv",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        # Response should be CSV data
        assert "text/csv" in response.content_type
        assert "attachment" in response.headers["Content-Disposition"]

        # Verify CSV content contains expected data
        csv_content = response.data.decode("utf-8")
        assert "Type,Memory (MB)" in csv_content
        assert "lambda,512" in csv_content

    def test_csv_export_success_vm(self, client):
        """Test CSV export for VM calculations"""
        payload = {
            "calculations": [
                {
                    "type": "vm",
                    "provider": "aws_ec2",
                    "instance_type": "t3.micro",
                    "region": "us-east-1",
                    "monthly_cost_usd": 7.59,
                    "monthly_cost_jpy": 1138.0,
                }
            ]
        }

        response = client.post(
            "/api/v1/calculator/export_csv",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert "text/csv" in response.content_type

        csv_content = response.data.decode("utf-8")
        assert "vm,aws_ec2" in csv_content

    def test_csv_export_mixed_calculations(self, client):
        """Test CSV export with mixed calculation types"""
        payload = {
            "calculations": [
                {"type": "lambda", "memory_mb": 1024, "total_cost_usd": 5.50},
                {
                    "type": "vm",
                    "provider": "sakura_cloud",
                    "instance_type": "2core-4gb",
                    "monthly_cost_usd": 25.00,
                },
                {
                    "type": "comparison",
                    "lambda_cost": 5.50,
                    "vm_cost": 25.00,
                    "recommendation": "Lambda",
                },
            ],
            "filename": "mixed_analysis",
        }

        response = client.post(
            "/api/v1/calculator/export_csv",
            data=json.dumps(payload),
            content_type="application/json",
        )

        assert response.status_code == 200
        csv_content = response.data.decode("utf-8")
        assert "lambda,1024" in csv_content
        assert "sakura_cloud" in csv_content
        assert "comparison" in csv_content


class TestInstancesEndpoint:
    """Test /api/v1/calculator/instances endpoint"""

    def test_get_available_instances_success(self, client):
        """Test successful retrieval of available instances"""
        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.get_available_instances.return_value = {
                "aws_ec2": {
                    "us-east-1": ["t3.micro", "t3.small", "t3.medium"],
                    "ap-northeast-1": ["t3.micro", "t3.small"],
                },
                "sakura_cloud": {"is1b": ["1core-1gb", "2core-4gb"]},
            }

            response = client.get("/api/v1/calculator/instances")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert "aws_ec2" in data["data"]
            assert "sakura_cloud" in data["data"]

    def test_get_available_instances_with_provider_filter(self, client):
        """Test instances endpoint with provider filter"""
        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.get_available_instances.return_value = {
                "aws_ec2": {"us-east-1": ["t3.micro", "t3.small"]}
            }

            response = client.get("/api/v1/calculator/instances?provider=aws_ec2")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

            # Verify provider filter was applied
            mock_calc.get_available_instances.assert_called_once_with("aws_ec2")


class TestRecommendEndpoint:
    """Test /api/v1/calculator/recommend endpoint"""

    def test_recommend_instances_success(self, client):
        """Test successful instance recommendations"""
        payload = {
            "budget_usd": 50.0,
            "cpu_cores": 2,
            "memory_gb": 4,
            "provider": "aws_ec2",
            "region": "us-east-1",
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.recommend_instances.return_value = [
                {
                    "instance_type": "t3.medium",
                    "monthly_cost_usd": 30.24,
                    "cpu_cores": 2,
                    "memory_gb": 4.0,
                    "match_score": 0.95,
                },
                {
                    "instance_type": "t3.small",
                    "monthly_cost_usd": 15.12,
                    "cpu_cores": 2,
                    "memory_gb": 2.0,
                    "match_score": 0.75,
                },
            ]

            response = client.post(
                "/api/v1/calculator/recommend",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["match_score"] == 0.95

    def test_recommend_instances_no_matches(self, client):
        """Test recommendations when no instances match"""
        payload = {
            "budget_usd": 1.0,  # Very low budget
            "cpu_cores": 16,  # High requirements
            "memory_gb": 64,
            "provider": "aws_ec2",
        }

        with patch("app.api.calculator_api.vm_calc") as mock_calc:
            mock_calc.recommend_instances.return_value = []

            response = client.post(
                "/api/v1/calculator/recommend",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"] == []


class TestCurrencyConvertEndpoint:
    """Test /api/v1/calculator/currency/convert endpoint"""

    def test_currency_convert_success(self, client):
        """Test successful currency conversion"""
        payload = {"amount": 100.0, "from_currency": "USD", "to_currency": "JPY"}

        with patch("app.api.calculator_api.requests") as mock_requests:
            mock_response = Mock()
            mock_response.json.return_value = {"conversion_rates": {"JPY": 150.0}}
            mock_response.raise_for_status.return_value = None
            mock_requests.get.return_value = mock_response

            response = client.post(
                "/api/v1/calculator/currency/convert",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["converted_amount"] == 15000.0
            assert data["data"]["exchange_rate"] == 150.0

    def test_currency_convert_api_error(self, client):
        """Test currency conversion with API error"""
        payload = {"amount": 50.0, "from_currency": "USD", "to_currency": "EUR"}

        with patch("app.api.calculator_api.requests") as mock_requests:
            mock_requests.get.side_effect = Exception("API timeout")

            response = client.post(
                "/api/v1/calculator/currency/convert",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "Error converting currency" in data["error"]


class TestServerlessEndpoint:
    """Test /api/v1/calculator/serverless endpoint"""

    def test_serverless_cost_gcp_functions_success(self, client):
        """Test successful serverless cost calculation for GCP Functions"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 256,
            "execution_time_seconds": 1.5,
            "monthly_executions": 50000,
            "include_free_tier": True,
        }

        with patch("app.api.calculator_api.serverless_calc") as mock_calc:
            mock_calc.calculate.return_value = {
                "provider": "gcp_functions",
                "total_cost_usd": 3.45,
                "breakdown": {"request_cost": 0.45, "compute_cost": 3.00},
            }

            response = client.post(
                "/api/v1/calculator/serverless",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert data["data"]["provider"] == "gcp_functions"
            assert data["data"]["total_cost_usd"] == 3.45

    def test_serverless_cost_azure_functions_success(self, client):
        """Test serverless cost for Azure Functions"""
        payload = {
            "provider": "azure_functions",
            "memory_mb": 512,
            "execution_time_seconds": 2.0,
            "monthly_executions": 100000,
            "include_free_tier": False,
        }

        with patch("app.api.calculator_api.serverless_calc") as mock_calc:
            mock_calc.calculate.return_value = {
                "provider": "azure_functions",
                "total_cost_usd": 8.75,
            }

            response = client.post(
                "/api/v1/calculator/serverless",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

    def test_serverless_validation_error(self, client):
        """Test serverless endpoint with validation error"""
        payload = {
            "provider": "invalid_provider",
            "memory_mb": 128,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
        }

        with patch(
            "app.api.calculator_api.validate_serverless_inputs"
        ) as mock_validate:
            mock_validate.side_effect = ValidationError(
                "Unsupported provider: invalid_provider"
            )

            response = client.post(
                "/api/v1/calculator/serverless",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 400
            data = json.loads(response.data)
            assert "Unsupported provider" in data["error"]


class TestServerlessProvidersEndpoint:
    """Test /api/v1/calculator/serverless/providers endpoint"""

    def test_get_serverless_providers_success(self, client):
        """Test successful retrieval of serverless providers"""
        with patch("app.api.calculator_api.serverless_calc") as mock_calc:
            mock_calc.get_supported_providers.return_value = [
                {
                    "provider": "gcp_functions",
                    "name": "Google Cloud Functions",
                    "regions": ["us-central1", "asia-northeast1"],
                    "memory_options": [128, 256, 512, 1024, 2048],
                },
                {
                    "provider": "azure_functions",
                    "name": "Azure Functions",
                    "regions": ["eastus", "japaneast"],
                    "memory_options": [128, 256, 512, 1024],
                },
            ]

            response = client.get("/api/v1/calculator/serverless/providers")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["data"][0]["provider"] == "gcp_functions"

    def test_get_serverless_providers_with_filter(self, client):
        """Test providers endpoint with region filter"""
        with patch("app.api.calculator_api.serverless_calc") as mock_calc:
            mock_calc.get_supported_providers.return_value = [
                {"provider": "gcp_functions", "regions": ["asia-northeast1"]}
            ]

            response = client.get(
                "/api/v1/calculator/serverless/providers?region=asia-northeast1"
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True


class TestCalculatorAPIErrorHandling:
    """Test general error handling across all endpoints"""

    def test_malformed_json_handling(self, client):
        """Test handling of malformed JSON across endpoints"""
        endpoints = [
            "/api/v1/calculator/lambda",
            "/api/v1/calculator/vm",
            "/api/v1/calculator/comparison",
            "/api/v1/calculator/serverless",
        ]

        for endpoint in endpoints:
            response = client.post(
                endpoint, data="invalid json data", content_type="application/json"
            )
            assert response.status_code == 400
            data = json.loads(response.data)
            assert "error" in data

    def test_missing_content_type_handling(self, client):
        """Test handling of missing content type"""
        valid_payload = {"memory_mb": 512, "execution_time_seconds": 1.0}

        response = client.post(
            "/api/v1/calculator/lambda",
            data=json.dumps(valid_payload),
            # No content_type specified
        )

        # Should still work or return appropriate error
        assert response.status_code in [200, 400, 415]

    def test_empty_payload_handling(self, client):
        """Test handling of empty payloads"""
        response = client.post(
            "/api/v1/calculator/lambda",
            data=json.dumps({}),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "error" in data

    def test_method_not_allowed_handling(self, client):
        """Test handling of unsupported HTTP methods"""
        # Test GET on POST-only endpoints
        post_only_endpoints = [
            "/api/v1/calculator/lambda",
            "/api/v1/calculator/vm",
            "/api/v1/calculator/comparison",
            "/api/v1/calculator/export_csv",
            "/api/v1/calculator/recommend",
            "/api/v1/calculator/currency/convert",
            "/api/v1/calculator/serverless",
        ]

        for endpoint in post_only_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 405

    def test_internal_server_error_simulation(self, client):
        """Test internal server error handling"""
        payload = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
        }

        # Mock an unexpected exception in the calculator
        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.side_effect = RuntimeError(
                "Unexpected error"
            )

            response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 500
            data = json.loads(response.data)
            assert "Internal server error" in data["error"]


class TestCalculatorAPIIntegration:
    """Integration tests for calculator API endpoints"""

    def test_full_workflow_lambda_to_csv(self, client):
        """Test full workflow: calculate Lambda cost then export to CSV"""
        # Step 1: Calculate Lambda cost
        lambda_payload = {
            "memory_mb": 1024,
            "execution_time_seconds": 3.0,
            "monthly_executions": 250000,
            "include_free_tier": True,
        }

        with patch("app.api.calculator_api.lambda_calc") as mock_calc:
            mock_calc.calculate_total_cost.return_value = {
                "total_cost_usd": 25.48,
                "total_cost_jpy": 3822.0,
                "compute_cost_usd": 22.35,
                "request_cost_usd": 3.13,
            }

            lambda_response = client.post(
                "/api/v1/calculator/lambda",
                data=json.dumps(lambda_payload),
                content_type="application/json",
            )

            assert lambda_response.status_code == 200
            lambda_data = json.loads(lambda_response.data)

        # Step 2: Export results to CSV
        export_payload = {
            "calculations": [
                {
                    "type": "lambda",
                    "memory_mb": 1024,
                    "execution_time_seconds": 3.0,
                    "monthly_executions": 250000,
                    **lambda_data["data"],
                }
            ],
            "filename": "lambda_analysis",
        }

        csv_response = client.post(
            "/api/v1/calculator/export_csv",
            data=json.dumps(export_payload),
            content_type="application/json",
        )

        assert csv_response.status_code == 200
        assert "text/csv" in csv_response.content_type

        csv_content = csv_response.data.decode("utf-8")
        assert "1024" in csv_content  # Memory size
        assert "25.48" in csv_content  # Total cost

    def test_comparison_workflow(self, client):
        """Test comparison workflow with both Lambda and VM"""
        payload = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 2.5,
                "monthly_executions": 75000,
                "include_free_tier": True,
            },
            "vm_config": {
                "provider": "aws_ec2",
                "instance_type": "t3.small",
                "region": "us-east-1",
            },
        }

        with (
            patch("app.api.calculator_api.lambda_calc") as mock_lambda,
            patch("app.api.calculator_api.vm_calc") as mock_vm,
        ):

            mock_lambda.calculate_total_cost.return_value = {"total_cost_usd": 18.75}
            mock_vm.calculate_vm_cost.return_value = {"monthly_cost_usd": 15.12}

            response = client.post(
                "/api/v1/calculator/comparison",
                data=json.dumps(payload),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["success"] is True

            # Verify both costs are included
            assert "lambda_cost" in data["data"]
            assert "vm_cost" in data["data"]
            assert data["data"]["lambda_cost"]["total_cost_usd"] == 18.75
            assert data["data"]["vm_cost"]["monthly_cost_usd"] == 15.12
