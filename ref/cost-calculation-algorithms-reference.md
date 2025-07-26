# Cost Calculation Algorithms Reference

## Overview

This document provides detailed reference for all cost calculation algorithms implemented in the AWS Lambda vs VM Cost Simulator. The algorithms support accurate cost comparisons across 6 cloud providers with comprehensive egress cost calculations and break-even point analysis.

## Supported Providers

### Serverless Providers
- **AWS Lambda**: First-generation serverless with Tokyo region pricing
- **Google Cloud Functions**: 1st and 2nd generation support (Phase 1A implementation)

### Virtual Machine Providers
- **AWS EC2**: 6 instance types (t3.micro to c5.xlarge)
- **Google Cloud Compute Engine**: 6 instance types (e2-micro to c2-standard-4)
- **Azure Virtual Machines**: 8 instance types (B1ls to D4)
- **Oracle Cloud Infrastructure**: 7 instance types (including Always Free tier)
- **Sakura Cloud**: 5 instance types with JPY pricing

## AWS Lambda Cost Calculations

### Core Algorithm

**Request Charges**
```python
def calculate_request_charges(executions: int, include_free_tier: bool = True) -> float:
    """Calculate AWS Lambda request charges"""
    FREE_TIER_REQUESTS = 1_000_000  # 1M requests/month
    REQUEST_RATE = 0.20  # $0.20 per million requests
    
    if include_free_tier:
        billable_requests = max(0, executions - FREE_TIER_REQUESTS)
    else:
        billable_requests = executions
    
    return (billable_requests / 1_000_000) * REQUEST_RATE
```

**Compute Charges**
```python
def calculate_compute_charges(memory_mb: int, execution_time_seconds: float, 
                            executions: int, include_free_tier: bool = True) -> float:
    """Calculate AWS Lambda compute charges based on GB-seconds"""
    FREE_TIER_GB_SECONDS = 400_000  # 400K GB-seconds/month
    COMPUTE_RATE = 0.0000166667  # $0.0000166667 per GB-second
    
    # Convert memory to GB and calculate total GB-seconds
    memory_gb = memory_mb / 1024
    total_gb_seconds = memory_gb * execution_time_seconds * executions
    
    if include_free_tier:
        billable_gb_seconds = max(0, total_gb_seconds - FREE_TIER_GB_SECONDS)
    else:
        billable_gb_seconds = total_gb_seconds
    
    return billable_gb_seconds * COMPUTE_RATE
```

**Total Lambda Cost**
```python
def calculate_total_cost(config: LambdaConfig) -> LambdaResult:
    """Calculate total AWS Lambda cost including egress"""
    request_cost = calculate_request_charges(config.monthly_executions, config.include_free_tier)
    compute_cost = calculate_compute_charges(config.memory_mb, config.execution_time_seconds, 
                                           config.monthly_executions, config.include_free_tier)
    
    # Calculate egress costs if specified
    egress_cost = 0.0
    if config.egress_per_request_kb > 0:
        egress_config = EgressConfig(
            provider="aws_lambda",
            total_transfer_gb=(config.egress_per_request_kb * config.monthly_executions) / (1024 * 1024),
            internet_transfer_ratio=config.internet_transfer_ratio
        )
        egress_cost = EgressCalculator().calculate_cost(egress_config).total_cost_usd
    
    total_usd = request_cost + compute_cost + egress_cost
    total_jpy = total_usd * config.exchange_rate
    
    return LambdaResult(
        total_cost_usd=total_usd,
        total_cost_jpy=total_jpy,
        request_cost=request_cost,
        compute_cost=compute_cost,
        egress_cost=egress_cost,
        free_tier_savings=calculate_free_tier_savings(config)
    )
```

### Free Tier Calculation

**Free Tier Savings Algorithm**
```python
def calculate_free_tier_savings(config: LambdaConfig) -> dict:
    """Calculate savings from AWS Lambda free tier"""
    if not config.include_free_tier:
        return {"request_savings": 0.0, "compute_savings": 0.0, "total_savings": 0.0}
    
    # Request savings
    eligible_requests = min(config.monthly_executions, 1_000_000)
    request_savings = (eligible_requests / 1_000_000) * 0.20
    
    # Compute savings
    memory_gb = config.memory_mb / 1024
    total_gb_seconds = memory_gb * config.execution_time_seconds * config.monthly_executions
    eligible_gb_seconds = min(total_gb_seconds, 400_000)
    compute_savings = eligible_gb_seconds * 0.0000166667
    
    return {
        "request_savings": request_savings,
        "compute_savings": compute_savings,
        "total_savings": request_savings + compute_savings
    }
```

## Virtual Machine Cost Calculations

### Multi-Provider Pricing Matrix

**AWS EC2 (USD/hour, Tokyo region)**
```python
AWS_EC2_PRICING = {
    "t3.micro": 0.0116,     # 1 vCPU, 1 GiB RAM
    "t3.small": 0.0232,     # 1 vCPU, 2 GiB RAM
    "t3.medium": 0.0464,    # 2 vCPU, 4 GiB RAM
    "t3.large": 0.0928,     # 2 vCPU, 8 GiB RAM
    "c5.large": 0.096,      # 2 vCPU, 4 GiB RAM
    "c5.xlarge": 0.192      # 4 vCPU, 8 GiB RAM
}
```

**Google Cloud Compute Engine (USD/hour, asia-northeast1)**
```python
GCP_PRICING = {
    "e2-micro": 0.008,      # 0.25-2 vCPU, 1 GiB RAM
    "e2-small": 0.016,      # 0.5-2 vCPU, 2 GiB RAM
    "e2-medium": 0.032,     # 1-2 vCPU, 4 GiB RAM
    "n1-standard-1": 0.0475, # 1 vCPU, 3.75 GiB RAM
    "n1-standard-2": 0.095,  # 2 vCPU, 7.5 GiB RAM
    "c2-standard-4": 0.19    # 4 vCPU, 16 GiB RAM
}
```

**Azure Virtual Machines (USD/hour, Japan East)**
```python
AZURE_PRICING = {
    "B1ls": 0.0052,         # 1 vCPU, 0.5 GiB RAM
    "B1s": 0.0104,          # 1 vCPU, 1 GiB RAM
    "B2s": 0.0416,          # 2 vCPU, 4 GiB RAM
    "D2s_v3": 0.096,        # 2 vCPU, 8 GiB RAM
    "D4s_v3": 0.192,        # 4 vCPU, 16 GiB RAM
    "F2s_v2": 0.085         # 2 vCPU, 4 GiB RAM
}
```

**Oracle Cloud Infrastructure (USD/hour, Japan East)**
```python
OCI_PRICING = {
    "VM.Standard.E2.1.Micro": 0.0,     # Always Free (1 OCPU, 1 GiB)
    "VM.Standard.E2.1": 0.0255,        # 1 OCPU, 8 GiB RAM
    "VM.Standard.E2.2": 0.051,         # 2 OCPU, 16 GiB RAM
    "VM.Standard.E2.4": 0.102,         # 4 OCPU, 32 GiB RAM
    "VM.Standard.E3.Flex": 0.015       # Flexible OCPU/RAM
}
```

**Sakura Cloud (JPY/month, Tokyo)**
```python
SAKURA_PRICING = {
    "1core_1gb": 1848,      # 1 core, 1 GiB RAM, 20 GiB SSD
    "2core_2gb": 3696,      # 2 core, 2 GiB RAM, 20 GiB SSD
    "4core_8gb": 14080,     # 4 core, 8 GiB RAM, 40 GiB SSD
    "6core_12gb": 28160     # 6 core, 12 GiB RAM, 60 GiB SSD
}
```

### VM Cost Calculation Algorithm

**Monthly Cost Calculation**
```python
def calculate_vm_cost(provider: str, instance_type: str, exchange_rate: float = 150.0) -> VMResult:
    """Calculate monthly VM cost for any provider"""
    HOURS_PER_MONTH = 730  # Standard monthly hours
    
    if provider == "aws_ec2":
        hourly_rate_usd = AWS_EC2_PRICING[instance_type]
        monthly_cost_usd = hourly_rate_usd * HOURS_PER_MONTH
        monthly_cost_jpy = monthly_cost_usd * exchange_rate
        
    elif provider == "sakura_cloud":
        monthly_cost_jpy = SAKURA_PRICING[instance_type]
        monthly_cost_usd = monthly_cost_jpy / exchange_rate
        
    # Calculate egress costs if specified
    egress_cost = calculate_vm_egress_cost(provider, config)
    
    return VMResult(
        provider=provider,
        instance_type=instance_type,
        monthly_cost_usd=monthly_cost_usd + egress_cost.total_cost_usd,
        monthly_cost_jpy=monthly_cost_jpy + egress_cost.total_cost_jpy,
        compute_cost=monthly_cost_usd,
        egress_cost=egress_cost.total_cost_usd
    )
```

### Instance Recommendation Algorithm

**Memory-Based Recommendation**
```python
def recommend_vm_instance(lambda_memory_mb: int, provider: str) -> str:
    """Recommend VM instance based on Lambda memory requirements"""
    memory_gb = lambda_memory_mb / 1024
    
    if provider == "aws_ec2":
        if memory_gb <= 1:
            return "t3.micro"   # 1 GiB RAM
        elif memory_gb <= 2:
            return "t3.small"   # 2 GiB RAM
        elif memory_gb <= 4:
            return "t3.medium"  # 4 GiB RAM
        elif memory_gb <= 8:
            return "t3.large"   # 8 GiB RAM
        else:
            return "c5.xlarge"  # 8 GiB RAM
    
    # Similar logic for other providers with memory optimization
```

## Egress Cost Calculations

### Provider-Specific Egress Rates

**Data Transfer Pricing (per GB)**
```python
EGRESS_RATES = {
    "aws_lambda": 0.114,    # AWS Lambda data transfer out
    "aws_ec2": 0.114,       # AWS EC2 data transfer out
    "google_cloud": 0.12,   # Google Cloud egress
    "azure": 0.12,          # Azure bandwidth out
    "oci": 0.025,           # OCI data transfer (after 10TB free)
    "sakura_cloud": 0.0     # Free egress
}

FREE_TIER_EGRESS = {
    "aws_lambda": 100,      # 100 GB/month free
    "aws_ec2": 100,         # 100 GB/month free
    "google_cloud": 100,    # 100 GB/month free
    "azure": 100,           # 100 GB/month free
    "oci": 10 * 1024,       # 10 TB/month free
    "sakura_cloud": float('inf')  # Unlimited free
}
```

### Egress Calculation Algorithm

**Data Transfer Cost Calculation**
```python
def calculate_egress_cost(config: EgressConfig) -> EgressResult:
    """Calculate egress costs with free tier and internet ratio"""
    provider = config.provider
    total_transfer_gb = config.total_transfer_gb
    internet_ratio = config.internet_transfer_ratio / 100.0  # Convert to decimal
    
    # Calculate internet-bound traffic only
    internet_transfer_gb = total_transfer_gb * internet_ratio
    
    # Apply free tier
    free_tier_gb = FREE_TIER_EGRESS.get(provider, 0)
    billable_gb = max(0, internet_transfer_gb - free_tier_gb)
    
    # Calculate cost
    rate_per_gb = EGRESS_RATES[provider]
    egress_cost_usd = billable_gb * rate_per_gb
    egress_cost_jpy = egress_cost_usd * config.exchange_rate
    
    return EgressResult(
        provider=provider,
        total_transfer_gb=total_transfer_gb,
        internet_transfer_gb=internet_transfer_gb,
        billable_gb=billable_gb,
        free_tier_gb=min(internet_transfer_gb, free_tier_gb),
        cost_usd=egress_cost_usd,
        cost_jpy=egress_cost_jpy,
        rate_per_gb=rate_per_gb
    )
```

### Internet Transfer Ratio (PBI10)

**Transfer Ratio Implementation**
```python
def apply_internet_transfer_ratio(total_egress_gb: float, ratio_percent: float) -> float:
    """Apply internet transfer ratio to total egress"""
    # ratio_percent: 0-100 representing percentage to internet
    # 0% = fully private network (no internet egress charges)
    # 100% = all traffic goes to internet (full egress charges)
    
    if ratio_percent < 0 or ratio_percent > 100:
        raise ValueError("Internet transfer ratio must be between 0 and 100")
    
    internet_ratio = ratio_percent / 100.0
    return total_egress_gb * internet_ratio
```

## Break-Even Point Analysis

### Break-Even Calculation Algorithm

**Lambda vs VM Break-Even Point**
```python
def calculate_break_even_point(lambda_config: LambdaConfig, vm_config: VMConfig) -> BreakEvenResult:
    """Calculate execution frequency where Lambda and VM costs are equal"""
    
    # VM costs are fixed monthly regardless of execution frequency
    vm_monthly_cost = calculate_vm_cost(vm_config).monthly_cost_usd
    
    # Lambda costs scale with execution frequency
    # We need to solve: lambda_cost(x) = vm_cost
    # where x = monthly executions
    
    def lambda_cost_function(executions: int) -> float:
        config = LambdaConfig(
            memory_mb=lambda_config.memory_mb,
            execution_time_seconds=lambda_config.execution_time_seconds,
            monthly_executions=executions,
            include_free_tier=lambda_config.include_free_tier,
            egress_per_request_kb=lambda_config.egress_per_request_kb,
            internet_transfer_ratio=lambda_config.internet_transfer_ratio
        )
        return calculate_lambda_cost(config).total_cost_usd
    
    # Binary search for break-even point
    low, high = 1, 100_000_000  # 1 to 100M executions
    tolerance = 0.01  # $0.01 tolerance
    
    while high - low > 1:
        mid = (low + high) // 2
        lambda_cost = lambda_cost_function(mid)
        
        if abs(lambda_cost - vm_monthly_cost) < tolerance:
            break
        elif lambda_cost < vm_monthly_cost:
            low = mid
        else:
            high = mid
    
    break_even_executions = (low + high) // 2
    break_even_per_second = break_even_executions / (30 * 24 * 3600)  # Monthly to per-second
    
    return BreakEvenResult(
        executions_per_month=break_even_executions,
        executions_per_second=break_even_per_second,
        lambda_cost=lambda_cost_function(break_even_executions),
        vm_cost=vm_monthly_cost,
        cost_difference=abs(lambda_cost_function(break_even_executions) - vm_monthly_cost)
    )
```

### Cost Comparison Range Analysis

**Execution Range Analysis**
```python
def generate_cost_comparison_data(lambda_config: LambdaConfig, vm_configs: List[VMConfig], 
                                num_points: int = 50) -> List[ComparisonDataPoint]:
    """Generate cost comparison data across execution range"""
    
    # Logarithmic scale from 1K to 100M executions
    min_executions = 1_000
    max_executions = 100_000_000
    
    execution_points = []
    for i in range(num_points):
        # Logarithmic distribution
        log_min = math.log10(min_executions)
        log_max = math.log10(max_executions)
        log_value = log_min + (log_max - log_min) * i / (num_points - 1)
        execution_points.append(int(10 ** log_value))
    
    comparison_data = []
    for executions in execution_points:
        # Calculate Lambda cost for this execution level
        lambda_config_point = lambda_config._replace(monthly_executions=executions)
        lambda_result = calculate_lambda_cost(lambda_config_point)
        
        # Calculate VM costs (fixed regardless of executions)
        vm_costs = {}
        for vm_config in vm_configs:
            vm_result = calculate_vm_cost(vm_config)
            vm_costs[f"{vm_config.provider}_{vm_config.instance_type}"] = vm_result.monthly_cost_usd
        
        comparison_data.append(ComparisonDataPoint(
            executions_per_month=executions,
            executions_per_second=executions / (30 * 24 * 3600),
            lambda_cost_usd=lambda_result.total_cost_usd,
            vm_costs_usd=vm_costs,
            break_even_flags=calculate_break_even_flags(lambda_result.total_cost_usd, vm_costs)
        ))
    
    return comparison_data
```

## Currency Conversion

### Exchange Rate Handling

**USD ↔ JPY Conversion**
```python
def convert_currency(amount_usd: float, exchange_rate: float, target_currency: str = "JPY") -> float:
    """Convert USD to JPY or vice versa"""
    if target_currency.upper() == "JPY":
        return amount_usd * exchange_rate
    elif target_currency.upper() == "USD":
        return amount_usd / exchange_rate
    else:
        raise ValueError(f"Unsupported currency: {target_currency}")

def validate_exchange_rate(rate: float) -> bool:
    """Validate exchange rate is within reasonable bounds"""
    MIN_RATE, MAX_RATE = 50.0, 300.0  # Historical JPY/USD range
    return MIN_RATE <= rate <= MAX_RATE
```

## Algorithm Validation

### Test Coverage

**Unit Test Coverage**
- **Lambda Calculator**: 39 test cases covering all pricing scenarios
- **VM Calculator**: 67 test cases across all providers and instance types
- **Egress Calculator**: 31 test cases covering all provider rates and free tiers
- **Break-Even Analysis**: 15 test cases covering edge cases and precision

**Mathematical Precision**
- **Float comparison tolerance**: `pytest.approx(rel=1e-3)` for financial calculations
- **Free tier boundary testing**: Exact calculations at tier limits
- **Currency conversion precision**: Proper rounding for display purposes

**Performance Requirements**
- **API response time**: <100ms for standard calculations
- **Bulk calculations**: <500ms for 50-point comparison data
- **Memory efficiency**: O(1) space complexity for cost calculations

## Conclusion

The cost calculation algorithms provide **accurate, comprehensive cost analysis** across multiple cloud providers with:

1. **Precise financial calculations** with proper free tier handling
2. **Multi-provider support** with provider-specific pricing and features
3. **Comprehensive egress cost modeling** with internet transfer ratios
4. **Accurate break-even analysis** using optimized search algorithms
5. **Production-ready performance** with <100ms response times
6. **Extensive test coverage** ensuring mathematical accuracy

The algorithms support real-world cost optimization decisions with enterprise-grade accuracy and reliability.