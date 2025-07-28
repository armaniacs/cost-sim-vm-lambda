"""
Input validation utilities for security enhancement
PBI-SEC-ESSENTIAL implementation
"""
from typing import Any, Union


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


def safe_int_conversion(value: Any, min_val: int, max_val: int, field_name: str) -> int:
    """
    Safely convert value to int with bounds checking
    
    Args:
        value: Value to convert
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Field name for error messages
        
    Returns:
        Validated integer value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        int_val = int(value)
        if not (min_val <= int_val <= max_val):
            raise ValidationError(f"{field_name} must be between {min_val} and {max_val}")
        return int_val
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a valid integer")


def safe_float_conversion(value: Any, min_val: float, max_val: float, field_name: str) -> float:
    """
    Safely convert value to float with bounds checking
    
    Args:
        value: Value to convert
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Field name for error messages
        
    Returns:
        Validated float value
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        float_val = float(value)
        if not (min_val <= float_val <= max_val):
            raise ValidationError(f"{field_name} must be between {min_val} and {max_val}")
        return float_val
    except (ValueError, TypeError):
        raise ValidationError(f"Invalid {field_name}: must be a valid number")


def validate_lambda_inputs(data: dict) -> dict:
    """
    Validate Lambda configuration inputs with security boundaries
    
    Args:
        data: Input data dictionary
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If any validation fails
    """
    validated = {}
    
    # Memory validation: AWS Lambda supports 128MB to 10,240MB
    validated['memory_mb'] = safe_int_conversion(
        data.get('memory_mb', 0), 
        128, 
        10240, 
        "Memory size"
    )
    
    # Execution time validation: 0.1 seconds to 15 minutes (900 seconds)
    validated['execution_time_seconds'] = safe_float_conversion(
        data.get('execution_time_seconds', 0),
        0.1,
        900.0,
        "Execution time"
    )
    
    # Monthly executions validation: 0 to 1 billion
    validated['monthly_executions'] = safe_int_conversion(
        data.get('monthly_executions', 0),
        0,
        1_000_000_000,
        "Monthly executions"
    )
    
    # Optional fields with validation
    if 'egress_per_request_kb' in data:
        validated['egress_per_request_kb'] = safe_float_conversion(
            data['egress_per_request_kb'],
            0.0,
            1_000_000.0,  # 1GB per request maximum
            "Egress per request"
        )
    
    if 'internet_transfer_ratio' in data:
        validated['internet_transfer_ratio'] = safe_float_conversion(
            data['internet_transfer_ratio'],
            0.0,
            100.0,
            "Internet transfer ratio"
        )
    
    # Boolean fields (pass through with default values)
    validated['include_free_tier'] = data.get('include_free_tier', True)
    
    return validated


def validate_vm_inputs(data: dict) -> dict:
    """
    Validate VM configuration inputs with security boundaries
    
    Args:
        data: Input data dictionary
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If any validation fails
    """
    validated = {}
    
    # Provider validation
    provider = data.get('provider', '').strip()
    allowed_providers = ['aws_ec2', 'sakura_cloud', 'google_cloud']
    if not provider:
        raise ValidationError("Provider is required")
    if provider not in allowed_providers:
        raise ValidationError(f"Provider must be one of: {', '.join(allowed_providers)}")
    validated['provider'] = provider
    
    # Instance type validation (must be non-empty string)
    instance_type = data.get('instance_type', '').strip()
    if not instance_type:
        raise ValidationError("Instance type is required")
    if len(instance_type) > 50:
        raise ValidationError("Instance type must be 50 characters or less")
    validated['instance_type'] = instance_type
    
    # Region validation (optional)
    region = data.get('region', 'ap-northeast-1').strip()
    if len(region) > 50:
        raise ValidationError("Region must be 50 characters or less")
    validated['region'] = region
    
    # Optional fields with validation
    if 'monthly_executions' in data:
        validated['monthly_executions'] = safe_int_conversion(
            data['monthly_executions'],
            0,
            1_000_000_000,
            "Monthly executions"
        )
    
    if 'egress_per_request_kb' in data:
        validated['egress_per_request_kb'] = safe_float_conversion(
            data['egress_per_request_kb'],
            0.0,
            1_000_000.0,  # 1GB per request maximum
            "Egress per request"
        )
    
    if 'internet_transfer_ratio' in data:
        validated['internet_transfer_ratio'] = safe_float_conversion(
            data['internet_transfer_ratio'],
            0.0,
            100.0,
            "Internet transfer ratio"
        )
    
    return validated


def validate_serverless_inputs(data: dict) -> dict:
    """
    Validate Serverless configuration inputs with security boundaries
    
    Args:
        data: Input data dictionary
        
    Returns:
        Validated data dictionary
        
    Raises:
        ValidationError: If any validation fails
    """
    validated = {}
    
    # Provider validation (will be checked against supported providers in endpoint)
    provider = data.get('provider', '').strip()
    if not provider:
        raise ValidationError("Provider is required")
    validated['provider'] = provider
    
    # Memory validation (varies by provider, using conservative range)
    validated['memory_mb'] = safe_int_conversion(
        data.get('memory_mb', 0),
        128,
        32768,  # 32GB maximum for most providers
        "Memory size"
    )
    
    # Execution time validation
    validated['execution_time_seconds'] = safe_float_conversion(
        data.get('execution_time_seconds', 0),
        0.1,
        900.0,
        "Execution time"
    )
    
    # Monthly executions validation
    validated['monthly_executions'] = safe_int_conversion(
        data.get('monthly_executions', 0),
        0,
        1_000_000_000,
        "Monthly executions"
    )
    
    # Optional CPU count validation
    if 'cpu_count' in data:
        validated['cpu_count'] = safe_float_conversion(
            data['cpu_count'],
            0.1,
            64.0,  # Maximum 64 CPUs
            "CPU count"
        )
    
    # Optional egress validation
    if 'egress_per_request_kb' in data:
        validated['egress_per_request_kb'] = safe_float_conversion(
            data['egress_per_request_kb'],
            0.0,
            1_000_000.0,
            "Egress per request"
        )
    
    # Optional internet transfer ratio validation
    if 'internet_transfer_ratio' in data:
        validated['internet_transfer_ratio'] = safe_float_conversion(
            data['internet_transfer_ratio'],
            0.0,
            100.0,
            "Internet transfer ratio"
        )
    
    # Optional exchange rate validation
    if 'exchange_rate' in data:
        validated['exchange_rate'] = safe_float_conversion(
            data['exchange_rate'],
            1.0,
            1000.0,  # Reasonable exchange rate range
            "Exchange rate"
        )
    
    # Boolean fields
    validated['include_free_tier'] = data.get('include_free_tier', True)
    
    return validated