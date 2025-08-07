"""
Unit tests for calculation service
Tests the centralized calculation service functionality
"""
import pytest
from unittest.mock import patch, MagicMock

from app.services.calculation_service import CalculationService, get_calculation_service
from app.utils.validation import ValidationError


class TestCalculationService:
    """Test the CalculationService class"""
    
    def test_service_initialization(self):
        """Test calculation service initializes correctly"""
        service = CalculationService()
        assert service is not None
    
    @patch("app.services.calculation_service.validate_lambda_inputs")
    @patch("app.services.calculation_service.get_lambda_calculator")
    def test_calculate_lambda_cost_success(self, mock_get_calculator, mock_validate):
        """Test successful Lambda cost calculation"""
        service = CalculationService()
        
        # Mock validation
        validated_data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000000,
            "include_free_tier": True,
            "egress_per_request_kb": 10.0,
            "internet_transfer_ratio": 50.0
        }
        mock_validate.return_value = validated_data
        
        # Mock calculator
        mock_calculator = MagicMock()
        mock_result = {"total_cost": 5.0}
        mock_calculator.calculate_total_cost.return_value = mock_result
        mock_get_calculator.return_value = mock_calculator
        
        # Test calculation
        data = {"memory_mb": 512, "execution_time_seconds": 1.0}
        result = service.calculate_lambda_cost(data)
        
        assert result == mock_result
        mock_validate.assert_called_once_with(data)
        mock_calculator.calculate_total_cost.assert_called_once()
    
    @patch("app.services.calculation_service.validate_lambda_inputs")
    def test_calculate_lambda_cost_validation_error(self, mock_validate):
        """Test Lambda cost calculation with validation error"""
        service = CalculationService()
        mock_validate.side_effect = ValidationError("Invalid input")
        
        with pytest.raises(ValidationError, match="Invalid input"):
            service.calculate_lambda_cost({})
    
    @patch("app.services.calculation_service.validate_lambda_inputs")
    @patch("app.services.calculation_service.get_lambda_calculator")
    def test_calculate_lambda_cost_with_custom_rates(self, mock_get_calculator, mock_validate):
        """Test Lambda cost calculation with custom egress rates"""
        service = CalculationService()
        
        # Mock validation
        validated_data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000000,
            "include_free_tier": True
        }
        mock_validate.return_value = validated_data
        
        # Mock calculator
        mock_calculator = MagicMock()
        mock_result = {"total_cost": 10.0}
        mock_calculator.calculate_total_cost.return_value = mock_result
        mock_get_calculator.return_value = mock_calculator
        
        # Test calculation with custom rates
        data = {"memory_mb": 512}
        custom_rates = {"aws": 0.12}
        result = service.calculate_lambda_cost(data, custom_rates, False)
        
        assert result == mock_result
        mock_calculator.calculate_total_cost.assert_called_once()
        call_args = mock_calculator.calculate_total_cost.call_args
        assert call_args[0][1] == custom_rates  # custom_egress_rates
        assert call_args[0][2] is False  # include_egress_free_tier
    
    @patch("app.services.calculation_service.validate_vm_inputs")
    @patch("app.services.calculation_service.get_vm_calculator")
    def test_calculate_vm_cost_success(self, mock_get_calculator, mock_validate):
        """Test successful VM cost calculation"""
        service = CalculationService()
        
        # Mock validation
        validated_data = {"instance_type": "t3.micro", "provider": "aws"}
        mock_validate.return_value = validated_data
        
        # Mock calculator
        mock_calculator = MagicMock()
        mock_result = {"monthly_cost": 10.0}
        mock_calculator.calculate_cost.return_value = mock_result
        mock_get_calculator.return_value = mock_calculator
        
        # Test calculation
        data = {"instance_type": "t3.micro"}
        result = service.calculate_vm_cost(data)
        
        assert result == mock_result
        mock_validate.assert_called_once_with(data)
        mock_calculator.calculate_cost.assert_called_once_with(validated_data)
    
    @patch("app.services.calculation_service.validate_vm_inputs")
    def test_calculate_vm_cost_validation_error(self, mock_validate):
        """Test VM cost calculation with validation error"""
        service = CalculationService()
        mock_validate.side_effect = ValidationError("Invalid VM config")
        
        with pytest.raises(ValidationError, match="Invalid VM config"):
            service.calculate_vm_cost({})
    
    @patch("app.services.calculation_service.validate_serverless_inputs")
    @patch("app.services.calculation_service.get_serverless_calculator")
    def test_calculate_serverless_cost_success(self, mock_get_calculator, mock_validate):
        """Test successful serverless cost calculation"""
        service = CalculationService()
        
        # Mock validation
        validated_data = {"provider": "gcp_functions", "memory_mb": 256}
        mock_validate.return_value = validated_data
        
        # Mock calculator
        mock_calculator = MagicMock()
        mock_result = {"total_cost": 8.0}
        mock_calculator.calculate.return_value = mock_result
        mock_get_calculator.return_value = mock_calculator
        
        # Test calculation
        data = {"provider": "gcp_functions"}
        result = service.calculate_serverless_cost(data)
        
        assert result == mock_result
        mock_validate.assert_called_once_with(data)
        mock_calculator.calculate.assert_called_once_with(validated_data)
    
    @patch("app.services.calculation_service.validate_serverless_inputs")
    def test_calculate_serverless_cost_validation_error(self, mock_validate):
        """Test serverless cost calculation with validation error"""
        service = CalculationService()
        mock_validate.side_effect = ValidationError("Invalid serverless config")
        
        with pytest.raises(ValidationError, match="Invalid serverless config"):
            service.calculate_serverless_cost({})
    
    @patch.object(CalculationService, 'calculate_lambda_cost')
    @patch.object(CalculationService, 'calculate_vm_cost')
    def test_calculate_comparison_success(self, mock_vm_calc, mock_lambda_calc):
        """Test successful cost comparison"""
        service = CalculationService()
        
        # Mock calculation results
        lambda_result = {"total_cost": 5.0}
        vm_result = {"total_cost": 10.0}
        mock_lambda_calc.return_value = lambda_result
        mock_vm_calc.return_value = vm_result
        
        # Test comparison
        lambda_data = {"memory_mb": 512}
        vm_data = {"instance_type": "t3.micro"}
        result = service.calculate_comparison(lambda_data, vm_data)
        
        assert result["lambda"] == lambda_result
        assert result["vm"] == vm_result
        assert result["cost_difference"] == -5.0  # Lambda cheaper
        assert result["cheaper_option"] == "lambda"
        assert "break_even_executions" in result
        
        mock_lambda_calc.assert_called_once_with(lambda_data)
        mock_vm_calc.assert_called_once_with(vm_data)
    
    @patch.object(CalculationService, 'calculate_lambda_cost')
    @patch.object(CalculationService, 'calculate_vm_cost')
    def test_calculate_comparison_vm_cheaper(self, mock_vm_calc, mock_lambda_calc):
        """Test cost comparison when VM is cheaper"""
        service = CalculationService()
        
        # Mock calculation results - VM cheaper
        lambda_result = {"total_cost": 15.0}
        vm_result = {"total_cost": 10.0}
        mock_lambda_calc.return_value = lambda_result
        mock_vm_calc.return_value = vm_result
        
        # Test comparison
        lambda_data = {"memory_mb": 512}
        vm_data = {"instance_type": "t3.micro"}
        result = service.calculate_comparison(lambda_data, vm_data, include_break_even=False)
        
        assert result["cost_difference"] == 5.0  # Lambda more expensive
        assert result["cheaper_option"] == "vm"
        assert "break_even_executions" not in result
    
    def test_calculate_break_even_point_success(self):
        """Test successful break-even point calculation"""
        service = CalculationService()
        
        lambda_data = {"cost_per_execution": 0.001}
        vm_data = {"monthly_cost": 10.0}
        
        result = service._calculate_break_even_point(lambda_data, vm_data)
        assert result == 10000  # 10.0 / 0.001
    
    def test_calculate_break_even_point_zero_execution_cost(self):
        """Test break-even calculation with zero execution cost"""
        service = CalculationService()
        
        lambda_data = {"cost_per_execution": 0}
        vm_data = {"monthly_cost": 10.0}
        
        result = service._calculate_break_even_point(lambda_data, vm_data)
        assert result is None
    
    def test_calculate_break_even_point_missing_data(self):
        """Test break-even calculation with missing data"""
        service = CalculationService()
        
        lambda_data = {}
        vm_data = {}
        
        result = service._calculate_break_even_point(lambda_data, vm_data)
        assert result is None
    
    def test_calculate_break_even_point_invalid_data(self):
        """Test break-even calculation with invalid data"""
        service = CalculationService()
        
        lambda_data = {"cost_per_execution": "invalid"}
        vm_data = {"monthly_cost": "invalid"}
        
        result = service._calculate_break_even_point(lambda_data, vm_data)
        assert result is None


class TestGlobalCalculationService:
    """Test global calculation service function"""
    
    def test_get_calculation_service(self):
        """Test getting global calculation service"""
        service = get_calculation_service()
        assert isinstance(service, CalculationService)
        
        # Should return the same instance (singleton)
        service2 = get_calculation_service()
        assert service is service2