# API Reference

## Base URL

```
http://localhost:5001/api/v1/calculator
```

## Authentication

No authentication required. All endpoints are publicly accessible.

## Response Format
All responses follow this structure:
```json
{
  "success": boolean,
  "data": object,     // Present on success
  "error": string     // Present on error
}
```

## Endpoint Details

### Calculate Lambda Costs

**Endpoint:** `POST /lambda`

**Description:** Calculate AWS Lambda costs based on configuration parameters.

**Request Body:**
```json
{
  "memory_mb": 512,
  "execution_time_seconds": 10,
  "monthly_executions": 1000000,
  "include_free_tier": true
}
```

**Parameters:**
- `memory_mb` (integer, required): Lambda memory size (128, 512, 1024, 2048)
- `execution_time_seconds` (integer, required): Execution duration in seconds
- `monthly_executions` (integer, required): Number of executions per month
- `include_free_tier` (boolean, optional): Include AWS free tier benefits (default: true)

**Response:**
```json
{
  "success": true,
  "data": {
    "request_charges": 0.0,
    "compute_charges": 8.33,
    "total_cost": 8.33,
    "gb_seconds": 5000000,
    "configuration": {
      "memory_mb": 512,
      "execution_time_seconds": 10,
      "monthly_executions": 1000000,
      "include_free_tier": true
    }
  }
}
```

### Calculate VM Costs

**Endpoint:** `POST /vm`

**Description:** Calculate VM costs for AWS EC2, Sakura Cloud, or Google Cloud Compute Engine instances.

**Request Body:**
```json
{
  "provider": "aws_ec2",
  "instance_type": "t3.small",
  "region": "ap-northeast-1"
}
```

**Parameters:**
- `provider` (string, required): Cloud provider ("aws_ec2" or "sakura_cloud")
- `instance_type` (string, required): Instance type identifier
- `region` (string, optional): AWS region (default: "ap-northeast-1")

**Response (EC2):**
```json
{
  "success": true,
  "data": {
    "provider": "aws_ec2",
    "instance_type": "t3.small",
    "hourly_cost_usd": 0.0272,
    "monthly_cost_usd": 19.856,
    "specs": {
      "vcpu": 2,
      "memory_gb": 2
    },
    "configuration": {
      "provider": "aws_ec2",
      "instance_type": "t3.small",
      "region": "ap-northeast-1"
    }
  }
}
```

**Response (Sakura Cloud):**
```json
{
  "success": true,
  "data": {
    "provider": "sakura_cloud",
    "instance_type": "2core_4gb",
    "monthly_cost_jpy": 4180,
    "specs": {
      "vcpu": 2,
      "memory_gb": 4,
      "storage_gb": 20
    },
    "configuration": {
      "provider": "sakura_cloud",
      "instance_type": "2core_4gb",
      "region": "tokyo"
    }
  }
}
```

### Generate Cost Comparison

**Endpoint:** `POST /comparison`

**Description:** Generate comprehensive cost comparison between Lambda and VMs across execution ranges.

**Request Body:**
```json
{
  "lambda_config": {
    "memory_mb": 512,
    "execution_time_seconds": 10,
    "include_free_tier": true
  },
  "vm_configs": [
    {
      "provider": "aws_ec2",
      "instance_type": "t3.small"
    },
    {
      "provider": "sakura_cloud",
      "instance_type": "2core_4gb"
    }
  ],
  "execution_range": {
    "min": 0,
    "max": 10000000,
    "steps": 50
  }
}
```

**Parameters:**
- `lambda_config` (object, required): Lambda configuration
- `vm_configs` (array, required): Array of VM configurations to compare
- `execution_range` (object, optional): Execution range settings
  - `min` (integer): Minimum executions (default: 0)
  - `max` (integer): Maximum executions (default: 10,000,000)
  - `steps` (integer): Number of data points (default: 50)

**Response:**
```json
{
  "success": true,
  "data": {
    "comparison_data": [
      {
        "executions_per_month": 0,
        "lambda_cost_usd": 0.0,
        "vm_costs": {
          "aws_ec2_t3_small": 19.856,
          "sakura_cloud_2core_4gb": 27.87
        }
      },
      {
        "executions_per_month": 204081,
        "lambda_cost_usd": 1.70,
        "vm_costs": {
          "aws_ec2_t3_small": 19.856,
          "sakura_cloud_2core_4gb": 27.87
        }
      }
    ],
    "break_even_points": [
      {
        "vm_provider": "aws_ec2",
        "vm_instance": "t3_small",
        "executions_per_month": 2380952,
        "executions_per_second": 0.92
      }
    ],
    "lambda_configuration": {
      "memory_mb": 512,
      "execution_time_seconds": 10,
      "include_free_tier": true
    },
    "vm_configurations": [
      {
        "provider": "aws_ec2",
        "instance_type": "t3.small"
      }
    ]
  }
}
```

### Get Available Instances

**Endpoint:** `GET /instances`

**Description:** Get available instance types for all or specific providers.

**Query Parameters:**
- `provider` (string, optional): Filter by provider ("aws_ec2" or "sakura_cloud")

**Response:**
```json
{
  "success": true,
  "data": {
    "aws_ec2": {
      "t3.micro": {
        "hourly_cost_usd": 0.0136,
        "specs": {
          "vcpu": 2,
          "memory_gb": 1
        }
      },
      "t3.small": {
        "hourly_cost_usd": 0.0272,
        "specs": {
          "vcpu": 2,
          "memory_gb": 2
        }
      }
    },
    "sakura_cloud": {
      "2core_4gb": {
        "monthly_cost_jpy": 4180,
        "specs": {
          "vcpu": 2,
          "memory_gb": 4,
          "storage_gb": 20
        }
      }
    }
  }
}
```

### Get VM Recommendations

**Endpoint:** `POST /recommend`

**Description:** Get VM instance recommendations based on Lambda memory configuration.

**Request Body:**
```json
{
  "lambda_memory_mb": 512
}
```

**Parameters:**
- `lambda_memory_mb` (integer, required): Lambda memory size in MB

**Response:**
```json
{
  "success": true,
  "data": {
    "aws_ec2": [
      {
        "instance_type": "t3.micro",
        "memory_ratio": 2.0,
        "provider": "aws_ec2",
        "hourly_cost_usd": 0.0136,
        "monthly_cost_usd": 9.928,
        "specs": {
          "vcpu": 2,
          "memory_gb": 1
        }
      }
    ],
    "sakura_cloud": [
      {
        "instance_type": "2core_4gb",
        "memory_ratio": 8.0,
        "provider": "sakura_cloud",
        "monthly_cost_jpy": 4180,
        "specs": {
          "vcpu": 2,
          "memory_gb": 4,
          "storage_gb": 20
        }
      }
    ]
  }
}
```

### Convert Currency

**Endpoint:** `POST /currency/convert`

**Description:** Convert between USD and JPY currencies.

**Request Body:**
```json
{
  "amount": 19.58,
  "from_currency": "USD",
  "to_currency": "JPY",
  "exchange_rate": 150
}
```

**Parameters:**
- `amount` (number, required): Amount to convert
- `from_currency` (string, optional): Source currency (default: "USD")
- `to_currency` (string, optional): Target currency (default: "JPY")
- `exchange_rate` (number, optional): Exchange rate (default: 150.0)

**Response:**
```json
{
  "success": true,
  "data": {
    "original_amount": 19.58,
    "converted_amount": 2937.0,
    "from_currency": "USD",
    "to_currency": "JPY",
    "exchange_rate": 150
  }
}
```

## Error Responses

### 400 Bad Request
Missing required fields or invalid input data:
```json
{
  "success": false,
  "error": "Missing required fields: ['memory_mb', 'execution_time_seconds']"
}
```

### 500 Internal Server Error
Server-side calculation or system errors:
```json
{
  "success": false,
  "error": "Internal server error: calculation failed"
}
```

## Usage Examples

### JavaScript/Fetch
```javascript
// Calculate Lambda cost
const response = await fetch('/api/v1/calculator/lambda', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    memory_mb: 512,
    execution_time_seconds: 10,
    monthly_executions: 1000000,
    include_free_tier: true
  })
});

const result = await response.json();
if (result.success) {
  console.log('Total cost:', result.data.total_cost);
}
```

### Python/Requests
```python
import requests

# Generate cost comparison
response = requests.post('http://localhost:5000/api/v1/calculator/comparison', json={
  'lambda_config': {
    'memory_mb': 512,
    'execution_time_seconds': 10,
    'include_free_tier': True
  },
  'vm_configs': [
    {'provider': 'aws_ec2', 'instance_type': 't3.small'}
  ]
})

if response.json()['success']:
  data = response.json()['data']
  print(f"Break-even points: {data['break_even_points']}")
```

### cURL
```bash
# Get available instances
curl -X GET http://localhost:5000/api/v1/calculator/instances

# Calculate VM cost
curl -X POST http://localhost:5000/api/v1/calculator/vm \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "aws_ec2",
    "instance_type": "t3.small"
  }'
```