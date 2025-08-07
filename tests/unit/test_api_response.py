"""
Unit tests for API response utilities
Tests standardized API response formats
"""
import pytest
from flask import Flask, jsonify
from app.utils.api_response import APIResponse


class TestAPIResponse:
    """Test the APIResponse utility class"""
    
    def setup_method(self):
        """Set up test Flask app"""
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
        
    def test_success_response(self):
        """Test successful API response"""
        with self.app.app_context():
            data = {"result": "success"}
            response, status_code = APIResponse.success(data)
            
            assert status_code == 200
            response_data = response.get_json()
            assert response_data["success"] is True
            assert response_data["data"] == data
            assert "message" not in response_data
    
    def test_success_response_with_message(self):
        """Test successful API response with message"""
        with self.app.app_context():
            data = {"result": "success"}
            message = "Operation completed"
            response, status_code = APIResponse.success(data, message)
            
            assert status_code == 200
            response_data = response.get_json()
            assert response_data["success"] is True
            assert response_data["data"] == data
            assert response_data["message"] == message
    
    def test_success_response_custom_status(self):
        """Test successful API response with custom status code"""
        with self.app.app_context():
            data = {"result": "created"}
            response, status_code = APIResponse.success(data, status_code=201)
            
            assert status_code == 201
            response_data = response.get_json()
            assert response_data["success"] is True
            assert response_data["data"] == data
    
    def test_error_response(self):
        """Test error API response"""
        with self.app.app_context():
            message = "Something went wrong"
            response, status_code = APIResponse.error(message)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert "code" not in response_data["error"]
            assert "details" not in response_data["error"]
    
    def test_error_response_with_code(self):
        """Test error API response with error code"""
        with self.app.app_context():
            message = "Invalid input"
            error_code = "VALIDATION_ERROR"
            response, status_code = APIResponse.error(message, error_code)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert response_data["error"]["code"] == error_code
    
    def test_error_response_with_details(self):
        """Test error API response with details"""
        with self.app.app_context():
            message = "Multiple errors"
            details = {"field1": "error1", "field2": "error2"}
            response, status_code = APIResponse.error(message, details=details)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert response_data["error"]["details"] == details
    
    def test_error_response_custom_status(self):
        """Test error API response with custom status code"""
        with self.app.app_context():
            message = "Unauthorized"
            response, status_code = APIResponse.error(message, status_code=401)
            
            assert status_code == 401
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
    
    def test_validation_error_response(self):
        """Test validation error response"""
        with self.app.app_context():
            message = "Validation failed"
            response, status_code = APIResponse.validation_error(message)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert response_data["error"]["code"] == "VALIDATION_ERROR"
    
    def test_validation_error_with_field_errors(self):
        """Test validation error response with field errors"""
        with self.app.app_context():
            message = "Validation failed"
            field_errors = {"email": "Invalid email", "password": "Too short"}
            response, status_code = APIResponse.validation_error(message, field_errors)
            
            assert status_code == 400
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert response_data["error"]["code"] == "VALIDATION_ERROR"
            assert response_data["error"]["details"]["field_errors"] == field_errors
    
    def test_internal_error_response(self):
        """Test internal server error response"""
        with self.app.app_context():
            response, status_code = APIResponse.internal_error()
            
            assert status_code == 500
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == "Internal server error"
            assert response_data["error"]["code"] == "INTERNAL_ERROR"
    
    def test_internal_error_with_custom_message(self):
        """Test internal server error with custom message"""
        with self.app.app_context():
            message = "Database connection failed"
            response, status_code = APIResponse.internal_error(message)
            
            assert status_code == 500
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == message
            assert response_data["error"]["code"] == "INTERNAL_ERROR"
    
    def test_not_found_response(self):
        """Test not found error response"""
        with self.app.app_context():
            response, status_code = APIResponse.not_found()
            
            assert status_code == 404
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == "Resource not found"
            assert response_data["error"]["code"] == "NOT_FOUND"
    
    def test_not_found_with_custom_resource(self):
        """Test not found error with custom resource name"""
        with self.app.app_context():
            resource = "User"
            response, status_code = APIResponse.not_found(resource)
            
            assert status_code == 404
            response_data = response.get_json()
            assert response_data["success"] is False
            assert response_data["error"]["message"] == "User not found"
            assert response_data["error"]["code"] == "NOT_FOUND"