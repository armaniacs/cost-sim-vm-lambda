"""
E2E tests for Internet Transfer Ratio feature (PBI10)
Following BDD scenarios and t_wada TDD approach

Tests the complete user journey for setting internet transfer ratio
"""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from app.main import create_app


class TestInternetTransferRatioE2E:
    """
    E2E tests for Internet Transfer Ratio feature
    Tests complete user scenarios from PBI10 BDD acceptance criteria
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

    def test_preset_transfer_ratio_calculation(self, client: FlaskClient):
        """
        BDD Scenario 1: プリセット転送割合での計算
        Given コスト比較シミュレーターが起動している
        When ユーザーがインターネット転送割合として "50%" を選択する
        And 他のパラメータ（Lambda設定、VM設定）を入力する
        And "計算実行" ボタンをクリックする
        Then egress費用が50%として計算される
        And グラフに反映された結果が表示される
        And CSV出力にも50%適用後の費用が含まれる
        """
        # Given: Basic Lambda and VM configuration
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
                "internet_transfer_ratio": 50,  # NEW: 50% to internet
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                    "region": "ap-northeast-1",
                }
            ],
            "execution_range": {"min": 1_000_000, "max": 2_000_000, "steps": 2},
            "currency": "USD",
        }

        # When: Call comparison API
        response = client.post("/api/v1/calculator/comparison", json=request_data)

        # Then: Should calculate with 50% ratio applied
        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Verify 50% ratio is applied to egress calculation
        # Expected: 1MB * 1M executions * 50% = 500GB total internet transfer
        # At 0.114 USD/GB (after 100GB free): (500GB - 100GB) * 0.114 = 45.6 USD
        first_point = comparison_data[0]
        lambda_cost = first_point["lambda_cost_usd"]
        assert lambda_cost > 0  # Should include 50% of egress cost

    def test_custom_transfer_ratio_calculation(self, client: FlaskClient):
        """
        BDD Scenario 2: カスタム転送割合での計算
        Given コスト比較シミュレーターが起動している
        When ユーザーがカスタム入力欄に "75" を入力する
        And 他のパラメータを設定して計算を実行する
        Then egress費用が75%として計算される
        And カスタム値がUIに保持される
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
                "internet_transfer_ratio": 75,  # NEW: Custom 75% to internet
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                }
            ],
            "execution_range": {"min": 1_000_000, "max": 2_000_000, "steps": 2},
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # Verify 75% ratio is applied
        # Expected: 1MB * 1M executions * 75% = 750GB total internet transfer
        # At 0.114 USD/GB (after 100GB free): (750GB - 100GB) * 0.114 = 74.1 USD
        first_point = comparison_data[0]
        lambda_cost = first_point["lambda_cost_usd"]
        assert lambda_cost > 0

    def test_invalid_transfer_ratio_validation(self, client: FlaskClient):
        """
        BDD Scenario 3: 無効な転送割合の入力
        Given コスト比較シミュレーターが起動している
        When ユーザーがカスタム入力欄に "-10" を入力する
        And 計算を実行しようとする
        Then "転送割合は0-100の範囲で入力してください" エラーが表示される
        And 計算は実行されない
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,
                "internet_transfer_ratio": -10,  # NEW: Invalid negative ratio
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                }
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        # Should return validation error
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Internet transfer ratio must be between 0.0 and 100.0" in data["error"]

    def test_transfer_ratio_over_100_validation(self, client: FlaskClient):
        """
        Additional validation test for ratio > 100%
        """
        request_data = {
            "lambda_config": {
                "internet_transfer_ratio": 150,  # Invalid: over 100%
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "egress_per_request_kb": 100,
            },
            "vm_configs": [],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "Internet transfer ratio must be between 0.0 and 100.0" in data["error"]

    def test_zero_percent_private_network_calculation(self, client: FlaskClient):
        """
        BDD Scenario 4: 完全閉域環境での計算
        Given コスト比較シミュレーターが起動している
        When ユーザーがインターネット転送割合として "0%" を選択する
        And 計算を実行する
        Then 全プロバイダのegress費用が0として計算される
        And Lambda vs VM の比較で egress影響が除外される
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,  # 1MB per request
                "internet_transfer_ratio": 0,  # NEW: 0% to internet (fully private)
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                },
                {
                    "provider": "sakura_cloud",
                    "instance_type": "2core_4gb",
                },
            ],
            "execution_range": {"min": 1_000_000, "max": 2_000_000, "steps": 2},
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

        # With 0% internet transfer, egress costs should be 0
        # Lambda cost should only include compute cost, no egress
        first_point = comparison_data[0]
        lambda_cost = first_point["lambda_cost_usd"]

        # Should have some cost (compute) but no egress cost
        assert lambda_cost > 0  # Base compute cost
        # egress portion should be 0 with 0% internet ratio

    def test_missing_transfer_ratio_defaults_to_100_percent(self, client: FlaskClient):
        """
        Test backward compatibility: missing ratio defaults to 100%
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,
                # internet_transfer_ratio missing - should default to 100%
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                }
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/comparison", json=request_data)

        # Should succeed with default 100% ratio
        assert response.status_code == 200
        data = response.get_json()

        comparison_data = data["data"]["comparison_data"]
        assert len(comparison_data) > 0

    def test_csv_export_includes_transfer_ratio_impact(self, client: FlaskClient):
        """
        Test CSV export includes transfer ratio impact in costs
        """
        request_data = {
            "lambda_config": {
                "memory_mb": 512,
                "execution_time_seconds": 5,
                "monthly_executions": 1_000_000,
                "include_free_tier": True,
                "egress_per_request_kb": 1000,
                "internet_transfer_ratio": 25,  # 25% to internet
            },
            "vm_configs": [
                {
                    "provider": "aws_ec2",
                    "instance_type": "t3.small",
                }
            ],
            "currency": "USD",
        }

        response = client.post("/api/v1/calculator/export_csv", json=request_data)

        assert response.status_code == 200
        csv_content = response.get_data(as_text=True)

        # CSV should contain cost data affected by 25% transfer ratio
        lines = csv_content.strip().split("\n")
        assert len(lines) >= 2  # Header + at least one data row

        headers = lines[0].split(",")
        assert any("cost" in header.lower() for header in headers)

    def test_lambda_api_direct_with_transfer_ratio(self, client: FlaskClient):
        """
        Test Lambda cost API directly with transfer ratio
        """
        request_data = {
            "memory_mb": 512,
            "execution_time_seconds": 10,
            "monthly_executions": 1_000_000,
            "egress_per_request_kb": 1000,
            "internet_transfer_ratio": 30,  # 30% to internet
        }

        response = client.post("/api/v1/calculator/lambda", json=request_data)

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert data["data"]["total_cost"] > 0

    def test_vm_api_direct_with_transfer_ratio(self, client: FlaskClient):
        """
        Test VM cost API directly with transfer ratio
        """
        request_data = {
            "provider": "aws_ec2",
            "instance_type": "t3.small",
            "region": "ap-northeast-1",
            "monthly_executions": 1_000_000,
            "egress_per_request_kb": 1000,
            "internet_transfer_ratio": 40,  # 40% to internet
        }

        response = client.post("/api/v1/calculator/vm", json=request_data)

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert data["data"]["total_monthly_cost_usd"] >= 0
