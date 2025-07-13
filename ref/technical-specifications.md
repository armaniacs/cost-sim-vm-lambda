# Technical Specifications

## Cost Calculation Algorithms

### AWS Lambda Pricing Model

#### Configuration Parameters
- **Memory Size**: 128MB, 512MB, 1024MB, 2048MB
- **Execution Time**: 1 second, 10 seconds, 30 seconds, 60 seconds  
- **Execution Frequency**: 100K to 1B+ executions per month
- **Free Tier**: Optional inclusion in calculations

#### Pricing Constants (Tokyo Region ap-northeast-1)
```python
REQUEST_PRICE_PER_MILLION = 0.20  # USD per 1M requests
COMPUTE_PRICE_PER_GB_SECOND = 0.0000166667  # USD per GB-second
FREE_TIER_REQUESTS = 1_000_000  # 1M requests per month
FREE_TIER_GB_SECONDS = 400_000  # 400K GB-seconds per month
```

#### Request Charges Calculation
```python
def calculate_request_charges(monthly_executions, include_free_tier):
    if include_free_tier:
        billable_requests = max(0, monthly_executions - FREE_TIER_REQUESTS)
    else:
        billable_requests = monthly_executions
    
    return (billable_requests * REQUEST_PRICE_PER_MILLION) / 1_000_000
```

#### Compute Charges Calculation
```python
def calculate_compute_charges(memory_mb, execution_time_seconds, monthly_executions, include_free_tier):
    # Convert memory to GB
    gb_memory = memory_mb / 1024
    
    # Calculate total GB-seconds
    total_gb_seconds = gb_memory * execution_time_seconds * monthly_executions
    
    # Apply free tier if enabled
    if include_free_tier:
        billable_gb_seconds = max(0, total_gb_seconds - FREE_TIER_GB_SECONDS)
    else:
        billable_gb_seconds = total_gb_seconds
    
    return billable_gb_seconds * COMPUTE_PRICE_PER_GB_SECOND
```

#### Total Lambda Cost
```python
total_cost = request_charges + compute_charges
```

### Virtual Machine Pricing

#### AWS EC2 Instances (Tokyo Region)
All prices in USD per hour for on-demand instances:

| Instance Type | vCPU | Memory (GB) | Hourly Cost | Monthly Cost |
|---------------|------|-------------|-------------|--------------|
| t3.micro      | 2    | 1           | $0.0136     | $9.79        |
| t3.small      | 2    | 2           | $0.0272     | $19.58       |
| t3.medium     | 2    | 4           | $0.0544     | $39.17       |
| t3.large      | 2    | 8           | $0.1088     | $79.42       |
| c5.large      | 2    | 4           | $0.096      | $69.12       |
| c5.xlarge     | 4    | 8           | $0.192      | $140.16      |

**Monthly Cost Calculation**: `hourly_cost * 730 hours`

#### Sakura Cloud Instances
All prices in JPY per month:

| Instance Type | vCPU | Memory (GB) | Monthly Cost (JPY) |
|---------------|------|-------------|-------------------|
| 1core_1gb     | 1    | 1           | ¥1,595            |
| 2core_2gb     | 2    | 2           | ¥3,190            |
| 2core_4gb     | 2    | 4           | ¥4,180            |
| 4core_8gb     | 4    | 8           | ¥7,370            |
| 6core_12gb    | 6    | 12          | ¥11,560           |

### Currency Conversion

#### Exchange Rate Configuration
```python
DEFAULT_EXCHANGE_RATE = 150.0  # JPY/USD
MIN_EXCHANGE_RATE = 50.0
MAX_EXCHANGE_RATE = 300.0
```

#### Conversion Functions
```python
def usd_to_jpy(usd_amount, exchange_rate):
    return usd_amount * exchange_rate

def jpy_to_usd(jpy_amount, exchange_rate):
    return jpy_amount / exchange_rate
```

## Break-even Point Analysis

### Calculation Algorithm
Break-even points occur where Lambda total cost equals VM monthly cost:

```python
def find_break_even_point(lambda_config, vm_monthly_cost):
    for execution_count in execution_range:
        lambda_cost = calculate_lambda_cost(lambda_config, execution_count)
        if lambda_cost >= vm_monthly_cost:
            return {
                'executions_per_month': execution_count,
                'executions_per_second': execution_count / (30 * 24 * 3600),
                'cost': lambda_cost
            }
    return None
```

### Execution Rate Conversion
```python
SECONDS_PER_MONTH = 30 * 24 * 3600  # 2,592,000 seconds

executions_per_second = executions_per_month / SECONDS_PER_MONTH
executions_per_month = executions_per_second * SECONDS_PER_MONTH
```

## Data Structures

### Lambda Configuration
```python
@dataclass
class LambdaConfig:
    memory_mb: int                    # 128, 512, 1024, 2048
    execution_time_seconds: int       # 1, 10, 30, 60
    monthly_executions: int           # Variable execution count
    include_free_tier: bool = True    # Whether to include free tier
```

### VM Configuration
```python
@dataclass
class VMConfig:
    provider: str                     # "aws_ec2" or "sakura_cloud"
    instance_type: str                # Provider-specific instance ID
    region: str = "ap-northeast-1"    # Default to Tokyo
```

### Cost Calculation Response
```python
{
    "success": True,
    "data": {
        "comparison_data": [
            {
                "executions_per_month": 1000000,
                "lambda_cost_usd": 23.45,
                "vm_costs": {
                    "aws_ec2_t3.small": 19.58,
                    "sakura_cloud_2core_4gb": 27.87
                }
            }
        ],
        "break_even_points": [
            {
                "vm_provider": "aws_ec2",
                "vm_instance": "t3.small",
                "executions_per_month": 850000,
                "executions_per_second": 0.328
            }
        ]
    }
}
```

## Execution Range Generation

### Default Parameters
```python
EXECUTION_RANGE = {
    "min": 1_000_000,      # 1M executions/month
    "max": 6_000_000,      # 6M executions/month  
    "steps": 50            # Number of data points
}
```

### Data Point Generation
```python
def generate_execution_points(min_exec, max_exec, steps):
    if steps <= 1:
        return [min_exec, max_exec]
    
    step_size = (max_exec - min_exec) / (steps - 1)
    return [int(min_exec + i * step_size) for i in range(steps)]
```

## Validation Rules

### Input Validation
```python
# Lambda memory validation
VALID_MEMORY_SIZES = [128, 512, 1024, 2048]  # MB

# Lambda execution time validation  
VALID_EXECUTION_TIMES = [1, 10, 30, 60]  # seconds

# Exchange rate validation
MIN_EXCHANGE_RATE = 50.0   # JPY/USD
MAX_EXCHANGE_RATE = 300.0  # JPY/USD

# Execution frequency validation
MIN_MONTHLY_EXECUTIONS = 0
MAX_MONTHLY_EXECUTIONS = 1_000_000_000  # 1B executions
```

### VM Instance Validation
```python
VALID_AWS_INSTANCES = [
    "t3.micro", "t3.small", "t3.medium", "t3.large",
    "c5.large", "c5.xlarge"
]

VALID_SAKURA_INSTANCES = [
    "1core_1gb", "2core_2gb", "2core_4gb", 
    "4core_8gb", "6core_12gb"
]
```

## Chart Visualization Specifications

### Execution Rate Reference Lines
Yellow dashed lines at execution frequencies:
```python
EXECUTION_RATES = [
    {"per_second": 0.001, "label": "0.001/秒"},
    {"per_second": 0.01, "label": "0.01/秒"},
    {"per_second": 0.1, "label": "0.1/秒"},
    {"per_second": 1, "label": "1/秒", "emphasis": True},
    {"per_second": 2, "label": "2/秒", "emphasis": True},
    {"per_second": 5, "label": "5/秒", "emphasis": True},
    {"per_second": 10, "label": "10/秒", "major": True},
    {"per_second": 100, "label": "100/秒", "major": True}
]
```

### Break-even Point Markers
Purple dashed lines with:
- Vertical line from top to bottom of chart
- Downward arrow at X-axis
- Label showing executions per second and provider

### Chart Configuration
```javascript
{
    type: 'line',
    scales: {
        x: {
            type: 'logarithmic',
            min: 1000000,      // 1M executions
            max: 6000000,      // 6M executions
            title: 'Monthly Executions'
        },
        y: {
            beginAtZero: true,
            title: 'Monthly Cost ($)'
        }
    }
}
```

## Performance Specifications

### API Response Times
- **Target**: <100ms for all calculations
- **Maximum**: <500ms for complex scenarios
- **Timeout**: 30 seconds for client requests

### Data Processing Limits
- **Maximum Execution Points**: 100 per calculation
- **Maximum VM Configurations**: 10 per comparison
- **CSV Export Size**: Up to 10MB

### Browser Compatibility
- **Chrome**: 90+
- **Firefox**: 88+
- **Safari**: 14+
- **Edge**: 90+

---

**Last Updated**: January 2025  
**Version**: 1.0.0  
**Pricing Data**: Current as of January 2025