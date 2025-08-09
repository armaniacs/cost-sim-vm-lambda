"""
Unit tests for VM cost calculation
Following t_wada TDD principles
"""

import pytest

from app.models.vm_calculator import VMCalculator, VMConfig


class TestVMCalculator:
    """Test VM cost calculation logic"""

    def test_vm_calculator_initialization(self):
        """Test VMCalculator can be initialized"""
        calculator = VMCalculator()
        assert calculator is not None

    def test_vm_config_creation(self):
        """Test VMConfig data class creation"""
        config = VMConfig(
            provider="aws_ec2", instance_type="t3.small", region="ap-northeast-1"
        )
        assert config.provider == "aws_ec2"
        assert config.instance_type == "t3.small"
        assert config.region == "ap-northeast-1"

    def test_get_ec2_cost_valid_instance(self):
        """Test EC2 cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_ec2_cost("t3.small")

        assert result is not None
        assert result["provider"] == "aws_ec2"
        assert result["instance_type"] == "t3.small"
        assert result["hourly_cost_usd"] == 0.0272
        assert result["monthly_cost_usd"] == pytest.approx(19.856, rel=1e-3)
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 2

    def test_get_ec2_cost_invalid_instance(self):
        """Test EC2 cost calculation for invalid instance"""
        calculator = VMCalculator()
        result = calculator.get_ec2_cost("invalid.instance")
        assert result is None

    def test_get_sakura_cost_valid_instance(self):
        """Test Sakura Cloud cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_sakura_cost("2core_4gb")

        assert result is not None
        assert result["provider"] == "sakura_cloud"
        assert result["instance_type"] == "2core_4gb"
        assert result["monthly_cost_jpy"] == 4180
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 4
        assert result["specs"]["storage_gb"] == 20

    def test_get_sakura_cost_invalid_instance(self):
        """Test Sakura Cloud cost calculation for invalid instance"""
        calculator = VMCalculator()
        result = calculator.get_sakura_cost("invalid_instance")
        assert result is None

    def test_get_gcp_cost_valid_instance(self):
        """Test Google Cloud cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_gcp_cost("e2-micro")

        assert result is not None
        assert result["provider"] == "google_cloud"
        assert result["instance_type"] == "e2-micro"
        assert result["hourly_cost_usd"] == 0.0084
        assert result["monthly_cost_usd"] == pytest.approx(6.132, rel=1e-3)
        assert result["specs"]["vcpu"] == 0.25
        assert result["specs"]["memory_gb"] == 1

    def test_get_gcp_cost_invalid_instance(self):
        """Test Google Cloud cost calculation for invalid instance"""
        calculator = VMCalculator()
        result = calculator.get_gcp_cost("invalid.instance")
        assert result is None

    def test_calculate_vm_cost_ec2(self):
        """Test VM cost calculation for EC2"""
        calculator = VMCalculator()
        config = VMConfig(
            provider="aws_ec2", instance_type="t3.small", region="ap-northeast-1"
        )

        result = calculator.calculate_vm_cost(config)

        assert result is not None
        assert result["provider"] == "aws_ec2"
        assert result["monthly_cost_usd"] == pytest.approx(19.856, rel=1e-3)
        assert result["configuration"]["provider"] == "aws_ec2"
        assert result["configuration"]["instance_type"] == "t3.small"

    def test_calculate_vm_cost_sakura(self):
        """Test VM cost calculation for Sakura Cloud"""
        calculator = VMCalculator()
        config = VMConfig(
            provider="sakura_cloud", instance_type="2core_4gb", region="tokyo"
        )

        result = calculator.calculate_vm_cost(config)

        assert result is not None
        assert result["provider"] == "sakura_cloud"
        assert result["monthly_cost_jpy"] == 4180
        assert result["configuration"]["provider"] == "sakura_cloud"
        assert result["configuration"]["instance_type"] == "2core_4gb"

    def test_calculate_vm_cost_google_cloud(self):
        """Test VM cost calculation for Google Cloud"""
        calculator = VMCalculator()
        config = VMConfig(
            provider="google_cloud", instance_type="e2-medium", region="asia-northeast1"
        )

        result = calculator.calculate_vm_cost(config)

        assert result is not None
        assert result["provider"] == "google_cloud"
        assert result["monthly_cost_usd"] == pytest.approx(24.455, rel=1e-3)
        assert result["configuration"]["provider"] == "google_cloud"
        assert result["configuration"]["instance_type"] == "e2-medium"

    def test_calculate_vm_cost_invalid_provider(self):
        """Test VM cost calculation for invalid provider"""
        calculator = VMCalculator()
        config = VMConfig(provider="invalid_provider", instance_type="some_instance")

        result = calculator.calculate_vm_cost(config)
        assert result is None

    def test_get_available_instances_ec2(self):
        """Test getting available EC2 instances"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("aws_ec2")

        assert "t3.small" in instances
        assert "t3.medium" in instances
        assert instances["t3.small"]["hourly_cost_usd"] == 0.0272
        assert instances["t3.small"]["specs"]["memory_gb"] == 2

    def test_get_available_instances_sakura(self):
        """Test getting available Sakura Cloud instances"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("sakura_cloud")

        assert "2core_4gb" in instances
        assert instances["2core_4gb"]["monthly_cost_jpy"] == 4180
        assert instances["2core_4gb"]["specs"]["memory_gb"] == 4

    def test_get_available_instances_google_cloud(self):
        """Test getting available Google Cloud instances"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("google_cloud")

        assert "e2-micro" in instances
        assert "n2-standard-2" in instances
        assert instances["e2-micro"]["hourly_cost_usd"] == 0.0084
        assert instances["e2-micro"]["specs"]["memory_gb"] == 1
        assert instances["n2-standard-2"]["specs"]["vcpu"] == 2

    def test_get_available_instances_invalid_provider(self):
        """Test getting available instances for invalid provider"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("invalid_provider")
        assert instances == {}

    def test_recommend_instance_for_lambda_512mb(self):
        """Test instance recommendation for 512MB Lambda"""
        calculator = VMCalculator()
        recommendations = calculator.recommend_instance_for_lambda(512)

        # Should recommend instances with >= 0.5GB memory
        assert "aws_ec2" in recommendations
        assert "sakura_cloud" in recommendations
        assert "google_cloud" in recommendations

        # EC2 recommendations should be sorted by memory ratio
        ec2_recs = recommendations["aws_ec2"]
        assert len(ec2_recs) > 0
        assert ec2_recs[0]["memory_ratio"] >= 1.0

        # Should have t3.micro (1GB) as closest match
        ec2_types = [rec["instance_type"] for rec in ec2_recs]
        assert "t3.micro" in ec2_types

        # Google Cloud recommendations should include instances with >= 0.5GB memory
        gcp_recs = recommendations["google_cloud"]
        assert len(gcp_recs) > 0
        for rec in gcp_recs:
            assert rec["specs"]["memory_gb"] >= 0.5

        # Should have e2-micro (1GB) in recommendations
        gcp_types = [rec["instance_type"] for rec in gcp_recs]
        assert "e2-micro" in gcp_types

    def test_recommend_instance_for_lambda_2048mb(self):
        """Test instance recommendation for 2048MB Lambda"""
        calculator = VMCalculator()
        recommendations = calculator.recommend_instance_for_lambda(2048)

        # Should recommend instances with >= 2GB memory
        ec2_recs = recommendations["aws_ec2"]
        for rec in ec2_recs:
            assert rec["specs"]["memory_gb"] >= 2.0

        sakura_recs = recommendations["sakura_cloud"]
        for rec in sakura_recs:
            assert rec["specs"]["memory_gb"] >= 2.0

        gcp_recs = recommendations["google_cloud"]
        for rec in gcp_recs:
            assert rec["specs"]["memory_gb"] >= 2.0

    def test_convert_currency_default_rate(self):
        """Test currency conversion with default rate"""
        calculator = VMCalculator()
        jpy_amount = calculator.convert_currency(100.0)
        assert jpy_amount == 15000.0  # 100 USD * 150 rate

    def test_convert_currency_custom_rate(self):
        """Test currency conversion with custom rate"""
        calculator = VMCalculator()
        jpy_amount = calculator.convert_currency(100.0, 140.0)
        assert jpy_amount == 14000.0  # 100 USD * 140 rate

    def test_hours_per_month_constant(self):
        """Test hours per month constant"""
        calculator = VMCalculator()
        assert calculator.HOURS_PER_MONTH == 730

    def test_get_azure_cost_valid_instance(self):
        """Test Azure cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_azure_cost("B2ms")

        assert result is not None
        assert result["provider"] == "azure"
        assert result["instance_type"] == "B2ms"
        assert result["hourly_cost_usd"] == 0.0832
        assert result["monthly_cost_usd"] == pytest.approx(0.0832 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 8

    def test_get_azure_cost_b1ls(self):
        """Test Azure cost calculation for B1ls (cheapest option)"""
        calculator = VMCalculator()
        result = calculator.get_azure_cost("B1ls")

        assert result is not None
        assert result["provider"] == "azure"
        assert result["instance_type"] == "B1ls"
        assert result["hourly_cost_usd"] == 0.0092
        assert result["monthly_cost_usd"] == pytest.approx(0.0092 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 0.5

    def test_get_azure_cost_b1s(self):
        """Test Azure cost calculation for B1s"""
        calculator = VMCalculator()
        result = calculator.get_azure_cost("B1s")

        assert result is not None
        assert result["provider"] == "azure"
        assert result["instance_type"] == "B1s"
        assert result["hourly_cost_usd"] == 0.0104
        assert result["monthly_cost_usd"] == pytest.approx(0.0104 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 1

    def test_get_azure_cost_a1_basic(self):
        """Test Azure cost calculation for A1 Basic"""
        calculator = VMCalculator()
        result = calculator.get_azure_cost("A1_Basic")

        assert result is not None
        assert result["provider"] == "azure"
        assert result["instance_type"] == "A1_Basic"
        assert result["hourly_cost_usd"] == 0.016
        assert result["monthly_cost_usd"] == pytest.approx(0.016 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 1.75

    def test_get_azure_cost_invalid_instance(self):
        """Test Azure cost calculation for invalid instance"""
        calculator = VMCalculator()
        result = calculator.get_azure_cost("invalid.instance")
        assert result is None

    def test_get_oci_cost_valid_instance(self):
        """Test OCI cost calculation for valid instance"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("VM.Standard.E4.Flex_2_16")

        assert result is not None
        assert result["provider"] == "oci"
        assert result["instance_type"] == "VM.Standard.E4.Flex_2_16"
        assert result["hourly_cost_usd"] == 0.049
        assert result["monthly_cost_usd"] == pytest.approx(0.049 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 2
        assert result["specs"]["memory_gb"] == 16

    def test_get_oci_cost_e2_micro(self):
        """Test OCI cost calculation for E2.1.Micro (cheapest paid option)"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("VM.Standard.E2.1.Micro")

        assert result is not None
        assert result["provider"] == "oci"
        assert result["instance_type"] == "VM.Standard.E2.1.Micro"
        assert result["hourly_cost_usd"] == 0.005
        assert result["monthly_cost_usd"] == pytest.approx(0.005 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 1

    def test_get_oci_cost_a1_flex(self):
        """Test OCI cost calculation for A1.Flex"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("VM.Standard.A1.Flex_1_6")

        assert result is not None
        assert result["provider"] == "oci"
        assert result["instance_type"] == "VM.Standard.A1.Flex_1_6"
        assert result["hourly_cost_usd"] == 0.015
        assert result["monthly_cost_usd"] == pytest.approx(0.015 * 730, rel=1e-3)
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 6

    def test_get_oci_cost_free_tier(self):
        """Test OCI cost calculation for Always Free tier"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("VM.Standard.E2.1.Micro_Free")

        assert result is not None
        assert result["provider"] == "oci"
        assert result["instance_type"] == "VM.Standard.E2.1.Micro_Free"
        assert result["hourly_cost_usd"] == 0.0
        assert result["monthly_cost_usd"] == 0.0
        assert result["specs"]["vcpu"] == 1
        assert result["specs"]["memory_gb"] == 1

    def test_get_oci_cost_a1_free_tier(self):
        """Test OCI cost calculation for A1.Flex Always Free tier"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("VM.Standard.A1.Flex_Free")

        assert result is not None
        assert result["provider"] == "oci"
        assert result["instance_type"] == "VM.Standard.A1.Flex_Free"
        assert result["hourly_cost_usd"] == 0.0
        assert result["monthly_cost_usd"] == 0.0
        assert result["specs"]["vcpu"] == 4
        assert result["specs"]["memory_gb"] == 24

    def test_get_oci_cost_invalid_instance(self):
        """Test OCI cost calculation for invalid instance"""
        calculator = VMCalculator()
        result = calculator.get_oci_cost("invalid.instance")
        assert result is None

    def test_calculate_vm_cost_azure(self):
        """Test VM cost calculation for Azure"""
        calculator = VMCalculator()
        config = VMConfig(provider="azure", instance_type="B2ms", region="japaneast")

        result = calculator.calculate_vm_cost(config)

        assert result is not None
        assert result["provider"] == "azure"
        assert result["monthly_cost_usd"] == pytest.approx(0.0832 * 730, rel=1e-3)
        assert result["configuration"]["provider"] == "azure"
        assert result["configuration"]["instance_type"] == "B2ms"

    def test_calculate_vm_cost_oci(self):
        """Test VM cost calculation for OCI"""
        calculator = VMCalculator()
        config = VMConfig(
            provider="oci",
            instance_type="VM.Standard.E4.Flex_2_16",
            region="ap-tokyo-1",
        )

        result = calculator.calculate_vm_cost(config)

        assert result is not None
        assert result["provider"] == "oci"
        assert result["monthly_cost_usd"] == pytest.approx(0.049 * 730, rel=1e-3)
        assert result["configuration"]["provider"] == "oci"
        assert result["configuration"]["instance_type"] == "VM.Standard.E4.Flex_2_16"

    def test_get_available_instances_azure(self):
        """Test getting available Azure instances"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("azure")

        # Test existing instances
        assert "B2ms" in instances
        assert instances["B2ms"]["hourly_cost_usd"] == 0.0832
        assert instances["B2ms"]["specs"]["memory_gb"] == 8

        # Test new cheapest instances
        assert "B1ls" in instances
        assert instances["B1ls"]["hourly_cost_usd"] == 0.0092
        assert instances["B1ls"]["specs"]["memory_gb"] == 0.5

        assert "B1s" in instances
        assert instances["B1s"]["hourly_cost_usd"] == 0.0104
        assert instances["B1s"]["specs"]["memory_gb"] == 1

        assert "A1_Basic" in instances
        assert instances["A1_Basic"]["hourly_cost_usd"] == 0.016
        assert instances["A1_Basic"]["specs"]["memory_gb"] == 1.75

    def test_get_available_instances_oci(self):
        """Test getting available OCI instances"""
        calculator = VMCalculator()
        instances = calculator.get_available_instances("oci")

        # Test existing instances
        assert "VM.Standard.E4.Flex_2_16" in instances
        assert instances["VM.Standard.E4.Flex_2_16"]["hourly_cost_usd"] == 0.049
        assert instances["VM.Standard.E4.Flex_2_16"]["specs"]["memory_gb"] == 16

        # Test new cheapest instances
        assert "VM.Standard.E2.1.Micro" in instances
        assert instances["VM.Standard.E2.1.Micro"]["hourly_cost_usd"] == 0.005
        assert instances["VM.Standard.E2.1.Micro"]["specs"]["memory_gb"] == 1

        assert "VM.Standard.A1.Flex_1_6" in instances
        assert instances["VM.Standard.A1.Flex_1_6"]["hourly_cost_usd"] == 0.015
        assert instances["VM.Standard.A1.Flex_1_6"]["specs"]["memory_gb"] == 6

        # Test always free instances
        assert "VM.Standard.E2.1.Micro_Free" in instances
        assert instances["VM.Standard.E2.1.Micro_Free"]["hourly_cost_usd"] == 0.0
        assert instances["VM.Standard.E2.1.Micro_Free"]["specs"]["memory_gb"] == 1

        assert "VM.Standard.A1.Flex_Free" in instances
        assert instances["VM.Standard.A1.Flex_Free"]["hourly_cost_usd"] == 0.0
        assert instances["VM.Standard.A1.Flex_Free"]["specs"]["memory_gb"] == 24

    def test_recommend_instance_for_lambda_512mb_with_azure_oci(self):
        """Test instance recommendation for 512MB Lambda including Azure and OCI"""
        calculator = VMCalculator()
        recommendations = calculator.recommend_instance_for_lambda(512)

        assert "azure" in recommendations
        assert "oci" in recommendations

        azure_recs = recommendations["azure"]
        assert len(azure_recs) > 0
        for rec in azure_recs:
            assert rec["specs"]["memory_gb"] >= 0.5

        oci_recs = recommendations["oci"]
        assert len(oci_recs) > 0
        for rec in oci_recs:
            assert rec["specs"]["memory_gb"] >= 0.5

    def test_recommend_instance_for_lambda_2048mb_with_azure_oci(self):
        """Test instance recommendation for 2048MB Lambda including Azure and OCI"""
        calculator = VMCalculator()
        recommendations = calculator.recommend_instance_for_lambda(2048)

        azure_recs = recommendations["azure"]
        for rec in azure_recs:
            assert rec["specs"]["memory_gb"] >= 2.0

        oci_recs = recommendations["oci"]
        for rec in oci_recs:
            assert rec["specs"]["memory_gb"] >= 2.0
