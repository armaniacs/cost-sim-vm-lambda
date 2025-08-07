"""
Success path tests for Calculator API to achieve coverage
Tests the actual functionality with proper imports and mocking
"""
import pytest
import json
from unittest.mock import patch, Mock
from flask import Flask

# Import what we can from the actual implementation
try:
    from app.main import create_app
    # Import the actual API module to ensure it gets loaded
    import app.api.calculator_api
    from app.models.lambda_calculator import LambdaConfig
    from app.models.vm_calculator import VMConfig  
    from app.models.serverless_calculator import ServerlessConfig
    from app.utils.validation import ValidationError
except ImportError as e:
    # Skip tests if imports fail
    pytest.skip(f"Calculator API module not available: {e}", allow_module_level=True)


class TestLambdaEndpointSuccessPaths:
    """Test successful Lambda calculation paths"""
    
    @patch('app.api.calculator_api.validate_lambda_inputs')
    @patch('app.api.calculator_api.lambda_calc')
    def test_lambda_success_minimal_config(self, mock_lambda_calc, mock_validate, client):
        """Test successful Lambda calculation with minimal configuration"""
        # Setup validation mock
        mock_validate.return_value = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
            "egress_per_request_kb": 0.0,
            "internet_transfer_ratio": 100.0
        }
        
        # Setup calculator mock
        mock_lambda_calc.calculate_total_cost.return_value = {
            "total_cost_usd": 0.02,
            "compute_cost_usd": 0.01,
            "request_cost_usd": 0.01
        }
        
        payload = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        
        response = client.post(
            '/api/v1/calculator/lambda',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "data" in data
        assert data["data"]["total_cost_usd"] == 0.02
        
        # Verify mocks were called
        mock_validate.assert_called_once()
        mock_lambda_calc.calculate_total_cost.assert_called_once()
    
    @patch('app.api.calculator_api.validate_lambda_inputs')
    @patch('app.api.calculator_api.lambda_calc')
    def test_lambda_success_with_custom_egress_rates(self, mock_lambda_calc, mock_validate, client):
        """Test Lambda calculation with custom egress rates"""
        mock_validate.return_value = {
            "memory_mb": 1024,
            "execution_time_seconds": 2.5,
            "monthly_executions": 50000,
            "include_free_tier": False,
            "egress_per_request_kb": 100.0,
            "internet_transfer_ratio": 75.0
        }
        
        mock_lambda_calc.calculate_total_cost.return_value = {
            "total_cost_usd": 15.45,
            "compute_cost_usd": 12.30,
            "request_cost_usd": 2.00,
            "egress_cost_usd": 1.15
        }
        
        payload = {
            "memory_mb": 1024,
            "execution_time_seconds": 2.5,
            "monthly_executions": 50000,
            "include_free_tier": False,
            "custom_egress_rates": {
                "us-east-1": 0.09,
                "ap-northeast-1": 0.12
            },
            "include_egress_free_tier": True
        }
        
        response = client.post(
            '/api/v1/calculator/lambda',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["egress_cost_usd"] == 1.15
        
        # Verify custom egress rates were passed
        mock_lambda_calc.calculate_total_cost.assert_called_once()
        call_args = mock_lambda_calc.calculate_total_cost.call_args[0]
        custom_rates_arg = mock_lambda_calc.calculate_total_cost.call_args[0][1] if len(call_args) > 1 else None
        assert custom_rates_arg == payload["custom_egress_rates"]
    
    @patch('app.api.calculator_api.validate_lambda_inputs')
    @patch('app.api.calculator_api.lambda_calc')
    def test_lambda_success_without_custom_egress_rates(self, mock_lambda_calc, mock_validate, client):
        """Test Lambda calculation without custom egress rates"""
        mock_validate.return_value = {
            "memory_mb": 256,
            "execution_time_seconds": 0.5,
            "monthly_executions": 10000,
            "include_free_tier": True,
            "egress_per_request_kb": 50.0,
            "internet_transfer_ratio": 80.0
        }
        
        mock_lambda_calc.calculate_total_cost.return_value = {
            "total_cost_usd": 2.35
        }
        
        payload = {
            "memory_mb": 256,
            "execution_time_seconds": 0.5,
            "monthly_executions": 10000,
            "include_free_tier": True
        }
        
        response = client.post(
            '/api/v1/calculator/lambda',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Verify called without custom rates
        mock_lambda_calc.calculate_total_cost.assert_called_once()
        call_args = mock_lambda_calc.calculate_total_cost.call_args[0]
        assert len(call_args) >= 1  # At least config argument
        if len(call_args) > 1:
            assert call_args[1] is None  # No custom rates


class TestVMEndpointSuccessPaths:
    """Test successful VM calculation paths"""
    
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('app.api.calculator_api.vm_calc')
    def test_vm_success_basic_calculation(self, mock_vm_calc, mock_validate, client):
        """Test successful VM cost calculation (basic)"""
        mock_validate.return_value = {
            "provider": "aws_ec2",
            "instance_type": "t3.micro",
            "region": "us-east-1"
        }
        
        mock_vm_calc.calculate_vm_cost.return_value = {
            "hourly_cost_usd": 0.0104,
            "monthly_cost_usd": 7.59,
            "monthly_cost_jpy": 1138.0
        }
        
        payload = {
            "provider": "aws_ec2",
            "instance_type": "t3.micro",
            "region": "us-east-1"
        }
        
        response = client.post(
            '/api/v1/calculator/vm',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["hourly_cost_usd"] == 0.0104
        
        # Verify basic calculation was called
        mock_vm_calc.calculate_vm_cost.assert_called_once()
        mock_vm_calc.get_monthly_cost_with_egress.assert_not_called()
    
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('app.api.calculator_api.vm_calc')
    def test_vm_success_with_egress(self, mock_vm_calc, mock_validate, client):
        """Test VM calculation with egress parameters"""
        mock_validate.return_value = {
            "provider": "sakura_cloud",
            "instance_type": "2core-4gb",
            "region": "is1b",
            "monthly_executions": 25000,
            "egress_per_request_kb": 75.0,
            "internet_transfer_ratio": 85.0
        }
        
        mock_vm_calc.get_monthly_cost_with_egress.return_value = {
            "monthly_cost_usd": 25.40,
            "vm_cost_usd": 23.50,
            "egress_cost_usd": 1.90
        }
        
        payload = {
            "provider": "sakura_cloud",
            "instance_type": "2core-4gb",
            "region": "is1b",
            "monthly_executions": 25000,
            "egress_per_request_kb": 75.0,
            "internet_transfer_ratio": 85.0
        }
        
        response = client.post(
            '/api/v1/calculator/vm',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["egress_cost_usd"] == 1.90
        
        # Verify egress calculation was called
        mock_vm_calc.get_monthly_cost_with_egress.assert_called_once()
        mock_vm_calc.calculate_vm_cost.assert_not_called()
    
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('app.api.calculator_api.vm_calc')
    def test_vm_calculator_returns_none(self, mock_vm_calc, mock_validate, client):
        """Test VM endpoint when calculator returns None (invalid config)"""
        mock_validate.return_value = {
            "provider": "invalid_provider",
            "instance_type": "invalid.type",
            "region": "invalid-region"
        }
        
        mock_vm_calc.calculate_vm_cost.return_value = None
        
        payload = {
            "provider": "invalid_provider",
            "instance_type": "invalid.type",
            "region": "invalid-region"
        }
        
        response = client.post(
            '/api/v1/calculator/vm',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid provider" in data["error"] or "instance type" in data["error"]


class TestComparisonEndpointSuccessPaths:
    """Test successful comparison endpoint"""
    
    @patch('app.api.calculator_api.validate_lambda_inputs')
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('app.api.calculator_api.lambda_calc')
    @patch('app.api.calculator_api.vm_calc')
    def test_comparison_success(self, mock_vm_calc, mock_lambda_calc, mock_vm_validate, mock_lambda_validate, client):
        """Test successful cost comparison"""
        # Setup validation mocks
        mock_lambda_validate.return_value = {
            "memory_mb": 512,
            "execution_time_seconds": 2.0,
            "monthly_executions": 100000,
            "include_free_tier": True,
            "egress_per_request_kb": 0.0,
            "internet_transfer_ratio": 100.0
        }
        
        mock_vm_validate.return_value = {
            "provider": "aws_ec2",
            "instance_type": "t3.micro",
            "region": "us-east-1"
        }
        
        # Setup calculator mocks
        mock_lambda_calc.calculate_total_cost.return_value = {
            "total_cost_usd": 12.34
        }
        
        mock_vm_calc.calculate_vm_cost.return_value = {
            "monthly_cost_usd": 7.59
        }
        
        payload = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 2.0,
                "monthly_executions": 100000,
                "include_free_tier": True
            },
            "vm_config": {
                "provider": "aws_ec2",
                "instance_type": "t3.micro",
                "region": "us-east-1"
            }
        }
        
        response = client.post(
            '/api/v1/calculator/comparison',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "lambda_cost" in data["data"]
        assert "vm_cost" in data["data"]
        assert "breakeven_analysis" in data["data"]


class TestInstancesEndpointSuccessPaths:
    """Test instances endpoint success paths"""
    
    @patch('app.api.calculator_api.vm_calc')
    def test_get_available_instances_success(self, mock_vm_calc, client):
        """Test successful retrieval of available instances"""
        mock_vm_calc.get_available_instances.return_value = {
            "aws_ec2": {
                "us-east-1": ["t3.micro", "t3.small", "t3.medium"],
                "ap-northeast-1": ["t3.micro", "t3.small"]
            },
            "sakura_cloud": {
                "is1b": ["1core-1gb", "2core-4gb"]
            }
        }
        
        response = client.get('/api/v1/calculator/instances')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "aws_ec2" in data["data"]
        assert "sakura_cloud" in data["data"]
        
        # Verify called without provider filter
        mock_vm_calc.get_available_instances.assert_called_once_with()
    
    @patch('app.api.calculator_api.vm_calc')
    def test_get_available_instances_with_provider_filter(self, mock_vm_calc, client):
        """Test instances endpoint with provider filter"""
        mock_vm_calc.get_available_instances.return_value = {
            "aws_ec2": {
                "us-east-1": ["t3.micro", "t3.small"]
            }
        }
        
        response = client.get('/api/v1/calculator/instances?provider=aws_ec2')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        
        # Verify provider filter was applied
        mock_vm_calc.get_available_instances.assert_called_once_with("aws_ec2")


class TestRecommendEndpointSuccessPaths:
    """Test recommend endpoint success paths"""
    
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('app.api.calculator_api.vm_calc')
    def test_recommend_instances_success(self, mock_vm_calc, mock_validate, client):
        """Test successful instance recommendations"""
        mock_validate.return_value = {
            "budget_usd": 50.0,
            "cpu_cores": 2,
            "memory_gb": 4,
            "provider": "aws_ec2",
            "region": "us-east-1"
        }
        
        mock_vm_calc.recommend_instances.return_value = [
            {
                "instance_type": "t3.medium",
                "monthly_cost_usd": 30.24,
                "cpu_cores": 2,
                "memory_gb": 4.0,
                "match_score": 0.95
            },
            {
                "instance_type": "t3.small",
                "monthly_cost_usd": 15.12,
                "cpu_cores": 2,
                "memory_gb": 2.0,
                "match_score": 0.75
            }
        ]
        
        payload = {
            "budget_usd": 50.0,
            "cpu_cores": 2,
            "memory_gb": 4,
            "provider": "aws_ec2",
            "region": "us-east-1"
        }
        
        response = client.post(
            '/api/v1/calculator/recommend',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["match_score"] == 0.95


class TestCurrencyConvertEndpointSuccessPaths:
    """Test currency convert endpoint success paths"""
    
    @patch('app.api.calculator_api.validate_vm_inputs')
    @patch('requests.get')
    def test_currency_convert_success(self, mock_requests, mock_validate, client):
        """Test successful currency conversion"""
        mock_validate.return_value = {
            "amount": 100.0,
            "from_currency": "USD",
            "to_currency": "JPY"
        }
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "conversion_rates": {"JPY": 150.0}
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response
        
        payload = {
            "amount": 100.0,
            "from_currency": "USD",
            "to_currency": "JPY"
        }
        
        response = client.post(
            '/api/v1/calculator/currency/convert',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["converted_amount"] == 15000.0
        assert data["data"]["exchange_rate"] == 150.0


class TestServerlessEndpointSuccessPaths:
    """Test serverless endpoint success paths"""
    
    @patch('app.api.calculator_api.validate_serverless_inputs')
    @patch('app.api.calculator_api.serverless_calc')
    def test_serverless_gcp_functions_success(self, mock_serverless_calc, mock_validate, client):
        """Test successful serverless calculation for GCP Functions"""
        mock_validate.return_value = {
            "provider": "gcp_functions",
            "memory_mb": 256,
            "execution_time_seconds": 1.5,
            "monthly_executions": 50000,
            "include_free_tier": True
        }
        
        mock_serverless_calc.calculate.return_value = {
            "provider": "gcp_functions",
            "total_cost_usd": 3.45,
            "breakdown": {
                "request_cost": 0.45,
                "compute_cost": 3.00
            }
        }
        
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 256,
            "execution_time_seconds": 1.5,
            "monthly_executions": 50000,
            "include_free_tier": True
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert data["data"]["provider"] == "gcp_functions"
        assert data["data"]["total_cost_usd"] == 3.45


class TestServerlessProvidersEndpointSuccessPaths:
    """Test serverless providers endpoint success paths"""
    
    @patch('app.api.calculator_api.serverless_calc')
    def test_get_serverless_providers_success(self, mock_serverless_calc, client):
        """Test successful retrieval of serverless providers"""
        mock_serverless_calc.get_supported_providers.return_value = [
            {
                "provider": "gcp_functions",
                "name": "Google Cloud Functions",
                "regions": ["us-central1", "asia-northeast1"],
                "memory_options": [128, 256, 512, 1024, 2048]
            },
            {
                "provider": "azure_functions",
                "name": "Azure Functions",
                "regions": ["eastus", "japaneast"],
                "memory_options": [128, 256, 512, 1024]
            }
        ]
        
        response = client.get('/api/v1/calculator/serverless/providers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert len(data["data"]) == 2
        assert data["data"][0]["provider"] == "gcp_functions"


class TestCSVExportEndpointSuccessPaths:
    """Test CSV export endpoint with correct payload structure"""
    
    @patch('app.api.calculator_api.validate_lambda_inputs')
    @patch('app.api.calculator_api.lambda_calc')
    @patch('app.api.calculator_api.vm_calc')
    @patch('app.api.calculator_api.create_safe_csv_content')
    def test_export_csv_success(self, mock_create_csv, mock_vm_calc, mock_lambda_calc, mock_validate, client):
        """Test successful CSV export with correct payload structure"""
        # Setup validation mock
        mock_validate.return_value = {
            "memory_mb": 512,
            "execution_time_seconds": 2.0,
            "monthly_executions": 100000,
            "include_free_tier": True,
            "egress_per_request_kb": 50.0,
            "internet_transfer_ratio": 80.0
        }
        
        # Setup calculator mocks
        mock_lambda_calc.calculate_total_cost.return_value = {
            "request_charges": 2.00,
            "compute_charges": 10.34,
            "egress_charges": 1.15,
            "total_cost": 13.49
        }
        
        mock_vm_calc.get_monthly_cost_with_egress.return_value = {
            "provider": "aws_ec2",
            "instance_type": "t3.micro",
            "monthly_cost_usd": 7.59,
            "egress_cost_usd": 1.20,
            "total_monthly_cost_usd": 8.79
        }
        
        # Setup CSV creation mock
        mock_create_csv.return_value = "provider,instance_type,lambda_total_cost_usd\naws_ec2,t3.micro,13.49\n"
        
        # Use the correct payload structure based on the actual API
        payload = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 2.0,
                "monthly_executions": 100000,
                "include_free_tier": True,
                "egress_per_request_kb": 50.0
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.micro",
                    "region": "us-east-1"
                }
            ],
            "currency": "USD",
            "exchange_rate": 150.0
        }
        
        response = client.post(
            '/api/v1/calculator/export_csv',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        assert 'text/csv' in response.content_type
        assert 'attachment' in response.headers['Content-Disposition']
        
        # Verify CSV content
        csv_content = response.data.decode('utf-8')
        assert "aws_ec2,t3.micro" in csv_content