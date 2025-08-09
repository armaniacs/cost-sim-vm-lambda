"""
E2E tests for egress fee calculation feature (PBI09)
Following BDD scenarios and Outside-In TDD approach

BDD Scenario: egress費用を含む基本的なコスト比較
"""

import time

import pytest
import requests


class TestEgressFeatureE2E:
    """
    E2E tests for egress fee calculation feature
    Testing complete user flow: UI input → API → calculation → display
    """

    BASE_URL = "http://localhost:5001"

    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup for each test method"""
        # Wait for server to be ready
        max_retries = 10
        for _ in range(max_retries):
            try:
                response = requests.get(f"{self.BASE_URL}/health", timeout=5)
                if response.status_code == 200:
                    break
            except requests.exceptions.RequestException:
                time.sleep(1)
        else:
            pytest.skip("Server not available for E2E testing")

    def test_egress_cost_calculation_basic_scenario(self):
        """
        BDD Scenario: egress費用を含む基本的なコスト比較
        Given: Lambda 512MB、5秒実行、月間100万回が設定されている
        When: egress転送量として100KBを入力する
        And: AWS EC2 t3.smallを比較対象として選択する
        And: 計算ボタンをクリックする
        Then: グラフにLambda総コスト（実行費用+egress費用）が表示される
        And: EC2総コスト（固定費用+egress費用）が表示される
        And: break-evenポイントがegress費用込みで再計算される
        And: 費用内訳でegress費用が個別表示される
        """
        # Given: Lambda configuration setup
        lambda_config = {
            "memory_mb": 512,
            "execution_time_seconds": 5,
            "monthly_executions": 1_000_000,
            "include_free_tier": True,
            "egress_per_request_kb": 100,  # New egress parameter
        }

        vm_configs = [
            {
                "provider": "aws_ec2",
                "instance_type": "t3.small",
                "region": "ap-northeast-1",
            }
        ]

        # When: Calculate costs with egress
        response = requests.post(
            f"{self.BASE_URL}/api/v1/calculator/comparison",
            json={
                "lambda_config": lambda_config,
                "vm_configs": vm_configs,
                "currency": "USD",
                "exchange_rate": 150.0,
            },
            timeout=10,
        )

        # Then: Response should be successful
        assert (
            response.status_code == 200
        ), f"Expected 200, got {response.status_code}: {response.text}"

        data = response.json()
        assert "success" in data
        assert data["success"] is True
        assert "data" in data

        result_data = data["data"]

        # Verify Lambda total cost includes egress fees
        assert "lambda_costs" in result_data
        lambda_costs = result_data["lambda_costs"]

        # Should have execution cost and egress cost breakdown
        assert "execution_cost_usd" in lambda_costs
        assert "egress_cost_usd" in lambda_costs
        assert "total_cost_usd" in lambda_costs

        # Total cost should be sum of execution + egress
        expected_total = (
            lambda_costs["execution_cost_usd"] + lambda_costs["egress_cost_usd"]
        )
        assert abs(lambda_costs["total_cost_usd"] - expected_total) < 0.001

        # Verify VM costs include egress fees
        assert "vm_costs" in result_data
        vm_costs = result_data["vm_costs"]
        assert len(vm_costs) == 1

        ec2_cost = vm_costs[0]
        assert ec2_cost["provider"] == "aws_ec2"
        assert ec2_cost["instance_type"] == "t3.small"
        assert "fixed_cost_usd" in ec2_cost
        assert "egress_cost_usd" in ec2_cost
        assert "total_cost_usd" in ec2_cost

        # Verify break-even calculation includes egress
        assert "break_even_point" in result_data
        break_even = result_data["break_even_point"]
        assert "executions_per_month" in break_even
        assert break_even["executions_per_month"] > 0

        # Egress cost should be positive for 100KB per request
        assert lambda_costs["egress_cost_usd"] > 0
        assert ec2_cost["egress_cost_usd"] > 0

    def test_csv_export_includes_egress_fees(self):
        """
        BDD Scenario: CSV出力でegress費用詳細確認
        Given: egress費用込みコスト計算が完了している
        When: CSV出力APIを呼び出す
        Then: CSV内容にegress費用列が含まれる
        And: 実行費用とegress費用が分離記録される
        """
        # Given: Calculate with egress first
        lambda_config = {
            "memory_mb": 512,
            "execution_time_seconds": 5,
            "monthly_executions": 1_000_000,
            "include_free_tier": True,
            "egress_per_request_kb": 100,
        }

        vm_configs = [{"provider": "aws_ec2", "instance_type": "t3.small"}]

        # When: Export CSV
        response = requests.post(
            f"{self.BASE_URL}/api/v1/calculator/export_csv",
            json={
                "lambda_config": lambda_config,
                "vm_configs": vm_configs,
                "currency": "USD",
            },
            timeout=10,
        )

        # Then: CSV should include egress cost columns
        assert response.status_code == 200
        csv_content = response.text

        # Verify CSV headers include egress costs
        lines = csv_content.strip().split("\n")
        headers = lines[0].split(",")

        # Should have separate columns for execution and egress costs
        assert any("lambda_execution_cost" in header.lower() for header in headers)
        assert any("lambda_egress_cost" in header.lower() for header in headers)
        assert any("vm_egress_cost" in header.lower() for header in headers)

        # Verify data rows have egress cost values
        data_rows = lines[1:]
        assert len(data_rows) > 0

        for row in data_rows[:3]:  # Check first few rows
            values = row.split(",")
            assert len(values) == len(headers)
            # Egress cost values should be numeric
            lambda_egress_idx = next(
                i for i, h in enumerate(headers) if "lambda_egress_cost" in h.lower()
            )
            assert float(values[lambda_egress_idx]) >= 0

    def test_invalid_egress_input_handling(self):
        """
        BDD Scenario: 無効入力のエラーハンドリング
        Given: コストシミュレーター画面が表示されている
        When: egress転送量に負の値を入力する
        Then: 適切なエラーメッセージが表示される
        """
        # When: Invalid negative egress value
        lambda_config = {
            "memory_mb": 512,
            "execution_time_seconds": 5,
            "monthly_executions": 1_000_000,
            "include_free_tier": True,
            "egress_per_request_kb": -100,  # Invalid negative value
        }

        response = requests.post(
            f"{self.BASE_URL}/api/v1/calculator/comparison",
            json={"lambda_config": lambda_config, "vm_configs": [], "currency": "USD"},
            timeout=10,
        )

        # Then: Should return validation error
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "egress" in data["error"].lower()
        assert (
            "negative" in data["error"].lower() or "positive" in data["error"].lower()
        )

    def test_realtime_egress_calculation_performance(self):
        """
        Verify egress calculation performance meets <100ms requirement
        """
        lambda_config = {
            "memory_mb": 1024,
            "execution_time_seconds": 10,
            "monthly_executions": 5_000_000,
            "include_free_tier": True,
            "egress_per_request_kb": 1000,  # 1MB
        }

        vm_configs = [
            {"provider": "aws_ec2", "instance_type": "t3.medium"},
            {"provider": "sakura_cloud", "instance_type": "2core_4gb"},
            {"provider": "google_cloud", "instance_type": "e2-medium"},
        ]

        start_time = time.time()

        response = requests.post(
            f"{self.BASE_URL}/api/v1/calculator/comparison",
            json={
                "lambda_config": lambda_config,
                "vm_configs": vm_configs,
                "currency": "USD",
            },
            timeout=1,  # 1 second timeout to enforce performance
        )

        end_time = time.time()
        calculation_time = (end_time - start_time) * 1000  # Convert to ms

        # Performance requirement: <100ms
        assert (
            calculation_time < 100
        ), f"Calculation took {calculation_time}ms, expected <100ms"
        assert response.status_code == 200

        # Verify response includes egress calculations for all providers
        data = response.json()["data"]
        assert len(data["vm_costs"]) == 3
        for vm_cost in data["vm_costs"]:
            assert "egress_cost_usd" in vm_cost
            assert vm_cost["egress_cost_usd"] > 0  # Should have egress cost for 1MB
