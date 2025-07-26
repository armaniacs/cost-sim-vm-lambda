"""
Calculator API endpoints
REST API for Lambda and VM cost calculations
"""
from typing import Union

from flask import Blueprint, Response, jsonify, request

from app.models.lambda_calculator import LambdaCalculator, LambdaConfig
from app.models.vm_calculator import VMCalculator, VMConfig
from app.models.serverless_calculator import ServerlessCalculator, ServerlessConfig

# Create Blueprint
calculator_bp = Blueprint("calculator", __name__)

# Initialize calculators
lambda_calc = LambdaCalculator()
vm_calc = VMCalculator()
serverless_calc = ServerlessCalculator()


@calculator_bp.route("/lambda", methods=["POST"])
def calculate_lambda_cost() -> Union[Response, tuple[Response, int]]:
    """
    Calculate AWS Lambda costs

    Expected JSON payload:
    {
        "memory_mb": 512,
        "execution_time_seconds": 10,
        "monthly_executions": 1000000,
        "include_free_tier": true
    }
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = [
            "memory_mb",
            "execution_time_seconds",
            "monthly_executions",
        ]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return (
                jsonify({"error": f"Missing required fields: {missing_fields}"}),
                400,
            )

        # Validate egress parameter
        egress_per_request_kb = data.get("egress_per_request_kb", 0.0)
        if egress_per_request_kb < 0:
            return (
                jsonify({"error": "Egress transfer amount must be zero or positive"}),
                400,
            )

        # Validate internet transfer ratio parameter (PBI10)
        internet_transfer_ratio = data.get("internet_transfer_ratio", 100.0)
        if internet_transfer_ratio < 0 or internet_transfer_ratio > 100:
            return (
                jsonify({"error": "転送割合は0-100の範囲で入力してください"}),
                400,
            )

        # Create configuration
        config = LambdaConfig(
            memory_mb=int(data["memory_mb"]),
            execution_time_seconds=int(data["execution_time_seconds"]),
            monthly_executions=int(data["monthly_executions"]),
            include_free_tier=data.get("include_free_tier", True),
            egress_per_request_kb=float(egress_per_request_kb),
            internet_transfer_ratio=float(internet_transfer_ratio),  # PBI10
        )

        # Calculate cost
        custom_egress_rates = data.get("custom_egress_rates", {})
        include_egress_free_tier = data.get("include_egress_free_tier", True)

        if custom_egress_rates:
            result = lambda_calc.calculate_total_cost(
                config, custom_egress_rates, include_egress_free_tier
            )
        else:
            result = lambda_calc.calculate_total_cost(
                config, None, include_egress_free_tier
            )

        return jsonify({"success": True, "data": result})

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/vm", methods=["POST"])
def calculate_vm_cost() -> Union[Response, tuple[Response, int]]:
    """
    Calculate VM costs (EC2, Sakura Cloud, or Google Cloud)

    Expected JSON payload:
    {
        "provider": "aws_ec2",  # or "sakura_cloud" or "google_cloud"
        "instance_type": "t3.small",
        "region": "ap-northeast-1"
    }
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        # Validate required fields
        required_fields = ["provider", "instance_type"]
        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return (
                jsonify({"error": f"Missing required fields: {missing_fields}"}),
                400,
            )

        # Create configuration
        config = VMConfig(
            provider=data["provider"],
            instance_type=data["instance_type"],
            region=data.get("region", "ap-northeast-1"),
        )

        # Check if egress parameters are provided for PBI10
        monthly_executions = data.get("monthly_executions", 0)
        egress_per_request_kb = data.get("egress_per_request_kb", 0.0)
        internet_transfer_ratio = data.get("internet_transfer_ratio", 100.0)

        # Validate internet transfer ratio if provided
        if internet_transfer_ratio < 0 or internet_transfer_ratio > 100:
            return (
                jsonify({"error": "転送割合は0-100の範囲で入力してください"}),
                400,
            )

        # Calculate cost with or without egress
        if monthly_executions > 0 and egress_per_request_kb >= 0:
            # Calculate cost including egress
            custom_egress_rates = data.get("custom_egress_rates", {})
            include_egress_free_tier = data.get("include_egress_free_tier", True)

            if custom_egress_rates:
                result = vm_calc.get_monthly_cost_with_egress(
                    config,
                    monthly_executions,
                    egress_per_request_kb,
                    custom_egress_rates,
                    include_egress_free_tier,
                    internet_transfer_ratio,  # PBI10
                )
            else:
                result = vm_calc.get_monthly_cost_with_egress(
                    config,
                    monthly_executions,
                    egress_per_request_kb,
                    None,
                    include_egress_free_tier,
                    internet_transfer_ratio,  # PBI10
                )
        else:
            # Calculate basic cost only
            result = vm_calc.calculate_vm_cost(config)

        if result is None:
            return (
                jsonify(
                    {
                        "error": (
                            f"Invalid provider '{config.provider}' "
                            f"or instance type '{config.instance_type}'"
                        )
                    }
                ),
                400,
            )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/comparison", methods=["POST"])
def calculate_comparison() -> Union[Response, tuple[Response, int]]:
    """
    Generate cost comparison between Lambda and VMs

    Expected JSON payload:
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
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        lambda_config_data = data.get("lambda_config", {})
        vm_configs_data = data.get("vm_configs", [])
        execution_range = data.get("execution_range", {})
        custom_egress_rates = data.get("custom_egress_rates", {})

        # Default execution range
        min_executions = execution_range.get("min", 0)
        max_executions = execution_range.get("max", 10_000_000)
        steps = execution_range.get("steps", 50)

        # Generate execution count points
        if steps <= 1:
            execution_points = [min_executions, max_executions]
        else:
            step_size = (max_executions - min_executions) / (steps - 1)
            execution_points = [
                int(min_executions + i * step_size) for i in range(steps)
            ]

        # Validate egress parameter for comparison
        egress_per_request_kb = lambda_config_data.get("egress_per_request_kb", 0.0)
        if egress_per_request_kb < 0:
            return (
                jsonify({"error": "Egress transfer amount must be zero or positive"}),
                400,
            )

        # Validate internet transfer ratio parameter for comparison (PBI10)
        internet_transfer_ratio = lambda_config_data.get(
            "internet_transfer_ratio", 100.0
        )
        if internet_transfer_ratio < 0 or internet_transfer_ratio > 100:
            return (
                jsonify({"error": "転送割合は0-100の範囲で入力してください"}),
                400,
            )

        # Calculate Lambda costs for each execution point
        comparison_data = []
        break_even_points = []

        for executions in execution_points:
            # Lambda cost
            lambda_config = LambdaConfig(
                memory_mb=lambda_config_data.get("memory_mb", 512),
                execution_time_seconds=lambda_config_data.get(
                    "execution_time_seconds", 10
                ),
                monthly_executions=executions,
                include_free_tier=lambda_config_data.get("include_free_tier", True),
                egress_per_request_kb=float(egress_per_request_kb),
                internet_transfer_ratio=float(internet_transfer_ratio),  # PBI10
            )

            # Use custom egress rates if provided
            include_egress_free_tier = data.get("include_egress_free_tier", True)
            if custom_egress_rates:
                lambda_result = lambda_calc.calculate_total_cost(
                    lambda_config, custom_egress_rates, include_egress_free_tier
                )
            else:
                lambda_result = lambda_calc.calculate_total_cost(
                    lambda_config, None, include_egress_free_tier
                )
            lambda_cost = lambda_result["total_cost"]

            # VM costs
            vm_costs = {}
            for vm_config_data in vm_configs_data:
                vm_config = VMConfig(
                    provider=vm_config_data["provider"],
                    instance_type=vm_config_data["instance_type"],
                    region=vm_config_data.get("region", "ap-northeast-1"),
                )

                # Calculate VM cost with egress
                if custom_egress_rates:
                    vm_result = vm_calc.get_monthly_cost_with_egress(
                        vm_config,
                        executions,
                        egress_per_request_kb,
                        custom_egress_rates,
                        include_egress_free_tier,
                        internet_transfer_ratio,  # PBI10
                    )
                else:
                    vm_result = vm_calc.get_monthly_cost_with_egress(
                        vm_config,
                        executions,
                        egress_per_request_kb,
                        None,
                        include_egress_free_tier,
                        internet_transfer_ratio,  # PBI10
                    )
                if vm_result:
                    vm_key = f"{vm_config.provider}_{vm_config.instance_type}"
                    if "total_monthly_cost_usd" in vm_result:
                        vm_costs[vm_key] = vm_result["total_monthly_cost_usd"]
                    elif "total_monthly_cost_jpy" in vm_result:
                        # Convert JPY to USD for comparison
                        vm_costs[vm_key] = vm_result["total_monthly_cost_jpy"] / 150.0

            comparison_data.append(
                {
                    "executions_per_month": executions,
                    "lambda_cost_usd": lambda_cost,
                    "vm_costs": vm_costs,
                }
            )

        # Calculate break-even points
        for vm_config_data in vm_configs_data:
            vm_config = VMConfig(
                provider=vm_config_data["provider"],
                instance_type=vm_config_data["instance_type"],
            )
            vm_result = vm_calc.calculate_vm_cost(vm_config)

            if vm_result:
                vm_monthly_cost_usd = (
                    vm_result.get("monthly_cost_usd", 0)
                    or vm_result.get("monthly_cost_jpy", 0) / 150.0
                )

                # Find break-even point (approximate)
                for point in comparison_data:
                    if point["lambda_cost_usd"] >= vm_monthly_cost_usd:
                        break_even_points.append(
                            {
                                "vm_provider": vm_config.provider,
                                "vm_instance": vm_config.instance_type,
                                "executions_per_month": point["executions_per_month"],
                                "executions_per_second": point["executions_per_month"]
                                / (30 * 24 * 3600),  # Approximate
                            }
                        )
                        break

        return jsonify(
            {
                "success": True,
                "data": {
                    "comparison_data": comparison_data,
                    "break_even_points": break_even_points,
                    "lambda_configuration": lambda_config_data,
                    "vm_configurations": vm_configs_data,
                },
            }
        )

    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/export_csv", methods=["POST"])
def export_csv() -> Union[Response, tuple[Response, int]]:
    """
    Export comparison data to CSV format with egress cost breakdown

    Expected JSON payload:
    {
        "lambda_config": {
            "memory_mb": 512,
            "execution_time_seconds": 10,
            "monthly_executions": 1000000,
            "include_free_tier": true,
            "egress_per_request_kb": 100
        },
        "vm_configs": [
            {
                "provider": "aws_ec2",
                "instance_type": "t3.small"
            }
        ],
        "currency": "USD",
        "exchange_rate": 150.0
    }
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        lambda_config_data = data.get("lambda_config", {})
        vm_configs_data = data.get("vm_configs", [])
        currency = data.get("currency", "USD")
        exchange_rate = data.get("exchange_rate", 150.0)
        custom_egress_rates = data.get("custom_egress_rates", {})

        # Validate egress parameter
        egress_per_request_kb = lambda_config_data.get("egress_per_request_kb", 0.0)
        if egress_per_request_kb < 0:
            return (
                jsonify({"error": "Egress transfer amount must be zero or positive"}),
                400,
            )

        # Validate internet transfer ratio parameter for CSV export (PBI10)
        internet_transfer_ratio = lambda_config_data.get(
            "internet_transfer_ratio", 100.0
        )
        if internet_transfer_ratio < 0 or internet_transfer_ratio > 100:
            return (
                jsonify({"error": "転送割合は0-100の範囲で入力してください"}),
                400,
            )

        # Create lambda config
        lambda_config = LambdaConfig(
            memory_mb=lambda_config_data.get("memory_mb", 512),
            execution_time_seconds=lambda_config_data.get("execution_time_seconds", 10),
            monthly_executions=lambda_config_data.get("monthly_executions", 1_000_000),
            include_free_tier=lambda_config_data.get("include_free_tier", True),
            egress_per_request_kb=float(egress_per_request_kb),
            internet_transfer_ratio=float(internet_transfer_ratio),  # PBI10
        )

        # Calculate Lambda costs
        include_egress_free_tier = data.get("include_egress_free_tier", True)
        if custom_egress_rates:
            lambda_result = lambda_calc.calculate_total_cost(
                lambda_config, custom_egress_rates, include_egress_free_tier
            )
        else:
            lambda_result = lambda_calc.calculate_total_cost(
                lambda_config, None, include_egress_free_tier
            )

        # Calculate VM costs with egress
        vm_results = []
        for vm_config_data in vm_configs_data:
            vm_config = VMConfig(
                provider=vm_config_data["provider"],
                instance_type=vm_config_data["instance_type"],
                region=vm_config_data.get("region", "ap-northeast-1"),
            )

            if custom_egress_rates:
                vm_result = vm_calc.get_monthly_cost_with_egress(
                    vm_config,
                    lambda_config.monthly_executions,
                    egress_per_request_kb,
                    custom_egress_rates,
                    include_egress_free_tier,
                    internet_transfer_ratio,  # PBI10
                )
            else:
                vm_result = vm_calc.get_monthly_cost_with_egress(
                    vm_config,
                    lambda_config.monthly_executions,
                    egress_per_request_kb,
                    None,
                    include_egress_free_tier,
                    internet_transfer_ratio,  # PBI10
                )
            if vm_result:
                vm_results.append(vm_result)

        # Generate CSV content
        csv_lines = []

        # CSV Headers
        headers = [
            "provider",
            "instance_type",
            "lambda_execution_cost_usd",
            "lambda_egress_cost_usd",
            "lambda_total_cost_usd",
            "vm_fixed_cost_usd",
            "vm_egress_cost_usd",
            "vm_total_cost_usd",
        ]

        if currency == "JPY":
            headers.extend(
                [
                    "lambda_execution_cost_jpy",
                    "lambda_egress_cost_jpy",
                    "lambda_total_cost_jpy",
                    "vm_fixed_cost_jpy",
                    "vm_egress_cost_jpy",
                    "vm_total_cost_jpy",
                ]
            )

        csv_lines.append(",".join(headers))

        # Lambda costs
        lambda_execution_cost = (
            lambda_result["request_charges"] + lambda_result["compute_charges"]
        )
        lambda_egress_cost = lambda_result.get("egress_charges", 0.0)
        lambda_total_cost = lambda_result["total_cost"]

        # Data rows for each VM
        for vm_result in vm_results:
            provider = vm_result["provider"]
            instance_type = vm_result["instance_type"]

            # VM costs
            if "total_monthly_cost_usd" in vm_result:
                vm_fixed_cost = vm_result["monthly_cost_usd"]
                vm_egress_cost = vm_result.get("egress_cost_usd", 0.0)
                vm_total_cost = vm_result["total_monthly_cost_usd"]
            else:
                # Sakura Cloud (JPY)
                vm_fixed_cost = vm_result["monthly_cost_jpy"] / exchange_rate
                vm_egress_cost = vm_result.get("egress_cost_jpy", 0.0) / exchange_rate
                vm_total_cost = vm_result["total_monthly_cost_jpy"] / exchange_rate

            row = [
                provider,
                instance_type,
                f"{lambda_execution_cost:.4f}",
                f"{lambda_egress_cost:.4f}",
                f"{lambda_total_cost:.4f}",
                f"{vm_fixed_cost:.4f}",
                f"{vm_egress_cost:.4f}",
                f"{vm_total_cost:.4f}",
            ]

            if currency == "JPY":
                row.extend(
                    [
                        f"{lambda_execution_cost * exchange_rate:.2f}",
                        f"{lambda_egress_cost * exchange_rate:.2f}",
                        f"{lambda_total_cost * exchange_rate:.2f}",
                        f"{vm_fixed_cost * exchange_rate:.2f}",
                        f"{vm_egress_cost * exchange_rate:.2f}",
                        f"{vm_total_cost * exchange_rate:.2f}",
                    ]
                )

            csv_lines.append(",".join(row))

        csv_content = "\n".join(csv_lines)

        # Return CSV as response
        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={
                "Content-Disposition": (
                    "attachment; filename=cost_comparison_with_egress.csv"
                )
            },
        )

        return response

    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/instances", methods=["GET"])
def get_available_instances() -> Union[Response, tuple[Response, int]]:
    """
    Get available instance types for all providers
    """
    try:
        provider = request.args.get("provider")

        if provider:
            # Get instances for specific provider
            instances = vm_calc.get_available_instances(provider)
            return jsonify({"success": True, "data": {provider: instances}})
        else:
            # Get instances for all providers
            all_instances = {
                "aws_ec2": vm_calc.get_available_instances("aws_ec2"),
                "sakura_cloud": vm_calc.get_available_instances("sakura_cloud"),
                "google_cloud": vm_calc.get_available_instances("google_cloud"),
            }
            return jsonify({"success": True, "data": all_instances})

    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/recommend", methods=["POST"])
def recommend_instances() -> Union[Response, tuple[Response, int]]:
    """
    Recommend VM instances based on Lambda configuration

    Expected JSON payload:
    {
        "lambda_memory_mb": 512
    }
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        lambda_memory_mb = data.get("lambda_memory_mb")
        if lambda_memory_mb is None:
            return jsonify({"error": "lambda_memory_mb is required"}), 400

        recommendations = vm_calc.recommend_instance_for_lambda(int(lambda_memory_mb))

        return jsonify({"success": True, "data": recommendations})

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/currency/convert", methods=["POST"])
def convert_currency() -> Union[Response, tuple[Response, int]]:
    """
    Convert between USD and JPY

    Expected JSON payload:
    {
        "amount": 19.58,
        "from_currency": "USD",
        "to_currency": "JPY",
        "exchange_rate": 150
    }
    """
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400

        amount = data.get("amount")
        from_currency = data.get("from_currency", "USD")
        to_currency = data.get("to_currency", "JPY")
        exchange_rate = data.get("exchange_rate", 150.0)

        if amount is None:
            return jsonify({"error": "amount is required"}), 400

        if from_currency == "USD" and to_currency == "JPY":
            converted_amount = vm_calc.convert_currency(float(amount), exchange_rate)
        elif from_currency == "JPY" and to_currency == "USD":
            converted_amount = float(amount) / exchange_rate
        else:
            return jsonify({"error": "Only USD<->JPY conversion supported"}), 400

        return jsonify(
            {
                "success": True,
                "data": {
                    "original_amount": float(amount),
                    "converted_amount": converted_amount,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "exchange_rate": exchange_rate,
                },
            }
        )

    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid input data: {str(e)}"}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/serverless", methods=["POST"])
def calculate_serverless_cost() -> Union[Response, tuple[Response, int]]:
    """
    Calculate serverless costs for various providers
    
    Expected JSON payload:
    {
        "provider": "gcp_functions",  // "aws_lambda", "gcp_functions", "gcp_cloudrun", "azure_functions", "oci_functions"
        "memory_mb": 512,
        "execution_time_seconds": 5,
        "monthly_executions": 1000000,
        "include_free_tier": true,
        "cpu_count": 1.0,  // For Cloud Run only
        "egress_per_request_kb": 10.0,
        "internet_transfer_ratio": 80.0,
        "exchange_rate": 150.0,
        "include_ecosystem_benefits": false
    }
    """
    try:
        data = request.get_json(silent=True)
        
        if data is None:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        required_fields = [
            "provider",
            "memory_mb", 
            "execution_time_seconds",
            "monthly_executions"
        ]
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields:
            return (
                jsonify({"error": f"Missing required fields: {missing_fields}"}),
                400,
            )
        
        # Validate provider
        provider = data["provider"]
        supported_providers = serverless_calc.get_supported_providers()
        if provider not in supported_providers:
            return (
                jsonify({
                    "error": f"Provider '{provider}' not supported. Available: {supported_providers}"
                }),
                400,
            )
        
        # Validate numeric parameters
        try:
            memory_mb = int(data["memory_mb"])
            execution_time_seconds = float(data["execution_time_seconds"])
            monthly_executions = int(data["monthly_executions"])
        except (ValueError, TypeError) as e:
            return (
                jsonify({"error": f"Invalid numeric parameters: {str(e)}"}),
                400,
            )
        
        # Validate optional parameters
        cpu_count = data.get("cpu_count")
        if cpu_count is not None:
            try:
                cpu_count = float(cpu_count)
                if cpu_count <= 0:
                    return jsonify({"error": "CPU count must be positive"}), 400
            except (ValueError, TypeError):
                return jsonify({"error": "Invalid CPU count"}), 400
        
        egress_per_request_kb = data.get("egress_per_request_kb", 0.0)
        if egress_per_request_kb < 0:
            return (
                jsonify({"error": "Egress transfer amount must be zero or positive"}),  
                400,
            )
        
        internet_transfer_ratio = data.get("internet_transfer_ratio", 100.0)
        if internet_transfer_ratio < 0 or internet_transfer_ratio > 100:
            return (
                jsonify({"error": "Internet transfer ratio must be between 0 and 100"}),
                400,
            )
        
        exchange_rate = data.get("exchange_rate", 150.0)
        if exchange_rate <= 0:
            return jsonify({"error": "Exchange rate must be positive"}), 400
        
        # Create serverless configuration
        config = ServerlessConfig(
            provider=provider,
            memory_mb=memory_mb,
            execution_time_seconds=execution_time_seconds,
            monthly_executions=monthly_executions,
            include_free_tier=data.get("include_free_tier", True),
            cpu_count=cpu_count,
            egress_per_request_kb=float(egress_per_request_kb),
            internet_transfer_ratio=float(internet_transfer_ratio),
            exchange_rate=float(exchange_rate),
            include_ecosystem_benefits=data.get("include_ecosystem_benefits", False)
        )
        
        # Calculate cost using unified serverless calculator
        include_egress_free_tier = data.get("include_egress_free_tier")
        result = serverless_calc.calculate(config, include_egress_free_tier)
        
        # Convert ServerlessResult to API response format
        response_data = {
            "provider": result.provider,
            "service_name": result.service_name,
            "total_cost_usd": result.total_cost_usd,
            "total_cost_jpy": result.total_cost_jpy,
            "cost_breakdown": result.breakdown,
            "free_tier_savings": result.free_tier_savings,
            "resource_usage": result.resource_usage,
            "provider_features": result.features,
            "configuration": {
                "memory_mb": config.memory_mb,
                "execution_time_seconds": config.execution_time_seconds,
                "monthly_executions": config.monthly_executions,
                "cpu_count": config.cpu_count,
                "include_free_tier": config.include_free_tier
            }
        }
        
        return jsonify({"success": True, "data": response_data})
        
    except ValueError as e:
        # Handle validation errors from ServerlessCalculator
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )


@calculator_bp.route("/serverless/providers", methods=["GET"])
def get_serverless_providers() -> Union[Response, tuple[Response, int]]:
    """
    Get information about supported serverless providers
    """
    try:
        providers = serverless_calc.get_supported_providers()
        provider_info = {}
        
        for provider in providers:
            provider_info[provider] = serverless_calc.get_provider_info(provider)
        
        return jsonify({
            "success": True,
            "data": {
                "supported_providers": providers,
                "provider_info": provider_info
            }
        })
        
    except Exception as e:
        return (
            jsonify({"error": f"Internal server error: {str(e)}"}),
            500,
        )
