"""
Authentication API endpoints for enterprise security
"""
import datetime
from typing import Dict, Any
from flask import Blueprint, request, jsonify, current_app, g
from marshmallow import Schema, fields, ValidationError

from app.auth.service import AuthService
from app.auth.jwt_auth import requires_auth, requires_permission
from app.auth.models import User, Role, Permission


# Create Blueprint
auth_bp = Blueprint("auth", __name__)


# Request schemas for validation
class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) > 0)


class RegisterSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=lambda x: len(x) >= 8)
    first_name = fields.Str(allow_none=True)
    last_name = fields.Str(allow_none=True)
    roles = fields.List(fields.Str(), allow_none=True)


class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True)


class ChangePasswordSchema(Schema):
    old_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=lambda x: len(x) >= 8)


class AssignRoleSchema(Schema):
    user_id = fields.Int(required=True)
    role_name = fields.Str(required=True)


# Initialize schemas
login_schema = LoginSchema()
register_schema = RegisterSchema()
refresh_token_schema = RefreshTokenSchema()
change_password_schema = ChangePasswordSchema()
assign_role_schema = AssignRoleSchema()


@auth_bp.route("/login", methods=["POST"])
def login():
    """
    Authenticate user and return JWT tokens
    
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "password123"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        validated_data = login_schema.load(data)
        
        # Authenticate user
        auth_service = AuthService()
        result = auth_service.authenticate_user(
            validated_data["email"],
            validated_data["password"]
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "user": result["user"],
                "tokens": result["tokens"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 401
    
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "Validation error",
            "details": e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/register", methods=["POST"])
def register():
    """
    Register a new user
    
    Expected JSON payload:
    {
        "email": "user@example.com",
        "password": "password123",
        "first_name": "John",
        "last_name": "Doe",
        "roles": ["viewer"]
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        validated_data = register_schema.load(data)
        
        # Create user
        auth_service = AuthService()
        result = auth_service.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name"),
            last_name=validated_data.get("last_name"),
            roles=validated_data.get("roles")
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "user": result["user"]
            }), 201
        else:
            return jsonify({
                "success": False,
                "error": result["error"],
                "details": result.get("details")
            }), 400
    
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "Validation error",
            "details": e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Registration error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """
    Refresh access token using refresh token
    
    Expected JSON payload:
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        validated_data = refresh_token_schema.load(data)
        
        # Refresh token
        auth_service = AuthService()
        result = auth_service.refresh_access_token(validated_data["refresh_token"])
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"],
                "tokens": result["tokens"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 401
    
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "Validation error",
            "details": e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Token refresh error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/logout", methods=["POST"])
@requires_auth
def logout():
    """
    Logout user and revoke refresh token
    
    Expected JSON payload:
    {
        "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        validated_data = refresh_token_schema.load(data)
        
        # Revoke token
        auth_service = AuthService()
        result = auth_service.revoke_refresh_token(validated_data["refresh_token"])
        
        return jsonify({
            "success": True,
            "message": "Logged out successfully"
        }), 200
    
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "Validation error",
            "details": e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Logout error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/me", methods=["GET"])
@requires_auth
def get_current_user():
    """Get current user information"""
    try:
        user = g.current_user
        return jsonify({
            "success": True,
            "user": user.to_dict()
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"Get current user error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/change-password", methods=["POST"])
@requires_auth
def change_password():
    """
    Change user password
    
    Expected JSON payload:
    {
        "old_password": "oldpassword123",
        "new_password": "newpassword123"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        validated_data = change_password_schema.load(data)
        
        # Change password
        auth_service = AuthService()
        result = auth_service.change_password(
            user_id=g.current_user.id,
            old_password=validated_data["old_password"],
            new_password=validated_data["new_password"]
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"],
                "details": result.get("details")
            }), 400
    
    except ValidationError as e:
        return jsonify({
            "success": False,
            "error": "Validation error",
            "details": e.messages
        }), 400
    
    except Exception as e:
        current_app.logger.error(f"Change password error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/users", methods=["GET"])
@requires_permission("users:read")
def list_users():
    """List all users (admin only)"""
    try:
        auth_service = AuthService()
        users = auth_service.db_session.query(User).all()
        
        return jsonify({
            "success": True,
            "users": [user.to_dict() for user in users]
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"List users error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/users/<int:user_id>/roles", methods=["POST"])
@requires_permission("users:write")
def assign_role(user_id):
    """
    Assign role to user (admin only)
    
    Expected JSON payload:
    {
        "role_name": "manager"
    }
    """
    try:
        # Validate request data
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        role_name = data.get("role_name")
        if not role_name:
            return jsonify({"error": "role_name is required"}), 400
        
        # Assign role
        auth_service = AuthService()
        result = auth_service.assign_role(
            user_id=user_id,
            role_name=role_name,
            assigned_by=g.current_user.id
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Assign role error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/users/<int:user_id>/roles/<role_name>", methods=["DELETE"])
@requires_permission("users:write")
def revoke_role(user_id, role_name):
    """Revoke role from user (admin only)"""
    try:
        # Revoke role
        auth_service = AuthService()
        result = auth_service.revoke_role(
            user_id=user_id,
            role_name=role_name
        )
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 400
    
    except Exception as e:
        current_app.logger.error(f"Revoke role error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/roles", methods=["GET"])
@requires_permission("users:read")
def list_roles():
    """List all roles (admin only)"""
    try:
        auth_service = AuthService()
        roles = auth_service.db_session.query(Role).all()
        
        return jsonify({
            "success": True,
            "roles": [role.to_dict() for role in roles]
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"List roles error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/permissions", methods=["GET"])
@requires_permission("users:read")
def list_permissions():
    """List all permissions (admin only)"""
    try:
        auth_service = AuthService()
        permissions = auth_service.db_session.query(Permission).all()
        
        return jsonify({
            "success": True,
            "permissions": [permission.to_dict() for permission in permissions]
        }), 200
    
    except Exception as e:
        current_app.logger.error(f"List permissions error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/init", methods=["POST"])
def initialize_auth():
    """Initialize default roles and permissions"""
    try:
        auth_service = AuthService()
        result = auth_service.initialize_default_roles_and_permissions()
        
        if result["success"]:
            return jsonify({
                "success": True,
                "message": result["message"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
    
    except Exception as e:
        current_app.logger.error(f"Initialize auth error: {str(e)}")
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500


@auth_bp.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint for authentication service"""
    return jsonify({
        "success": True,
        "message": "Authentication service is healthy",
        "timestamp": datetime.datetime.utcnow().isoformat()
    }), 200


# Error handlers
@auth_bp.errorhandler(400)
def bad_request(error):
    """Handle bad request errors"""
    return jsonify({
        "success": False,
        "error": "Bad request",
        "message": str(error)
    }), 400


@auth_bp.errorhandler(401)
def unauthorized(error):
    """Handle unauthorized errors"""
    return jsonify({
        "success": False,
        "error": "Unauthorized",
        "message": "Authentication required"
    }), 401


@auth_bp.errorhandler(403)
def forbidden(error):
    """Handle forbidden errors"""
    return jsonify({
        "success": False,
        "error": "Forbidden",
        "message": "Insufficient permissions"
    }), 403


@auth_bp.errorhandler(404)
def not_found(error):
    """Handle not found errors"""
    return jsonify({
        "success": False,
        "error": "Not found",
        "message": "Resource not found"
    }), 404


@auth_bp.errorhandler(500)
def internal_server_error(error):
    """Handle internal server errors"""
    current_app.logger.error(f"Internal server error: {str(error)}")
    return jsonify({
        "success": False,
        "error": "Internal server error",
        "message": "An unexpected error occurred"
    }), 500