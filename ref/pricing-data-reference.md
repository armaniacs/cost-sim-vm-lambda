# Pricing Data Reference

## Overview

This document provides comprehensive reference for all pricing data used in the cost simulator, including current rates, calculation methods, and data sources.

## AWS Lambda Pricing

### Base Pricing (Tokyo Region - ap-northeast-1)
- **Request Charges**: $0.20 per 1 million requests
- **Compute Charges**: $0.0000166667 per GB-second
- **Memory Options**: 128MB, 512MB, 1024MB, 2048MB
- **Execution Time Range**: 1-60 seconds

### Free Tier Allowances
- **Monthly Requests**: 1,000,000 requests/month
- **Compute Time**: 400,000 GB-seconds/month
- **Free Tier Calculation**: Applied first, then pay-as-you-go rates

### Egress Pricing
- **Rate**: $0.114 per GB (Tokyo region)
- **Free Allowance**: 100GB per month
- **Internet Transfer Ratio**: 0-100% configurable (PBI10)

## VM Pricing by Provider

### AWS EC2 (Tokyo Region)

| Instance Type | vCPU | Memory | Hourly (USD) | Monthly (USD) |
|---------------|------|---------|--------------|---------------|
| t3.micro      | 2    | 1GB     | $0.0136      | $9.93         |
| t3.small      | 2    | 2GB     | $0.0272      | $19.86        |
| t3.medium     | 2    | 4GB     | $0.0544      | $39.71        |
| t3.large      | 2    | 8GB     | $0.1088      | $79.42        |
| c5.large      | 2    | 4GB     | $0.096       | $70.08        |
| c5.xlarge     | 4    | 8GB     | $0.192       | $140.16       |

**Egress**: $0.114/GB after 100GB free allowance

### Google Cloud Platform (Tokyo - asia-northeast1)

| Instance Type   | vCPU | Memory | Hourly (USD) | Monthly (USD) |
|-----------------|------|---------|--------------|---------------|
| e2-micro        | 0.25 | 1GB     | $0.0084      | $6.13         |
| e2-small        | 0.5  | 2GB     | $0.0168      | $12.26        |
| e2-medium       | 1    | 4GB     | $0.0335      | $24.46        |
| n2-standard-1   | 1    | 4GB     | $0.0485      | $35.41        |
| n2-standard-2   | 2    | 8GB     | $0.0970      | $70.81        |
| c2-standard-4   | 4    | 16GB    | $0.2088      | $152.42       |

**Egress**: $0.12/GB after 100GB free allowance

### Microsoft Azure (Japan East)

| Instance Type | vCPU | Memory | Hourly (USD) | Monthly (USD) |
|---------------|------|---------|--------------|---------------|
| B1ls          | 1    | 0.5GB   | $0.0092      | $6.72         |
| B1s           | 1    | 1GB     | $0.0104      | $7.59         |
| B1ms          | 1    | 2GB     | $0.0208      | $15.18        |
| B2s           | 2    | 4GB     | $0.0416      | $30.37        |
| B2ms          | 2    | 8GB     | $0.0832      | $60.74        |
| A1_Basic      | 1    | 1.75GB  | $0.016       | $11.68        |
| D3            | 4    | 14GB    | $0.308       | $224.84       |
| D4            | 8    | 28GB    | $0.616       | $450.08       |

**Egress**: $0.12/GB after 100GB free allowance

### Oracle Cloud Infrastructure (Tokyo - ap-tokyo-1)

| Instance Type                | vCPU | Memory | Hourly (USD) | Monthly (USD) | Notes |
|------------------------------|------|---------|--------------|---------------|-------|
| VM.Standard.E2.1.Micro_Free | 1    | 1GB     | $0.000       | $0.00         | Always Free |
| VM.Standard.A1.Flex_Free    | 4    | 24GB    | $0.000       | $0.00         | Always Free |
| VM.Standard.E2.1.Micro      | 1    | 1GB     | $0.005       | $3.65         | |
| VM.Standard.A1.Flex_1_6     | 1    | 6GB     | $0.015       | $10.95        | Arm-based |
| VM.Standard.E4.Flex_1_8     | 1    | 8GB     | $0.025       | $18.25        | |
| VM.Standard.A1.Flex_2_12    | 2    | 12GB    | $0.030       | $21.90        | Arm-based |
| VM.Standard.E4.Flex_2_16    | 2    | 16GB    | $0.049       | $35.77        | |

**Egress**: $0.025/GB after 10TB free allowance per month
**Always Free Tier**: 2x E2.1.Micro + up to 4 A1.Flex instances

### Sakura Cloud (Tokyo)

| Instance Type | vCPU | Memory | Storage | Monthly (JPY) | Monthly (USD @150) |
|---------------|------|---------|---------|---------------|--------------------|
| 1core_1gb     | 1    | 1GB     | 20GB    | ¥1,595        | $10.63             |
| 2core_2gb     | 2    | 2GB     | 20GB    | ¥3,190        | $21.27             |
| 2core_4gb     | 2    | 4GB     | 20GB    | ¥4,180        | $27.87             |
| 4core_8gb     | 4    | 8GB     | 40GB    | ¥7,370        | $49.13             |
| 6core_12gb    | 6    | 12GB    | 60GB    | ¥11,560       | $77.07             |

**Egress**: Unlimited free transfer (no egress charges)

## Egress Pricing Summary

### Comprehensive Egress Rates

| Provider | Free Allowance | Rate (USD/GB) | Notes |
|----------|----------------|---------------|-------|
| AWS Lambda/EC2 | 100GB/month | $0.114 | Tokyo region premium |
| Google Cloud | 100GB/month | $0.12 | Standard global rate |
| Azure | 100GB/month | $0.12 | Global rate |
| Oracle Cloud | 10TB/month | $0.025 | Significantly higher free tier |
| Sakura Cloud | Unlimited | $0.00 | No egress charges |

### Internet Transfer Ratio (PBI10)
- **Purpose**: Configure percentage of traffic going to internet vs private networks
- **Range**: 0% (fully private) to 100% (fully internet)
- **Presets**: 0%, 10%, 50%, 100% + custom input
- **Impact**: Multiplies egress calculations by the percentage

## Currency Conversion

### Exchange Rate Configuration
- **Base Currency**: USD for all international providers
- **Japanese Yen**: JPY for Sakura Cloud
- **Default Rate**: ¥150 per USD
- **Configurable**: User can set custom exchange rates
- **Application**: Applied to final cost calculations for display

## Pricing Data Sources

### Cloud Provider APIs (Future - PBI11)
- **Azure Retail Prices API**: Real-time Azure pricing
- **AWS Pricing API**: Current AWS rates with authentication
- **Google Cloud Billing API**: GCP pricing information
- **Exchange Rate API**: Live currency conversion rates

### Current Data Management
- **Static Configuration**: Pricing data stored in calculator classes
- **Manual Updates**: Pricing reviewed and updated manually
- **Regional Focus**: Primarily Tokyo/Asia-Pacific regions
- **Validation**: Test coverage ensures pricing calculation accuracy

## Break-Even Analysis

### Calculation Methodology
1. **Lambda Variable Cost**: Function of execution frequency and duration
2. **VM Fixed Cost**: Constant monthly cost regardless of usage
3. **Egress Impact**: Added to both Lambda and VM costs based on transfer volume
4. **Intersection Point**: Where Lambda total cost equals VM total cost

### Cost Components
- **Lambda Total**: Request charges + compute charges + egress fees
- **VM Total**: Instance hourly rate × 730 hours + egress fees
- **Break-even Formula**: Find executions where Lambda_total = VM_total

## Data Validation

### Test Coverage
- **Unit Tests**: Verify individual pricing calculations
- **Integration Tests**: Test complete cost comparison workflows
- **E2E Tests**: Validate user scenarios with realistic pricing
- **Coverage Metrics**: 88% code coverage across all pricing logic

### Accuracy Measures
- **Provider Verification**: Pricing data verified against official sources
- **Regular Updates**: Monthly review of pricing changes
- **Test Scenarios**: Comprehensive test cases cover edge cases
- **Currency Precision**: Calculations maintain precision to 3 decimal places