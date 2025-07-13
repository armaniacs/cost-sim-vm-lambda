"""
Integration tests for Google Cloud provider API
Testing API endpoints with Google Cloud VM configurations
"""
import pytest
from flask.testing import FlaskClient


class TestGoogleCloudAPIIntegration:
    """Integration tests for Google Cloud provider API endpoints"""

    def test_vm_cost_calculation_google_cloud_e2_micro(self, client: FlaskClient):
        """Test VM cost calculation for Google Cloud e2-micro instance"""
        response = client.post(
            "/api/v1/calculator/vm",
            json={
                "provider": "google_cloud",
                "instance_type": "e2-micro",
                "region": "asia-northeast1",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        result = data["data"]

        assert result["provider"] == "google_cloud"
        assert result["instance_type"] == "e2-micro"
        assert result["hourly_cost_usd"] == 0.0084
        assert result["monthly_cost_usd"] == pytest.approx(6.132, rel=1e-3)
        assert result["specs"]["vcpu"] == 0.25
        assert result["specs"]["memory_gb"] == 1
        assert result["configuration"]["provider"] == "google_cloud"

    def test_vm_cost_calculation_google_cloud_n2_standard_2(self, client: FlaskClient):
        """Test VM cost calculation for Google Cloud n2-standard-2 instance"""
        response = client.post(
            "/api/v1/calculator/vm",
            json={
                "provider": "google_cloud",
                "instance_type": "n2-standard-2",
                "region": "asia-northeast1",
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        result = data["data"]

        assert result["provider"] == "google_cloud"
        assert result["instance_type"] == "n2-standard-2"
        assert result["hourly_cost_usd"] == 0.0970
        assert result["monthly_cost_usd"] == pytest.approx(70.81, rel=1e-3)
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 8

    def test_vm_cost_calculation_invalid_google_cloud_instance(
        self, client: FlaskClient
    ):
        """Test VM cost calculation for invalid Google Cloud instance"""
        response = client.post(
            "/api/v1/calculator/vm",
            json={
                "provider": "google_cloud",
                "instance_type": "invalid-instance",
                "region": "asia-northeast1",
            },
            content_type="application/json",
        )

        assert response.status_code == 400
        data = response.get_json()

        assert "error" in data
        assert "Invalid provider" in data["error"]

    def test_comparison_with_google_cloud(self, client: FlaskClient):
        """Test comparison API including Google Cloud provider"""
        response = client.post(
            "/api/v1/calculator/comparison",
            json={
                "lambda_config": {
                    "memory_mb": 512,
                    "execution_time_seconds": 10,
                    "include_free_tier": True,
                },
                "vm_configs": [
                    {"provider": "aws_ec2", "instance_type": "t3.small"},
                    {"provider": "sakura_cloud", "instance_type": "2core_4gb"},
                    {"provider": "google_cloud", "instance_type": "e2-medium"},
                ],
                "execution_range": {"min": 1000000, "max": 6000000, "steps": 10},
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        result = data["data"]

        # Check that comparison data exists
        assert "comparison_data" in result
        assert len(result["comparison_data"]) == 10

        # Check that Google Cloud costs are included
        comparison_row = result["comparison_data"][0]
        assert "vm_costs" in comparison_row

        gcp_key = "google_cloud_e2-medium"
        assert gcp_key in comparison_row["vm_costs"]
        assert comparison_row["vm_costs"][gcp_key] > 0

    def test_instances_endpoint_includes_google_cloud(self, client: FlaskClient):
        """Test instances endpoint includes Google Cloud instances"""
        response = client.get("/api/v1/calculator/instances")

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        instances = data["data"]

        assert "google_cloud" in instances
        gcp_instances = instances["google_cloud"]

        # Check that expected instance types are present
        expected_instances = [
            "e2-micro",
            "e2-small",
            "e2-medium",
            "n2-standard-1",
            "n2-standard-2",
            "c2-standard-4",
        ]
        for instance_type in expected_instances:
            assert instance_type in gcp_instances

            instance_data = gcp_instances[instance_type]
            assert "hourly_cost_usd" in instance_data
            assert "monthly_cost_usd" in instance_data
            assert "specs" in instance_data
            assert "vcpu" in instance_data["specs"]
            assert "memory_gb" in instance_data["specs"]

    def test_recommend_endpoint_includes_google_cloud(self, client: FlaskClient):
        """Test recommend endpoint includes Google Cloud recommendations"""
        response = client.post(
            "/api/v1/calculator/recommend",
            json={"lambda_memory_mb": 1024},
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        recommendations = data["data"]

        assert "google_cloud" in recommendations
        gcp_recs = recommendations["google_cloud"]

        # Should have at least one recommendation
        assert len(gcp_recs) > 0

        # All recommendations should have memory >= 1GB
        for rec in gcp_recs:
            assert rec["specs"]["memory_gb"] >= 1.0
            assert "memory_ratio" in rec
            assert rec["memory_ratio"] >= 1.0

    def test_comparison_with_break_even_points_google_cloud(self, client: FlaskClient):
        """Test comparison with break-even points including Google Cloud"""
        response = client.post(
            "/api/v1/calculator/comparison",
            json={
                "lambda_config": {
                    "memory_mb": 512,
                    "execution_time_seconds": 5,
                    "include_free_tier": True,
                },
                "vm_configs": [
                    {"provider": "google_cloud", "instance_type": "e2-micro"}
                ],
                "execution_range": {"min": 100000, "max": 10000000, "steps": 50},
            },
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.get_json()

        assert data["success"] is True
        result = data["data"]

        # Should have break-even points
        assert "break_even_points" in result
        break_even_points = result["break_even_points"]

        # Should find at least one break-even point with Google Cloud
        gcp_break_even = None
        for point in break_even_points:
            if point["vm_provider"] == "google_cloud":
                gcp_break_even = point
                break

        if gcp_break_even:  # Break-even point found
            assert gcp_break_even["vm_instance"] == "e2-micro"
            assert gcp_break_even["executions_per_month"] > 0
            assert gcp_break_even["executions_per_second"] > 0
        # Note: Break-even point may not exist if Lambda is always cheaper
        # or always more expensive

    def test_google_cloud_pricing_accuracy(self, client: FlaskClient):
        """Test Google Cloud pricing accuracy against expected values"""
        test_cases = [
            {
                "instance": "e2-micro",
                "expected_hourly": 0.0084,
                "expected_monthly": 6.132,
            },
            {
                "instance": "e2-small",
                "expected_hourly": 0.0168,
                "expected_monthly": 12.264,
            },
            {
                "instance": "c2-standard-4",
                "expected_hourly": 0.2088,
                "expected_monthly": 152.424,
            },
        ]

        for case in test_cases:
            response = client.post(
                "/api/v1/calculator/vm",
                json={
                    "provider": "google_cloud",
                    "instance_type": case["instance"],
                    "region": "asia-northeast1",
                },
                content_type="application/json",
            )

            assert response.status_code == 200
            data = response.get_json()
            result = data["data"]

            assert result["hourly_cost_usd"] == pytest.approx(
                case["expected_hourly"], rel=1e-6
            )
            assert result["monthly_cost_usd"] == pytest.approx(
                case["expected_monthly"], rel=1e-3
            )
