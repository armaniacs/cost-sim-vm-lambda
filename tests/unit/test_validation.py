"""
Unit tests for validation utilities
Tests security-critical input validation functions
"""
import pytest

from app.utils.validation import (
    ValidationError,
    safe_int_conversion,
    safe_float_conversion,
    validate_lambda_inputs,
    validate_vm_inputs,
    validate_serverless_inputs
)


class TestValidationUtilities:
    """Test validation utility functions"""
    
    def test_validation_error_creation(self):
        """Test ValidationError exception creation"""
        error = ValidationError("test error")
        assert str(error) == "test error"
    
    def test_safe_int_conversion_valid(self):
        """Test safe integer conversion with valid input"""
        result = safe_int_conversion(42, 0, 100, "test_field")
        assert result == 42
        assert isinstance(result, int)
    
    def test_safe_int_conversion_string_number(self):
        """Test safe integer conversion with string number"""
        result = safe_int_conversion("42", 0, 100, "test_field")
        assert result == 42
        assert isinstance(result, int)
    
    def test_safe_int_conversion_float_input(self):
        """Test safe integer conversion with float input"""
        result = safe_int_conversion(42.7, 0, 100, "test_field")
        assert result == 42
        assert isinstance(result, int)
    
    def test_safe_int_conversion_below_min(self):
        """Test safe integer conversion below minimum"""
        with pytest.raises(ValidationError, match="test_field must be between 10 and 100"):
            safe_int_conversion(5, 10, 100, "test_field")
    
    def test_safe_int_conversion_above_max(self):
        """Test safe integer conversion above maximum"""
        with pytest.raises(ValidationError, match="test_field must be between 10 and 100"):
            safe_int_conversion(150, 10, 100, "test_field")
    
    def test_safe_int_conversion_invalid_string(self):
        """Test safe integer conversion with invalid string"""
        with pytest.raises(ValidationError, match="Invalid test_field: must be a valid integer"):
            safe_int_conversion("not_a_number", 0, 100, "test_field")
    
    def test_safe_int_conversion_none(self):
        """Test safe integer conversion with None"""
        with pytest.raises(ValidationError, match="Invalid test_field: must be a valid integer"):
            safe_int_conversion(None, 0, 100, "test_field")
    
    def test_safe_float_conversion_valid(self):
        """Test safe float conversion with valid input"""
        result = safe_float_conversion(3.14, 0.0, 10.0, "test_field")
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_safe_float_conversion_integer_input(self):
        """Test safe float conversion with integer input"""
        result = safe_float_conversion(42, 0.0, 100.0, "test_field")
        assert result == 42.0
        assert isinstance(result, float)
    
    def test_safe_float_conversion_string_number(self):
        """Test safe float conversion with string number"""
        result = safe_float_conversion("3.14", 0.0, 10.0, "test_field")
        assert result == 3.14
        assert isinstance(result, float)
    
    def test_safe_float_conversion_below_min(self):
        """Test safe float conversion below minimum"""
        with pytest.raises(ValidationError, match="test_field must be between 1.0 and 10.0"):
            safe_float_conversion(0.5, 1.0, 10.0, "test_field")
    
    def test_safe_float_conversion_above_max(self):
        """Test safe float conversion above maximum"""
        with pytest.raises(ValidationError, match="test_field must be between 1.0 and 10.0"):
            safe_float_conversion(15.0, 1.0, 10.0, "test_field")
    
    def test_safe_float_conversion_invalid_string(self):
        """Test safe float conversion with invalid string"""
        with pytest.raises(ValidationError, match="Invalid test_field: must be a valid number"):
            safe_float_conversion("not_a_number", 0.0, 100.0, "test_field")


class TestLambdaInputValidation:
    """Test Lambda input validation"""
    
    def test_validate_lambda_inputs_valid(self):
        """Test valid Lambda input validation"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.5,
            "monthly_executions": 1000000,
            "include_free_tier": True,
            "egress_per_request_kb": 10.0,
            "internet_transfer_ratio": 50.0
        }
        result = validate_lambda_inputs(data)
        
        assert result["memory_mb"] == 512
        assert result["execution_time_seconds"] == 1.5
        assert result["monthly_executions"] == 1000000
        assert result["include_free_tier"] is True
        assert result["egress_per_request_kb"] == 10.0
        assert result["internet_transfer_ratio"] == 50.0
    
    def test_validate_lambda_inputs_minimal(self):
        """Test Lambda validation with minimal required fields"""
        data = {
            "memory_mb": 128,
            "execution_time_seconds": 0.1,
            "monthly_executions": 100,
            "include_free_tier": False
        }
        result = validate_lambda_inputs(data)
        
        assert result["memory_mb"] == 128
        assert result["execution_time_seconds"] == 0.1
        assert result["monthly_executions"] == 100
        assert result["include_free_tier"] is False
        # Optional fields are not included if not provided
        assert "egress_per_request_kb" not in result
        assert "internet_transfer_ratio" not in result
    
    def test_validate_lambda_inputs_missing_memory(self):
        """Test Lambda validation with missing memory"""
        data = {
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        # The actual implementation defaults to 0 which fails validation bounds
        with pytest.raises(ValidationError, match="Memory size must be between 128 and 10240"):
            validate_lambda_inputs(data)
    
    def test_validate_lambda_inputs_invalid_memory(self):
        """Test Lambda validation with invalid memory"""
        data = {
            "memory_mb": 32,  # Below minimum
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
    
    def test_validate_lambda_inputs_invalid_execution_time(self):
        """Test Lambda validation with invalid execution time"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": -1,  # Negative
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
    
    def test_validate_lambda_inputs_invalid_executions(self):
        """Test Lambda validation with invalid monthly executions"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": -100,  # Negative
            "include_free_tier": True
        }
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)


class TestVMInputValidation:
    """Test VM input validation"""
    
    def test_validate_vm_inputs_valid(self):
        """Test valid VM input validation"""
        data = {
            "provider": "aws_ec2",
            "instance_type": "t3.small",
            "region": "ap-northeast-1",
            "monthly_executions": 1000000,
            "egress_per_request_kb": 10.0,
            "internet_transfer_ratio": 75.0
        }
        result = validate_vm_inputs(data)
        
        assert result["provider"] == "aws_ec2"
        assert result["instance_type"] == "t3.small"
        assert result["region"] == "ap-northeast-1"
        assert result["monthly_executions"] == 1000000
        assert result["egress_per_request_kb"] == 10.0
        assert result["internet_transfer_ratio"] == 75.0
    
    def test_validate_vm_inputs_minimal(self):
        """Test VM validation with minimal required fields"""
        data = {
            "provider": "sakura_cloud",
            "instance_type": "2core_4gb",
            "region": "is1a"
        }
        result = validate_vm_inputs(data)
        
        assert result["provider"] == "sakura_cloud"
        assert result["instance_type"] == "2core_4gb"
        assert result["region"] == "is1a"
        # Optional fields are not included if not provided
        assert "monthly_executions" not in result
        assert "egress_per_request_kb" not in result
        assert "internet_transfer_ratio" not in result
    
    def test_validate_vm_inputs_missing_provider(self):
        """Test VM validation with missing provider"""
        data = {
            "instance_type": "t3.small",
            "region": "ap-northeast-1"
        }
        with pytest.raises(ValidationError, match="Provider is required"):
            validate_vm_inputs(data)
    
    def test_validate_vm_inputs_invalid_provider(self):
        """Test VM validation with invalid provider"""
        data = {
            "provider": "invalid_provider",
            "instance_type": "t3.small",
            "region": "ap-northeast-1"
        }
        with pytest.raises(ValidationError, match="Provider must be one of"):
            validate_vm_inputs(data)
    
    def test_validate_vm_inputs_missing_instance_type(self):
        """Test VM validation with missing instance type"""
        data = {
            "provider": "aws_ec2",
            "region": "ap-northeast-1"
        }
        with pytest.raises(ValidationError, match="Instance type is required"):
            validate_vm_inputs(data)


class TestServerlessInputValidation:
    """Test serverless input validation"""
    
    def test_validate_serverless_inputs_valid(self):
        """Test valid serverless input validation"""
        data = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 2.0,
            "monthly_executions": 1500000,
            "cpu_count": 1.0,
            "egress_per_request_kb": 15.0,
            "internet_transfer_ratio": 80.0,
            "exchange_rate": 150.0
        }
        result = validate_serverless_inputs(data)
        
        assert result["provider"] == "gcp_functions"
        assert result["memory_mb"] == 512
        assert result["execution_time_seconds"] == 2.0
        assert result["monthly_executions"] == 1500000
        assert result["cpu_count"] == 1.0
        assert result["egress_per_request_kb"] == 15.0
        assert result["internet_transfer_ratio"] == 80.0
        assert result["exchange_rate"] == 150.0
    
    def test_validate_serverless_inputs_minimal(self):
        """Test serverless validation with minimal required fields"""
        data = {
            "provider": "aws_lambda",
            "memory_mb": 128,
            "execution_time_seconds": 0.1,
            "monthly_executions": 1000
        }
        result = validate_serverless_inputs(data)
        
        assert result["provider"] == "aws_lambda"
        assert result["memory_mb"] == 128
        assert result["execution_time_seconds"] == 0.1
        assert result["monthly_executions"] == 1000
        assert result["include_free_tier"] is True  # default
        # Optional fields are not included if not provided
        assert "egress_per_request_kb" not in result
        assert "internet_transfer_ratio" not in result
        assert "exchange_rate" not in result
    
    def test_validate_serverless_inputs_missing_provider(self):
        """Test serverless validation with missing provider"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000
        }
        with pytest.raises(ValidationError, match="Provider is required"):
            validate_serverless_inputs(data)
    
    def test_validate_serverless_inputs_invalid_provider(self):
        """Test serverless validation with invalid provider"""
        data = {
            "provider": "invalid_serverless",
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000
        }
        # The serverless validator doesn't check specific providers - that's done at endpoint level
        result = validate_serverless_inputs(data)
        assert result["provider"] == "invalid_serverless"
    
    def test_validate_serverless_inputs_gcp_cloudrun_with_cpu(self):
        """Test GCP Cloud Run validation with CPU count"""
        data = {
            "provider": "gcp_cloudrun",
            "memory_mb": 1024,
            "execution_time_seconds": 3.0,
            "monthly_executions": 500000,
            "cpu_count": 2.0
        }
        result = validate_serverless_inputs(data)
        
        assert result["provider"] == "gcp_cloudrun"
        assert result["cpu_count"] == 2.0
    
    def test_validate_serverless_inputs_invalid_cpu_count(self):
        """Test serverless validation with invalid CPU count"""
        data = {
            "provider": "gcp_cloudrun",
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "cpu_count": 0.05  # Below minimum of 0.1
        }
        with pytest.raises(ValidationError, match="CPU count must be between 0.1 and 64.0"):
            validate_serverless_inputs(data)
    
    def test_validate_serverless_inputs_invalid_exchange_rate(self):
        """Test serverless validation with invalid exchange rate"""
        data = {
            "provider": "gcp_functions",
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "exchange_rate": 0  # Invalid rate
        }
        with pytest.raises(ValidationError):
            validate_serverless_inputs(data)


class TestSecurityBoundaries:
    """Test security boundary validation"""
    
    def test_lambda_memory_boundaries(self):
        """Test Lambda memory size boundaries"""
        # Test minimum boundary
        data = {
            "memory_mb": 128,  # Minimum allowed
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        result = validate_lambda_inputs(data)
        assert result["memory_mb"] == 128
        
        # Test maximum boundary  
        data["memory_mb"] = 10240  # Maximum allowed
        result = validate_lambda_inputs(data)
        assert result["memory_mb"] == 10240
        
        # Test below minimum
        data["memory_mb"] = 127
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
            
        # Test above maximum
        data["memory_mb"] = 10241
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
    
    def test_execution_time_boundaries(self):
        """Test execution time boundaries"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 900.0,  # Maximum allowed (15 minutes)
            "monthly_executions": 1000,
            "include_free_tier": True
        }
        result = validate_lambda_inputs(data)
        assert result["execution_time_seconds"] == 900.0
        
        # Test above maximum
        data["execution_time_seconds"] = 901.0
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
    
    def test_monthly_executions_boundaries(self):
        """Test monthly executions boundaries"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000000000,  # 1 billion, maximum allowed
            "include_free_tier": True
        }
        result = validate_lambda_inputs(data)
        assert result["monthly_executions"] == 1000000000
        
        # Test above maximum
        data["monthly_executions"] = 1000000001
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)
    
    def test_egress_ratio_boundaries(self):
        """Test internet transfer ratio boundaries"""
        data = {
            "memory_mb": 512,
            "execution_time_seconds": 1.0,
            "monthly_executions": 1000,
            "include_free_tier": True,
            "internet_transfer_ratio": 0.0  # Minimum allowed
        }
        result = validate_lambda_inputs(data)
        assert result["internet_transfer_ratio"] == 0.0
        
        # Test maximum
        data["internet_transfer_ratio"] = 100.0
        result = validate_lambda_inputs(data)
        assert result["internet_transfer_ratio"] == 100.0
        
        # Test above maximum
        data["internet_transfer_ratio"] = 100.1
        with pytest.raises(ValidationError):
            validate_lambda_inputs(data)