"""
Standardized API response utilities
Provides consistent response formats across all endpoints
"""

from typing import Any, Dict, Optional

from flask import Response, jsonify


class APIResponse:
    """Utility class for creating standardized API responses"""

    @staticmethod
    def success(
        data: Any, message: Optional[str] = None, status_code: int = 200
    ) -> tuple[Response, int]:
        """
        Create a successful API response

        Args:
            data: Response data
            message: Optional success message
            status_code: HTTP status code (default: 200)

        Returns:
            Tuple of JSON response and status code
        """
        response = {"success": True, "data": data}
        if message:
            response["message"] = message

        return jsonify(response), status_code

    @staticmethod
    def error(
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        status_code: int = 400,
    ) -> tuple[Response, int]:
        """
        Create an error API response

        Args:
            message: Error message
            error_code: Optional error code for client handling
            details: Optional additional error details
            status_code: HTTP status code (default: 400)

        Returns:
            Tuple of JSON error response and status code
        """
        response = {"success": False, "error": {"message": message}}

        if error_code:
            response["error"]["code"] = error_code

        if details:
            response["error"]["details"] = details

        return jsonify(response), status_code

    @staticmethod
    def validation_error(
        message: str, field_errors: Optional[Dict[str, str]] = None
    ) -> tuple[Response, int]:
        """
        Create a validation error response

        Args:
            message: General validation error message
            field_errors: Optional field-specific error messages

        Returns:
            Tuple of JSON validation error response and status code 400
        """
        details = {}
        if field_errors:
            details["field_errors"] = field_errors

        return APIResponse.error(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details if details else None,
            status_code=400,
        )

    @staticmethod
    def internal_error(message: str = "Internal server error") -> tuple[Response, int]:
        """
        Create an internal server error response

        Args:
            message: Error message

        Returns:
            Tuple of JSON error response and status code 500
        """
        return APIResponse.error(
            message=message, error_code="INTERNAL_ERROR", status_code=500
        )

    @staticmethod
    def not_found(resource: str = "Resource") -> tuple[Response, int]:
        """
        Create a not found error response

        Args:
            resource: Name of the resource that was not found

        Returns:
            Tuple of JSON error response and status code 404
        """
        return APIResponse.error(
            message=f"{resource} not found", error_code="NOT_FOUND", status_code=404
        )
