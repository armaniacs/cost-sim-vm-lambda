"""
Unit tests for Serverless API endpoint
Following t_wada TDD: Red -> Green -> Refactor

This test file drives the implementation of /api/serverless endpoint
Focusing on GCP Functions integration (Phase 1A)
"""
import json
import pytest


class TestServerlessAPI:
    """Test /api/serverless endpoint functionality"""

    def test_serverless_endpoint_gcp_functions_success(self, client):
        """Test successful GCP Functions cost calculation via API"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 5.0,
            "monthly_executions": 2500000,  # Above free tier
            "include_free_tier": True,
            "exchange_rate": 150.0,
            "egress_per_request_kb": 10.0,
            "internet_transfer_ratio": 100.0,
            "include_ecosystem_benefits": False
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert "data" in data
        
        result_data = data["data"]
        assert result_data["provider"] == "gcp_functions"
        assert result_data["service_name"] == "Google Cloud Functions"
        assert isinstance(result_data["total_cost_usd"], (int, float))
        assert isinstance(result_data["total_cost_jpy"], (int, float))
        assert result_data["total_cost_usd"] > 0  # Should have cost above free tier
        assert result_data["total_cost_jpy"] > result_data["total_cost_usd"]  # JPY > USD
        
        # Check cost breakdown structure
        assert "cost_breakdown" in result_data
        assert "request_cost" in result_data["cost_breakdown"]
        assert "compute_cost" in result_data["cost_breakdown"]
        
        # Check free tier savings
        assert "free_tier_savings" in result_data
        assert "request_savings" in result_data["free_tier_savings"]
        assert "compute_savings" in result_data["free_tier_savings"]
        
        # Check configuration echoed back
        assert "configuration" in result_data
        assert result_data["configuration"]["memory_mb"] == 512
        assert result_data["configuration"]["execution_time_seconds"] == 5.0
        assert result_data["configuration"]["monthly_executions"] == 2500000

    def test_serverless_endpoint_aws_lambda_success(self, client):
        """Test successful AWS Lambda cost calculation via API"""
        payload = {
            "provider": "aws_lambda",
            "memory_mb": 512,
            "execution_time_seconds": 10.0,
            "monthly_executions": 2000000,
            "include_free_tier": True,
            "exchange_rate": 150.0
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        result_data = data["data"]
        assert result_data["provider"] == "aws_lambda"
        assert result_data["service_name"] == "AWS Lambda"
        assert result_data["total_cost_usd"] > 0

    def test_serverless_endpoint_missing_required_fields(self, client):
        """Test API response when required fields are missing"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            # Missing execution_time_seconds and monthly_executions
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert "Missing required fields" in data["error"]

    def test_serverless_endpoint_unsupported_provider(self, client):
        """Test API response for unsupported provider"""
        payload = {
            "provider": "azure_functions",  # Not implemented yet
            "memory_mb": 512,
            "execution_time_seconds": 5.0,
            "monthly_executions": 1000000
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert "not supported" in data["error"]

    def test_serverless_endpoint_invalid_memory(self, client):
        """Test API response for invalid memory configuration"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 64,  # Below minimum for GCP Functions
            "execution_time_seconds": 5.0,
            "monthly_executions": 1000000
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data

    def test_serverless_endpoint_invalid_execution_time(self, client):
        """Test API response for invalid execution time"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 1000.0,  # Above maximum for GCP Functions
            "monthly_executions": 1000000
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data

    def test_serverless_endpoint_invalid_egress_amount(self, client):
        """Test API response for invalid egress amount"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 5.0,
            "monthly_executions": 1000000,
            "egress_per_request_kb": -10.0  # Negative value
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert "must be zero or positive" in data["error"]

    def test_serverless_endpoint_invalid_transfer_ratio(self, client):
        """Test API response for invalid internet transfer ratio"""
        payload = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 5.0,
            "monthly_executions": 1000000,
            "internet_transfer_ratio": 150.0  # Above 100%
        }
        
        response = client.post(
            '/api/v1/calculator/serverless',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert "between 0 and 100" in data["error"]

    def test_serverless_endpoint_no_json_data(self, client):
        """Test API response when no JSON data is provided"""
        response = client.post(
            '/api/v1/calculator/serverless',
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_serverless_providers_endpoint_success(self, client):
        """Test /api/serverless/providers endpoint returns supported providers"""
        response = client.get('/api/v1/calculator/serverless/providers')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        
        assert data["success"] is True
        assert "data" in data
        
        result_data = data["data"]
        assert "supported_providers" in result_data
        assert "provider_info" in result_data
        
        # Should include both aws_lambda and gcp_functions
        assert "aws_lambda" in result_data["supported_providers"]
        assert "gcp_functions" in result_data["supported_providers"]
        
        # Should have provider info for each
        assert "aws_lambda" in result_data["provider_info"]
        assert "gcp_functions" in result_data["provider_info"]
        
        # Check GCP Functions provider info structure
        gcp_info = result_data["provider_info"]["gcp_functions"]
        assert gcp_info["name"] == "Google Cloud Functions"
        assert gcp_info["pricing_model"] == "Request + GB-second"
        assert "2,000,000 requests" in gcp_info["free_tier"]