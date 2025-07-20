"""
JWT Authentication implementation for enterprise security
"""
import datetime
import os
import jwt
from functools import wraps
from typing import Any, Dict, Optional, List
from flask import request, jsonify, current_app, g
from werkzeug.security import generate_password_hash, check_password_hash

from app.auth.models import User, Role, Permission


class JWTAuth:
    """JWT Authentication handler for enterprise security"""
    
    def __init__(self, app=None):
        """Initialize JWT authentication"""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize Flask app with JWT configuration"""
        jwt_secret = os.environ.get('JWT_SECRET_KEY')
        if not jwt_secret:
            raise ValueError("JWT_SECRET_KEY environment variable is required")
        app.config['JWT_SECRET_KEY'] = jwt_secret
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', datetime.timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', datetime.timedelta(days=30))
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        
        # Store JWT instance in app extensions
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['jwt'] = self
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate JWT access and refresh tokens for user"""
        now = datetime.datetime.utcnow()
        
        # Access token payload
        access_payload = {
            'user_id': user.id,
            'email': user.email,
            'roles': [role.name for role in user.roles],
            'permissions': self._get_user_permissions(user),
            'iat': now,
            'exp': now + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
            'type': 'access'
        }
        
        # Refresh token payload
        refresh_payload = {
            'user_id': user.id,
            'iat': now,
            'exp': now + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
            'type': 'refresh'
        }
        
        access_token = jwt.encode(
            access_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        refresh_token = jwt.encode(
            refresh_payload,
            current_app.config['JWT_SECRET_KEY'],
            algorithm=current_app.config['JWT_ALGORITHM']
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': current_app.config['JWT_ACCESS_TOKEN_EXPIRES'].total_seconds()
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            payload = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Refresh access token using refresh token"""
        payload = self.verify_token(refresh_token)
        if not payload or payload.get('type') != 'refresh':
            return None
        
        # Get user and generate new tokens
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
        
        return self.generate_tokens(user)
    
    def get_current_user(self) -> Optional[User]:
        """Get current authenticated user from request context"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return None
        except ValueError:
            return None
        
        payload = self.verify_token(token)
        if not payload or payload.get('type') != 'access':
            return None
        
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
        
        return user
    
    def _get_user_permissions(self, user: User) -> List[str]:
        """Get all permissions for a user"""
        permissions = set()
        for role in user.roles:
            for permission in role.permissions:
                permissions.add(permission.name)
        return list(permissions)


def requires_auth(f):
    """Decorator to require authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        jwt_auth = current_app.extensions.get('jwt')
        if not jwt_auth:
            return jsonify({'error': 'Authentication not configured'}), 500
        
        user = jwt_auth.get_current_user()
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        # Store user in Flask g for use in view functions
        g.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def requires_permission(permission_name: str):
    """Decorator to require specific permission for endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check authentication
            jwt_auth = current_app.extensions.get('jwt')
            if not jwt_auth:
                return jsonify({'error': 'Authentication not configured'}), 500
            
            user = jwt_auth.get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check permission
            user_permissions = jwt_auth._get_user_permissions(user)
            if permission_name not in user_permissions:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def requires_role(role_name: str):
    """Decorator to require specific role for endpoint"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            jwt_auth = current_app.extensions.get('jwt')
            if not jwt_auth:
                return jsonify({'error': 'Authentication not configured'}), 500
            
            user = jwt_auth.get_current_user()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
            
            # Check role
            user_roles = [role.name for role in user.roles]
            if role_name not in user_roles:
                return jsonify({'error': 'Insufficient role'}), 403
            
            g.current_user = user
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class PasswordManager:
    """Password management utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password for storage"""
        return generate_password_hash(password)
    
    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return check_password_hash(password_hash, password)
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password meets enterprise security requirements"""
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }