# API Endpoints Reference

## Base URL
- **Development**: `http://localhost:5001/api/v1/calculator`
- **Production**: Configure based on deployment environment

## Authentication
- **Current**: No authentication required
- **Future**: API key authentication planned for external integrations

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": {
    // Endpoint-specific data
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message description",
  "details": {
    // Optional error details
  }
}
```

## Endpoints

### 1. Calculate Lambda Cost

**Endpoint**: `POST /lambda`

**Description**: Calculate AWS Lambda costs based on configuration parameters.

**Request Body**:
```json
{
  "memory_mb": 512,
  "execution_time_seconds": 5,
  "monthly_executions": 1000000,
  "include_free_tier": true,
  "egress_per_request_kb": 100.0,
  "internet_transfer_ratio": 100.0
}
```

**Parameters**:
- `memory_mb` (integer, required): Lambda memory allocation (128, 512, 1024, 2048)
- `execution_time_seconds` (integer, required): Function execution time (1-60)
- `monthly_executions` (integer, required): Number of executions per month
- `include_free_tier` (boolean, required): Whether to apply AWS free tier
- `egress_per_request_kb` (float, optional): KB transferred per request (default: 0)
- `internet_transfer_ratio` (float, optional): Percentage of traffic to internet (default: 100)

**Response**:
```json
{
  "success": true,
  "data": {
    "total_cost_usd": 8.34,
    "request_cost_usd": 0.0,
    "compute_cost_usd": 6.67,
    "egress_cost_usd": 1.67,
    "free_tier_applied": {
      "requests_covered": 1000000,
      "compute_covered": 2500.0
    },
    "configuration": {
      "memory_mb": 512,
      "execution_time_seconds": 5,
      "monthly_executions": 1000000,
      "include_free_tier": true,
      "egress_per_request_kb": 100.0,
      "internet_transfer_ratio": 100.0
    }
  }
}
```

### 2. Calculate VM Cost

**Endpoint**: `POST /vm`

**Description**: Calculate virtual machine costs for specified provider and instance type.

**Request Body**:
```json
{
  "provider": "aws_ec2",
  "instance_type": "t3.small",
  "region": "ap-northeast-1",
  "monthly_executions": 1000000,
  "egress_per_request_kb": 100.0,
  "include_egress_free_tier": true,
  "internet_transfer_ratio": 100.0
}
```

**Parameters**:
- `provider` (string, required): Cloud provider ("aws_ec2", "google_cloud", "azure", "oci", "sakura_cloud")
- `instance_type` (string, required): Instance type identifier
- `region` (string, optional): Target region (default: "ap-northeast-1")
- `monthly_executions` (integer, optional): Executions for egress calculation (default: 0)
- `egress_per_request_kb` (float, optional): KB transferred per request (default: 0)
- `include_egress_free_tier` (boolean, optional): Apply egress free tier (default: true)
- `internet_transfer_ratio` (float, optional): Percentage of traffic to internet (default: 100)

**Response**:
```json
{
  "success": true,
  "data": {
    "provider": "aws_ec2",
    "instance_type": "t3.small",
    "hourly_cost_usd": 0.0272,
    "monthly_cost_usd": 19.856,
    "egress_cost_usd": 1.67,
    "total_monthly_cost_usd": 21.526,
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

### 3. Cost Comparison

**Endpoint**: `POST /comparison`

**Description**: Compare Lambda costs against multiple VM configurations with break-even analysis.

**Request Body**:
```json
{
  "lambda_config": {
    "memory_mb": 512,
    "execution_time_seconds": 5,
    "monthly_executions": 1000000,
    "include_free_tier": true,
    "egress_per_request_kb": 100.0,
    "internet_transfer_ratio": 100.0
  },
  "vm_configs": [
    {
      "provider": "aws_ec2",
      "instance_type": "t3.small",
      "region": "ap-northeast-1"
    },
    {
      "provider": "google_cloud",
      "instance_type": "e2-medium",
      "region": "asia-northeast1"
    }
  ],
  "currency": "USD",
  "exchange_rate": 150.0
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "lambda_configuration": {
      "memory_mb": 512,
      "execution_time_seconds": 5,
      "monthly_executions": 1000000,
      "include_free_tier": true,
      "egress_per_request_kb": 100.0,
      "internet_transfer_ratio": 100.0
    },
    "vm_configurations": [
      {
        "provider": "aws_ec2",
        "instance_type": "t3.small",
        "region": "ap-northeast-1"
      }
    ],
    "break_even_points": [
      {
        "vm_provider": "aws_ec2",
        "vm_instance": "t3.small",
        "executions_per_month": 816326,
        "executions_per_second": 0.315
      }
    ],
    "comparison_data": [
      {
        "executions_per_month": 0,
        "lambda_cost_usd": 0.0,
        "vm_costs": {
          "aws_ec2_t3.small": 21.526
        }
      },
      // ... more data points
    ]
  }
}
```

### 4. Export CSV

**Endpoint**: `POST /export/csv`

**Description**: Export detailed cost comparison data as CSV format.

**Request Body**: Same as comparison endpoint

**Response**:
```json
{
  "success": true,
  "data": {
    "csv_data": "Executions per Month,Lambda Cost (USD),AWS EC2 t3.small (USD),Google Cloud e2-medium (USD)\n0,0.00,21.53,24.46\n...",
    "filename": "cost_comparison_2025_01_12.csv"
  }
}
```

### 5. Instance Recommendations

**Endpoint**: `POST /recommend`

**Description**: Get VM instance recommendations based on Lambda memory configuration.

**Request Body**:
```json
{
  "lambda_memory_mb": 512
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "lambda_memory_mb": 512,
    "recommendations": {
      "aws_ec2": [
        {
          "instance_type": "t3.micro",
          "memory_ratio": 2.0,
          "monthly_cost_usd": 9.93,
          "specs": {
            "vcpu": 2,
            "memory_gb": 1
          }
        }
      ],
      "google_cloud": [
        {
          "instance_type": "e2-micro",
          "memory_ratio": 2.0,
          "monthly_cost_usd": 6.13,
          "specs": {
            "vcpu": 0.25,
            "memory_gb": 1
          }
        }
      ]
    }
  }
}
```

### 6. Currency Conversion

**Endpoint**: `POST /convert`

**Description**: Convert amounts between USD and JPY.

**Request Body**:
```json
{
  "amount": 100.0,
  "from_currency": "USD",
  "to_currency": "JPY",
  "exchange_rate": 150.0
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "original_amount": 100.0,
    "converted_amount": 15000.0,
    "from_currency": "USD",
    "to_currency": "JPY",
    "exchange_rate": 150.0
  }
}
```

### 7. Health Check

**Endpoint**: `GET /health`

**Description**: Service health check endpoint.

**Response**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-01-12T10:30:00Z"
}
```

## Error Handling

### Common Error Codes

- **400 Bad Request**: Invalid input parameters
- **422 Unprocessable Entity**: Valid JSON but invalid business logic
- **500 Internal Server Error**: Server processing error

### Validation Errors

**Invalid Memory Size**:
```json
{
  "success": false,
  "error": "Invalid memory size. Must be one of: 128, 512, 1024, 2048"
}
```

**Invalid Provider**:
```json
{
  "success": false,
  "error": "Invalid provider. Must be one of: aws_ec2, google_cloud, azure, oci, sakura_cloud"
}
```

**Invalid Transfer Ratio**:
```json
{
  "success": false,
  "error": "転送割合は0-100の範囲で入力してください"
}
```

## Rate Limiting

- **Current**: No rate limiting implemented
- **Future**: 1000 requests/hour per IP planned
- **Caching**: Identical requests cached for 5 minutes

## Usage Examples

### Calculate Break-even for Small Workload

```bash
curl -X POST http://localhost:5001/api/v1/calculator/comparison \
  -H "Content-Type: application/json" \
  -d '{
    "lambda_config": {
      "memory_mb": 512,
      "execution_time_seconds": 5,
      "monthly_executions": 100000,
      "include_free_tier": true,
      "egress_per_request_kb": 50
    },
    "vm_configs": [
      {
        "provider": "aws_ec2",
        "instance_type": "t3.micro"
      }
    ],
    "currency": "USD"
  }'
```

### Get Recommendations for High-Memory Lambda

```bash
curl -X POST http://localhost:5001/api/v1/calculator/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "lambda_memory_mb": 2048
  }'
```

### Calculate OCI Always Free Cost

```bash
curl -X POST http://localhost:5001/api/v1/calculator/vm \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "oci",
    "instance_type": "VM.Standard.E2.1.Micro_Free",
    "monthly_executions": 1000000,
    "egress_per_request_kb": 100
  }'
```

## Integration Notes

### Frontend Integration
- All endpoints support CORS for browser-based requests
- JSON content-type required for POST requests
- Response data suitable for Chart.js visualization

### Error Handling Best Practices
- Always check `success` field in response
- Display user-friendly error messages from `error` field
- Log detailed error information from `details` field for debugging

### Performance Considerations
- Comparison endpoint can handle up to 10M executions in calculation range
- CSV export limited to reasonable data sizes (< 1MB)
- Concurrent requests supported with thread-safe calculations