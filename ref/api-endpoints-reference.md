# API Endpoints Reference

Complete documentation for the Cost Simulator REST API endpoints with comprehensive technical details for integration.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [1. Lambda Cost Calculation](#1-lambda-cost-calculation)
   - [2. VM Cost Calculation](#2-vm-cost-calculation)
   - [3. Cost Comparison](#3-cost-comparison)
   - [4. CSV Export](#4-csv-export)
   - [5. Available Instances](#5-available-instances)
   - [6. Instance Recommendations](#6-instance-recommendations)
   - [7. Currency Conversion](#7-currency-conversion)
   - [8. Serverless Cost Calculation](#8-serverless-cost-calculation)
   - [9. Serverless Providers Info](#9-serverless-providers-info)

## Overview

The Cost Simulator API provides REST endpoints for calculating and comparing costs between AWS Lambda and various virtual machine providers. All endpoints return JSON responses and support comprehensive cost analysis including egress charges, currency conversion, and free tier calculations.

**Base URL**: `http://localhost:5000/api/calculator`

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Error Handling

All endpoints follow a consistent error response format:

```json
{
  "error": "Error description message"
}
```

**HTTP Status Codes**:
- `200`: Success
- `400`: Bad Request (validation errors, missing fields)
- `500`: Internal Server Error

## Endpoints

### 1. Lambda Cost Calculation

Calculate AWS Lambda costs with comprehensive options including egress charges and free tier analysis.

**Endpoint**: `POST /lambda`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `memory_mb` | integer | Yes | Lambda memory allocation (128-10240 MB) |
| `execution_time_seconds` | integer | Yes | Function execution time in seconds |
| `monthly_executions` | integer | Yes | Number of monthly executions |
| `include_free_tier` | boolean | No | Include AWS free tier benefits (default: true) |
| `egress_per_request_kb` | float | No | Data transferred per request in KB (default: 0.0) |
| `internet_transfer_ratio` | float | No | Percentage of traffic to internet 0-100 (default: 100.0) |
| `custom_egress_rates` | object | No | Custom egress pricing rates |
| `include_egress_free_tier` | boolean | No | Include egress free tier (default: true) |

#### Cost Calculation Formulas

**Request Charges**:
```
billable_requests = max(0, monthly_executions - 1,000,000) // if free tier enabled
request_cost = (billable_requests / 1,000,000) * $0.20
```

**Compute Charges**:
```
gb_seconds = (memory_mb / 1024) * execution_time_seconds * monthly_executions
billable_gb_seconds = max(0, gb_seconds - 400,000) // if free tier enabled
compute_cost = billable_gb_seconds * $0.0000166667
```

**Egress Charges**:
```
total_egress_kb = monthly_executions * egress_per_request_kb
internet_egress_kb = total_egress_kb * (internet_transfer_ratio / 100)
egress_cost = calculated by EgressCalculator with tiered pricing
```

#### Example Request

```json
{
  "memory_mb": 512,
  "execution_time_seconds": 10,
  "monthly_executions": 1000000,
  "include_free_tier": true,
  "egress_per_request_kb": 50.0,
  "internet_transfer_ratio": 80.0
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "request_charges": 0.0,
    "compute_charges": 8.33,
    "egress_charges": 4.50,
    "total_cost": 12.83,
    "breakdown": {
      "requests_used": 1000000,
      "requests_free": 1000000,
      "gb_seconds_used": 5000,
      "gb_seconds_free": 400000,
      "egress_gb": 48.83
    }
  }
}
```

#### Parameter Validation

- `memory_mb`: Must be between 128-10240
- `execution_time_seconds`: Must be positive
- `monthly_executions`: Must be non-negative
- `egress_per_request_kb`: Must be >= 0
- `internet_transfer_ratio`: Must be 0-100

### 2. VM Cost Calculation

Calculate virtual machine costs for multiple cloud providers with egress cost support.

**Endpoint**: `POST /vm`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | Yes | Cloud provider: "aws_ec2", "sakura_cloud", "google_cloud", "azure", "oci" |
| `instance_type` | string | Yes | Instance type specific to provider |
| `region` | string | No | Region (default: "ap-northeast-1") |
| `monthly_executions` | integer | No | For egress calculation |
| `egress_per_request_kb` | float | No | Data transferred per request in KB |
| `internet_transfer_ratio` | float | No | Percentage of traffic to internet 0-100 |
| `custom_egress_rates` | object | No | Custom egress pricing rates |
| `include_egress_free_tier` | boolean | No | Include egress free tier (default: true) |

#### Supported Providers and Instance Types

**AWS EC2**:
- `t3.micro`, `t3.small`, `t3.medium`, `t3.large`
- `c5.large`, `c5.xlarge`

**Google Cloud**:
- `e2-micro`, `e2-small`, `e2-medium`
- `n2-standard-1`, `n2-standard-2`, `c2-standard-4`

**Azure**:
- `B1ls`, `B1s`, `B1ms`, `B2s`, `B2ms`
- `A1_Basic`, `D3`, `D4`

**Oracle Cloud (OCI)**:
- `VM.Standard.E2.1.Micro`, `VM.Standard.A1.Flex_1_6`
- `VM.Standard.E4.Flex_1_8`, `VM.Standard.E2.1.Micro_Free`

**Sakura Cloud**:
- `1core_1gb`, `2core_2gb`, `2core_4gb`
- `4core_8gb`, `6core_12gb`

#### Cost Calculation Formulas

**AWS EC2 / Google Cloud / Azure / OCI**:
```
monthly_cost_usd = hourly_rate * 730 // 730 hours per month
```

**Sakura Cloud**:
```
monthly_cost_jpy = fixed_monthly_rate
```

#### Example Request

```json
{
  "provider": "aws_ec2",
  "instance_type": "t3.small",
  "region": "ap-northeast-1",
  "monthly_executions": 1000000,
  "egress_per_request_kb": 30.0,
  "internet_transfer_ratio": 90.0
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "provider": "aws_ec2",
    "instance_type": "t3.small",
    "monthly_cost_usd": 19.86,
    "egress_cost_usd": 2.70,
    "total_monthly_cost_usd": 22.56,
    "specs": {
      "vcpu": 2,
      "memory_gb": 2
    },
    "egress_breakdown": {
      "total_transfer_gb": 29.30,
      "internet_transfer_gb": 26.37,
      "free_tier_applied": true
    }
  }
}
```

### 3. Cost Comparison

Generate comprehensive cost comparison between Lambda and multiple VM configurations across different execution volumes.

**Endpoint**: `POST /comparison`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lambda_config` | object | Yes | Lambda configuration object |
| `vm_configs` | array | Yes | Array of VM configuration objects |
| `execution_range` | object | No | Execution volume range configuration |
| `custom_egress_rates` | object | No | Custom egress pricing rates |
| `include_egress_free_tier` | boolean | No | Include egress free tier calculations |

#### Lambda Config Object

```json
{
  "memory_mb": 512,
  "execution_time_seconds": 10,
  "include_free_tier": true,
  "egress_per_request_kb": 25.0,
  "internet_transfer_ratio": 85.0
}
```

#### VM Config Object

```json
{
  "provider": "aws_ec2",
  "instance_type": "t3.small",
  "region": "ap-northeast-1"
}
```

#### Execution Range Object

```json
{
  "min": 0,
  "max": 10000000,
  "steps": 50
}
```

#### Example Request

```json
{
  "lambda_config": {
    "memory_mb": 512,
    "execution_time_seconds": 10,
    "include_free_tier": true,
    "egress_per_request_kb": 20.0,
    "internet_transfer_ratio": 80.0
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
    "max": 5000000,
    "steps": 25
  }
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "comparison_data": [
      {
        "executions_per_month": 0,
        "lambda_cost_usd": 0.0,
        "vm_costs": {
          "aws_ec2_t3.small": 19.86,
          "sakura_cloud_2core_4gb": 27.87
        }
      },
      {
        "executions_per_month": 208333,
        "lambda_cost_usd": 1.25,
        "vm_costs": {
          "aws_ec2_t3.small": 21.45,
          "sakura_cloud_2core_4gb": 29.12
        }
      }
    ],
    "break_even_points": [
      {
        "vm_provider": "aws_ec2",
        "vm_instance": "t3.small",
        "executions_per_month": 2500000,
        "executions_per_second": 0.96
      }
    ],
    "lambda_configuration": { /* lambda config */ },
    "vm_configurations": [ /* vm configs */ ]
  }
}
```

### 4. CSV Export

Export cost comparison data in CSV format with detailed breakdown of all cost components.

**Endpoint**: `POST /export_csv`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lambda_config` | object | Yes | Lambda configuration object |
| `vm_configs` | array | Yes | Array of VM configuration objects |
| `currency` | string | No | Output currency: "USD" or "JPY" (default: "USD") |
| `exchange_rate` | float | No | USD to JPY exchange rate (default: 150.0) |
| `custom_egress_rates` | object | No | Custom egress pricing rates |
| `include_egress_free_tier` | boolean | No | Include egress free tier |

#### Example Request

```json
{
  "lambda_config": {
    "memory_mb": 512,
    "execution_time_seconds": 10,
    "monthly_executions": 1000000,
    "include_free_tier": true,
    "egress_per_request_kb": 100,
    "internet_transfer_ratio": 75.0
  },
  "vm_configs": [
    {
      "provider": "aws_ec2",
      "instance_type": "t3.small"
    }
  ],
  "currency": "JPY",
  "exchange_rate": 150.0
}
```

#### Response Format

Returns a CSV file with the following structure:

```csv
provider,instance_type,lambda_execution_cost_usd,lambda_egress_cost_usd,lambda_total_cost_usd,vm_fixed_cost_usd,vm_egress_cost_usd,vm_total_cost_usd,lambda_execution_cost_jpy,lambda_egress_cost_jpy,lambda_total_cost_jpy,vm_fixed_cost_jpy,vm_egress_cost_jpy,vm_total_cost_jpy
aws_ec2,t3.small,8.3333,6.7500,15.0833,19.8600,5.6250,25.4850,1250.0,1012.5,2262.5,2979.0,843.8,3822.8
```

#### Response Headers

```
Content-Type: text/csv
Content-Disposition: attachment; filename=cost_comparison_with_egress.csv
```

### 5. Available Instances

Retrieve available instance types for cloud providers.

**Endpoint**: `GET /instances`

#### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | No | Specific provider to query |

#### Example Request

```
GET /instances?provider=aws_ec2
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "aws_ec2": [
      {
        "instance_type": "t3.micro",
        "vcpu": 2,
        "memory_gb": 1,
        "hourly_usd": 0.0136
      },
      {
        "instance_type": "t3.small",
        "vcpu": 2,
        "memory_gb": 2,
        "hourly_usd": 0.0272
      }
    ]
  }
}
```

#### All Providers Response

When no provider is specified, returns data for all providers:

```json
{
  "success": true,
  "data": {
    "aws_ec2": [ /* instances */ ],
    "sakura_cloud": [ /* instances */ ],
    "google_cloud": [ /* instances */ ],
    "azure": [ /* instances */ ],
    "oci": [ /* instances */ ]
  }
}
```

### 6. Instance Recommendations

Get VM instance recommendations based on Lambda memory configuration.

**Endpoint**: `POST /recommend`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `lambda_memory_mb` | integer | Yes | Lambda memory allocation in MB |

#### Recommendation Algorithm

The system recommends instances with memory capacity >= Lambda memory allocation, optimized for cost-effectiveness.

#### Example Request

```json
{
  "lambda_memory_mb": 512
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "provider": "aws_ec2",
        "instance_type": "t3.small",
        "memory_gb": 2,
        "vcpu": 2,
        "monthly_cost_usd": 19.86,
        "memory_efficiency": 0.25,
        "recommendation_score": 8.5
      },
      {
        "provider": "sakura_cloud",
        "instance_type": "2core_2gb",
        "memory_gb": 2,
        "vcpu": 2,
        "monthly_cost_jpy": 3190,
        "memory_efficiency": 0.25,
        "recommendation_score": 8.2
      }
    ]
  }
}
```

### 7. Currency Conversion

Convert between USD and JPY using specified exchange rates.

**Endpoint**: `POST /currency/convert`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `amount` | float | Yes | Amount to convert |
| `from_currency` | string | No | Source currency: "USD" or "JPY" (default: "USD") |
| `to_currency` | string | No | Target currency: "USD" or "JPY" (default: "JPY") |
| `exchange_rate` | float | No | USD to JPY exchange rate (default: 150.0) |

#### Conversion Formulas

**USD to JPY**:
```
jpy_amount = usd_amount * exchange_rate
```

**JPY to USD**:
```
usd_amount = jpy_amount / exchange_rate
```

#### Example Request

```json
{
  "amount": 19.58,
  "from_currency": "USD",
  "to_currency": "JPY",
  "exchange_rate": 150.0
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "original_amount": 19.58,
    "converted_amount": 2937.0,
    "from_currency": "USD",
    "to_currency": "JPY",
    "exchange_rate": 150.0
  }
}
```

### 8. Serverless Cost Calculation

Calculate costs for various serverless platforms including AWS Lambda, Google Cloud Functions/Cloud Run, Azure Functions, and Oracle Cloud Functions.

**Endpoint**: `POST /serverless`

#### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | Yes | Provider: "aws_lambda", "gcp_functions", "gcp_cloudrun", "azure_functions", "oci_functions" |
| `memory_mb` | integer | Yes | Memory allocation in MB |
| `execution_time_seconds` | float | Yes | Function execution time |
| `monthly_executions` | integer | Yes | Number of monthly executions |
| `include_free_tier` | boolean | No | Include free tier benefits (default: true) |
| `cpu_count` | float | No | CPU count for Cloud Run (required for gcp_cloudrun) |
| `egress_per_request_kb` | float | No | Data transferred per request in KB |
| `internet_transfer_ratio` | float | No | Percentage of traffic to internet 0-100 |
| `exchange_rate` | float | No | USD to JPY exchange rate (default: 150.0) |
| `include_ecosystem_benefits` | boolean | No | Include ecosystem integration benefits |
| `include_egress_free_tier` | boolean | No | Include egress free tier calculations |

#### Supported Providers

1. **AWS Lambda** (`aws_lambda`)
   - Request-based + GB-second pricing
   - 1M requests + 400K GB-seconds free tier

2. **Google Cloud Functions** (`gcp_functions`)
   - Request + GB-second + compute time pricing
   - 2M requests + 400K GB-seconds free tier

3. **Google Cloud Run** (`gcp_cloudrun`)
   - CPU + memory + request pricing
   - CPU count parameter required
   - 2M requests + 360K vCPU-seconds free tier

4. **Azure Functions** (`azure_functions`)
   - Request + GB-second pricing
   - 1M requests + 400K GB-seconds free tier

5. **Oracle Cloud Functions** (`oci_functions`)
   - Request + GB-second pricing
   - 2M requests + 400K GB-seconds free tier

#### Provider-Specific Cost Formulas

**AWS Lambda**:
```
request_cost = (requests / 1,000,000) * $0.20
compute_cost = gb_seconds * $0.0000166667
```

**Google Cloud Functions**:
```
request_cost = (requests / 1,000,000) * $0.40
memory_cost = gb_seconds * $0.0000025
cpu_cost = ghz_seconds * $0.00001
```

**Google Cloud Run**:
```
request_cost = (requests / 1,000,000) * $0.40
memory_cost = gb_seconds * $0.0000025
cpu_cost = vcpu_seconds * $0.00002400
```

#### Example Request

```json
{
  "provider": "gcp_functions",
  "memory_mb": 512,
  "execution_time_seconds": 5,
  "monthly_executions": 1000000,
  "include_free_tier": true,
  "egress_per_request_kb": 10.0,
  "internet_transfer_ratio": 80.0,
  "exchange_rate": 150.0
}
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "provider": "gcp_functions",
    "service_name": "Google Cloud Functions",
    "total_cost_usd": 2.25,
    "total_cost_jpy": 337.5,
    "cost_breakdown": {
      "request_cost": 0.0,
      "memory_cost": 1.25,
      "cpu_cost": 1.0,
      "egress_cost": 0.0
    },
    "free_tier_savings": {
      "request_savings": 0.40,
      "compute_savings": 1.0
    },
    "resource_usage": {
      "requests_used": 1000000,
      "requests_free": 2000000,
      "gb_seconds_used": 2500,
      "gb_seconds_free": 400000
    },
    "provider_features": {
      "cold_start_optimization": true,
      "auto_scaling": true,
      "integrated_monitoring": true
    },
    "configuration": {
      "memory_mb": 512,
      "execution_time_seconds": 5,
      "monthly_executions": 1000000,
      "cpu_count": null,
      "include_free_tier": true
    }
  }
}
```

#### Parameter Validation

- `provider`: Must be one of supported providers
- `memory_mb`: Must be positive
- `execution_time_seconds`: Must be positive
- `monthly_executions`: Must be non-negative
- `cpu_count`: Required for `gcp_cloudrun`, must be positive
- `egress_per_request_kb`: Must be >= 0
- `internet_transfer_ratio`: Must be 0-100
- `exchange_rate`: Must be positive

### 9. Serverless Providers Info

Get information about supported serverless providers and their capabilities.

**Endpoint**: `GET /serverless/providers`

#### Response Format

```json
{
  "success": true,
  "data": {
    "supported_providers": [
      "aws_lambda",
      "gcp_functions", 
      "gcp_cloudrun",
      "azure_functions",
      "oci_functions"
    ],
    "provider_info": {
      "aws_lambda": {
        "name": "AWS Lambda",
        "pricing_model": "Request + GB-second",
        "free_tier": "1,000,000 requests + 400,000 GB-seconds/month",
        "max_execution_time": 900,
        "max_memory": 10240
      },
      "gcp_functions": {
        "name": "Google Cloud Functions",
        "pricing_model": "Request + Memory + CPU",
        "free_tier": "2,000,000 requests + 400,000 GB-seconds/month",
        "max_execution_time": 540,
        "max_memory": 8192
      },
      "gcp_cloudrun": {
        "name": "Google Cloud Run",
        "pricing_model": "Request + Memory + vCPU",
        "free_tier": "2,000,000 requests + 360,000 vCPU-seconds/month",
        "max_execution_time": 3600,
        "max_memory": 32768
      }
    }
  }
}
```

## Integration Examples

### Complete Cost Analysis Workflow

```javascript
// 1. Get available instances
const instancesResponse = await fetch('/api/calculator/instances');
const instances = await instancesResponse.json();

// 2. Calculate Lambda costs
const lambdaResponse = await fetch('/api/calculator/lambda', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    memory_mb: 512,
    execution_time_seconds: 10,
    monthly_executions: 1000000,
    include_free_tier: true,
    egress_per_request_kb: 50.0
  })
});
const lambdaCost = await lambdaResponse.json();

// 3. Generate comparison data
const comparisonResponse = await fetch('/api/calculator/comparison', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lambda_config: {
      memory_mb: 512,
      execution_time_seconds: 10,
      include_free_tier: true
    },
    vm_configs: [
      { provider: 'aws_ec2', instance_type: 't3.small' },
      { provider: 'google_cloud', instance_type: 'e2-medium' }
    ]
  })
});
const comparison = await comparisonResponse.json();

// 4. Export to CSV
const csvResponse = await fetch('/api/calculator/export_csv', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    lambda_config: { /* config */ },
    vm_configs: [ /* configs */ ],
    currency: 'JPY',
    exchange_rate: 150.0
  })
});
const csvBlob = await csvResponse.blob();
```

### Error Handling Best Practices

```javascript
async function calculateCosts(config) {
  try {
    const response = await fetch('/api/calculator/lambda', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config)
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      throw new Error(result.error || `HTTP ${response.status}`);
    }
    
    if (!result.success) {
      throw new Error(result.error || 'Calculation failed');
    }
    
    return result.data;
  } catch (error) {
    console.error('Cost calculation failed:', error.message);
    throw error;
  }
}
```

### Multi-Provider Serverless Comparison

```javascript
async function compareServerlessProviders(config) {
  const providers = ['aws_lambda', 'gcp_functions', 'azure_functions'];
  const results = {};
  
  for (const provider of providers) {
    try {
      const response = await fetch('/api/calculator/serverless', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...config, provider })
      });
      
      const result = await response.json();
      if (result.success) {
        results[provider] = result.data;
      }
    } catch (error) {
      console.error(`Failed to calculate costs for ${provider}:`, error);
    }
  }
  
  return results;
}
```

## Rate Limits and Performance

- No rate limits currently implemented
- Response times typically < 100ms for single calculations
- Comparison endpoints may take longer due to multiple calculations
- CSV export includes streaming for large datasets

## Versioning

Current API version: 1.0  
No versioning scheme currently implemented in URLs.

## Support and Troubleshooting

Common issues and solutions:

1. **400 Bad Request**: Check required parameters and data types
2. **Invalid provider/instance**: Use `/instances` endpoint to get valid options
3. **Calculation errors**: Verify numeric parameters are within valid ranges
4. **Currency conversion**: Ensure positive exchange rates

For additional support, check the application logs for detailed error messages.