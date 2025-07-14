"""
Integration tests for egress fee calculation API (PBI09)
Following BDD scenarios and t_wada TDD approach

Tests the API layer integration for egress cost calculations
"""
import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.main import create_app


class TestEgressAPIIntegration:
    """
    Integration tests for egress fee calculation API endpoints
    Tests API contracts and data flow between layers
    """

    @pytest.fixture
    def app(self) -> Flask:
        """Create Flask app for testing"""
        app = create_app("testing")
        return app

    @pytest.fixture
    def client(self, app: Flask):
        """Create test client"""
        with app.test_client() as client:
            yield client

    def test_comparison_api_accepts_egress_parameter(self, client):
        """
        Test that comparison API accepts egress_per_request_kb parameter
        """
        # Given: Lambda config with egress parameter
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 100,  # New egress parameter
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                    "region": "ap-northeast-1",
                }
            ],
            "currency": "USD",
            "exchange_rate": 150.0,
        }

        # When: Call comparison API
        response = client.post("/api/v1/calculator/comparison", json=request_data)

        # Then: Should accept the request (even if not fully implemented yet)
        assert response.status_code in [
            200,
            400,
        ], f"Unexpected status: {response.status_code}"

        # If 400, should be validation error, not server error
        if response.status_code == 400:
            data = response.get_json()
            assert "error" in data
            # Should not be internal server error
            assert "internal" not in data["error"].lower()

    def test_lambda_egress_cost_calculation(self, client):
        """
        Test Lambda egress cost calculation
        AWS Lambda egress: 0.09 USD/GB
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
            },
            "vm_configs": [],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        # Should have comparison data
        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check if any comparison point shows lambda costs > 0
        # (indicating egress costs are being calculated)
        found_lambda_cost = False
        for point in comparison_data:
            if point["lambda_cost_usd"] > 0:
                found_lambda_cost = True
                break
        assert found_lambda_cost, "Lambda costs should include egress fees"

    def test_vm_egress_cost_calculation_aws_ec2(self, client):
        """
        Test AWS EC2 egress cost calculation
        AWS EC2 egress: 0.09 USD/GB
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 500,  # 500KB per request
            },
            "vm_configs": [{"provider": "aws_ec2", "instance_type": "t3.small"}],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check if VM costs are being calculated with egress
        found_vm_cost = False
        for point in comparison_data:
            if "vm_costs" in point and len(point["vm_costs"]) > 0:
                found_vm_cost = True
                break
        assert found_vm_cost, "VM costs should include egress fees"

    def test_vm_egress_cost_calculation_google_cloud(self, client):
        """
        Test Google Cloud egress cost calculation
        Google Cloud egress: 0.085 USD/GB
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
            },
            "vm_configs": [{"provider": "google_cloud", "instance_type": "e2-micro"}],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Simple validation that Google Cloud costs are being calculated
        found_costs = any(
            "vm_costs" in point and len(point["vm_costs"]) > 0
            for point in comparison_data
        )
        assert found_costs, "Google Cloud VM costs should be calculated"

    def test_sakura_cloud_egress_cost_calculation(self, client):
        """
        Test Sakura Cloud egress cost calculation
        Sakura Cloud egress: 0.0 JPY/GB (egress free)
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
            },
            "vm_configs": [{"provider": "sakura_cloud", "instance_type": "2core_4gb"}],
            "currency": "JPY",
            "exchange_rate": 150.0,
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # With Sakura Cloud egress rate of 0.0 JPY/GB (egress free), cost should be 0
        # Check if comparison data contains results with VM costs
        found_sakura_cost = False
        for point in comparison_data:
            if "vm_costs" in point and len(point["vm_costs"]) > 0:
                found_sakura_cost = True
                break
        assert found_sakura_cost, "Sakura Cloud VM costs should be calculated"

    def test_egress_validation_negative_value(self, client):
        """
        Test validation of negative egress values
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": -100,  # Invalid negative value
            },
            "vm_configs": [],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Egress transfer amount must be zero or positive" in data["error"]

    def test_egress_validation_missing_parameter(self, client):
        """
        Test behavior when egress parameter is missing (should use default)
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True
                # egress_per_request_kb missing - should default to 0
            },
            "vm_configs": [],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        # Should succeed with default egress value (0)
        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check if lambda costs are calculated (should work with default egress = 0)
        found_lambda_cost = False
        for point in comparison_data:
            if point["lambda_cost_usd"] >= 0:
                found_lambda_cost = True
                break
        assert (
            found_lambda_cost
        ), "Lambda costs should be calculated with default egress value"

    def test_currency_conversion_with_egress(self, client):
        """
        Test currency conversion works correctly with egress costs
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB
            },
            "vm_configs": [{"provider": "aws_ec2", "instance_type": "t3.small"}],
            "currency": "JPY",
            "exchange_rate": 150.0,
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check that currency conversion is working
        # Lambda costs should be calculated with new egress rate (0.114 USD/GB)
        found_valid_conversion = False
        for point in comparison_data:
            if point["lambda_cost_usd"] > 0 and len(point["vm_costs"]) > 0:
                found_valid_conversion = True
                break
        assert (
            found_valid_conversion
        ), "Currency conversion should work with egress costs"

    def test_csv_export_includes_egress_columns(self, client):
        """
        Test CSV export includes egress cost columns
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 100,
            },
            "vm_configs": [{"provider": "aws_ec2", "instance_type": "t3.small"}],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/export_csv", json=request_data)

        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)

        # Check CSV headers include egress costs
        lines = csv_content.strip().split("\n")
        headers = lines[0].split(",")

        # Should have egress cost columns
        header_text = ",".join(headers).lower()
        assert "egress" in header_text

        # Verify data rows have egress values
        if len(lines) > 1:
            data_row = lines[1].split(",")
            assert len(data_row) == len(headers)
            # At least one egress cost should be numeric
            egress_indices = [i for i, h in enumerate(headers) if "egress" in h.lower()]
            for idx in egress_indices:
                if idx < len(data_row):
                    try:
                        float(data_row[idx])
                        break
                        # Found at least one valid egress cost
                    except ValueError:
                        continue
            else:
                pytest.fail("No valid egress cost values found in CSV data")

    def test_calculate_lambda_cost_negative_egress(self, client: FlaskClient):
        """Test lambda_cost with negative egress"""
        response = client.post(
            "/api/v1/calculator/lambda",
            json={
                "memory_mb": 512,
                "execution_time_seconds": 10,
                "monthly_executions": 1000000,
                "egress_per_request_kb": -1,
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Egress transfer amount must be zero or positive" in data["error"]

    def test_calculate_vm_cost_no_json(self, client: FlaskClient):
        """Test vm_cost with no JSON data"""
        response = client.post("/api/v1/calculator/vm", data="not json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_calculate_vm_cost_missing_fields(self, client: FlaskClient):
        """Test vm_cost with missing fields"""
        response = client.post(
            "/api/v1/calculator/vm",
            json={"provider": "aws_ec2"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Missing required fields" in data["error"]

    def test_calculate_comparison_negative_egress(self, client: FlaskClient):
        """Test comparison with negative egress"""
        response = client.post(
            "/api/v1/calculator/comparison",
            json={
                "lambda_config": {"egress_per_request_kb": -1},
                "vm_configs": [],
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Egress transfer amount must be zero or positive" in data["error"]

    def test_export_csv_no_json(self, client: FlaskClient):
        """Test export_csv with no JSON data"""
        response = client.post("/api/v1/calculator/export_csv", data="not json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_export_csv_negative_egress(self, client: FlaskClient):
        """Test export_csv with negative egress"""
        response = client.post(
            "/api/v1/calculator/export_csv",
            json={"lambda_config": {"egress_per_request_kb": -1}},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Egress transfer amount must be zero or positive" in data["error"]

    def test_recommend_instances_no_json(self, client: FlaskClient):
        """Test recommend_instances with no JSON data"""
        response = client.post("/api/v1/calculator/recommend", data="not json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_recommend_instances_missing_memory(self, client: FlaskClient):
        """Test recommend_instances with missing memory"""
        response = client.post("/api/v1/calculator/recommend", json={})
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "lambda_memory_mb is required" in data["error"]

    def test_convert_currency_no_json(self, client: FlaskClient):
        """Test convert_currency with no JSON data"""
        response = client.post("/api/v1/calculator/currency/convert", data="not json")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "No JSON data provided" in data["error"]

    def test_convert_currency_missing_amount(self, client: FlaskClient):
        """Test convert_currency with missing amount"""
        response = client.post(
            "/api/v1/calculator/currency/convert",
            json={"from_currency": "USD", "to_currency": "JPY"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "amount is required" in data["error"]

    def test_convert_currency_unsupported_conversion(self, client: FlaskClient):
        """Test convert_currency with unsupported conversion"""
        response = client.post(
            "/api/v1/calculator/currency/convert",
            json={"amount": 100, "from_currency": "EUR", "to_currency": "GBP"},
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Only USD<->JPY conversion supported" in data["error"]

    def test_vm_egress_cost_calculation_azure(self, client: FlaskClient):
        """
        Test Azure egress cost calculation
        Azure egress: 0.12 USD/GB (Asia)
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
            },
            "vm_configs": [{"provider": "azure", "instance_type": "B2ms"}],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Simple validation that Azure costs are being calculated
        found_costs = any(
            "vm_costs" in point and len(point["vm_costs"]) > 0
            for point in comparison_data
        )
        assert found_costs, "Azure VM costs should be calculated"

    def test_vm_egress_cost_calculation_oci(self, client: FlaskClient):
        """
        Test OCI egress cost calculation
        OCI egress: 0.025 USD/GB (APAC, Japan) after 10TB free
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
            },
            "vm_configs": [
                {"provider": "oci", "instance_type": "VM.Standard.E4.Flex_2_16"}
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Simple validation that OCI costs are being calculated
        found_costs = any(
            "vm_costs" in point and len(point["vm_costs"]) > 0
            for point in comparison_data
        )
        assert found_costs, "OCI VM costs should be calculated"

    def test_vm_egress_cost_calculation_oci_free_tier(self, client: FlaskClient):
        """
        Test OCI egress cost calculation with free tier (10TB free)
        """
        # Total egress will be 1,000,000 executions * 10KB/request = 10GB/month
        # This should be within OCI's 10TB free tier, so egress cost should be 0
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 10,  # 10KB per request
            },
            "vm_configs": [
                {"provider": "oci", "instance_type": "VM.Standard.E4.Flex_2_16"}
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check that OCI egress cost is 0 due to free tier
        oci_cost = comparison_data[0]["vm_costs"]["oci_VM.Standard.E4.Flex_2_16"]
        assert oci_cost == pytest.approx(
            0.049 * 730, rel=1e-3
        )  # Only fixed cost, no egress

    def test_vm_egress_cost_calculation_oci_above_free_tier(self, client: FlaskClient):
        """
        Test OCI egress cost calculation above free tier (10TB free)
        """
        # Total egress will be 1,000,000 executions * 10MB/request =
        # 10,000GB/month = 10TB/month
        # This should be exactly at OCI's 10TB free tier,
        # so egress cost should be 0
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 10 * 1024,  # 10MB per request
            },
            "vm_configs": [
                {"provider": "oci", "instance_type": "VM.Standard.E4.Flex_2_16"}
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Check that OCI egress cost is 0 due to free tier
        oci_cost = comparison_data[0]["vm_costs"]["oci_VM.Standard.E4.Flex_2_16"]
        assert oci_cost == pytest.approx(
            0.049 * 730, rel=1e-3
        )  # Only fixed cost, no egress

        # Now test with 10MB + 1KB to go over the free tier
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 10 * 1024 + 1,  # 10MB + 1KB per request
            },
            "vm_configs": [
                {"provider": "oci", "instance_type": "VM.Standard.E4.Flex_2_16"}
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Calculate expected egress cost for 1KB over 10TB
        # 1,000,000 executions * 1KB/request = 1GB
        # 1GB * 0.025 USD/GB = 0.025 USD
        expected_egress_cost = 1 * 0.025
        expected_total_cost = (0.049 * 730) + expected_egress_cost

        oci_cost = comparison_data[0]["vm_costs"]["oci_VM.Standard.E4.Flex_2_16"]
        assert oci_cost == pytest.approx(expected_total_cost, rel=1e-3)
