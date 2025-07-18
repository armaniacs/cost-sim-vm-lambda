"""
Authentication service for enterprise security management
"""
import datetime
import hashlib
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.auth.models import User, Role, Permission, RefreshToken, DEFAULT_PERMISSIONS, DEFAULT_ROLES
from app.auth.jwt_auth import PasswordManager, JWTAuth
from app.models.database import get_db_session


class AuthService:
    """Service for authentication and authorization operations"""
    
    def __init__(self, db_session: Optional[Session] = None):
        """Initialize authentication service"""
        self.db_session = db_session or get_db_session()
        self.jwt_auth = JWTAuth()
        self.password_manager = PasswordManager()
    
    def create_user(self, email: str, password: str, first_name: str = None, 
                   last_name: str = None, roles: List[str] = None) -> Dict[str, Any]:
        """Create a new user"""
        try:
            # Validate password strength
            password_validation = self.password_manager.validate_password_strength(password)
            if not password_validation['valid']:
                return {
                    'success': False,
                    'error': 'Password does not meet security requirements',
                    'details': password_validation['errors']
                }
            
            # Check if user already exists
            existing_user = self.db_session.query(User).filter_by(email=email).first()
            if existing_user:
                return {
                    'success': False,
                    'error': 'User with this email already exists'
                }
            
            # Create user
            user = User(
                email=email,
                password_hash=self.password_manager.hash_password(password),
                first_name=first_name,
                last_name=last_name,
                is_active=True,
                is_verified=False
            )
            
            # Assign roles
            if roles:
                user_roles = self.db_session.query(Role).filter(Role.name.in_(roles)).all()
                user.roles = user_roles
            else:
                # Assign default viewer role
                viewer_role = self.db_session.query(Role).filter_by(name='viewer').first()
                if viewer_role:
                    user.roles = [viewer_role]
            
            self.db_session.add(user)
            self.db_session.commit()
            
            return {
                'success': True,
                'user': user.to_dict(),
                'message': 'User created successfully'
            }
            
        except IntegrityError:
            self.db_session.rollback()
            return {
                'success': False,
                'error': 'User creation failed due to database constraint'
            }
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'User creation failed: {str(e)}'
            }
    
    def authenticate_user(self, email: str, password: str) -> Dict[str, Any]:
        """Authenticate user and generate tokens"""
        try:
            # Find user
            user = self.db_session.query(User).filter_by(email=email).first()
            if not user:
                return {
                    'success': False,
                    'error': 'Invalid credentials'
                }
            
            # Check if user is active
            if not user.is_active:
                return {
                    'success': False,
                    'error': 'Account is deactivated'
                }
            
            # Verify password
            if not self.password_manager.verify_password(password, user.password_hash):
                return {
                    'success': False,
                    'error': 'Invalid credentials'
                }
            
            # Update last login
            user.last_login = datetime.datetime.utcnow()
            self.db_session.commit()
            
            # Generate tokens
            tokens = self.jwt_auth.generate_tokens(user)
            
            # Store refresh token
            self._store_refresh_token(user.id, tokens['refresh_token'])
            
            return {
                'success': True,
                'user': user.to_dict(),
                'tokens': tokens,
                'message': 'Authentication successful'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Authentication failed: {str(e)}'
            }
    
    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            token_data = self.jwt_auth.verify_token(refresh_token)
            if not token_data or token_data.get('type') != 'refresh':
                return {
                    'success': False,
                    'error': 'Invalid refresh token'
                }
            
            # Check if refresh token exists in database
            token_hash = self._hash_token(refresh_token)
            stored_token = self.db_session.query(RefreshToken).filter_by(
                token_hash=token_hash,
                user_id=token_data['user_id']
            ).first()
            
            if not stored_token or not stored_token.is_valid():
                return {
                    'success': False,
                    'error': 'Refresh token expired or revoked'
                }
            
            # Get user
            user = self.db_session.query(User).get(token_data['user_id'])
            if not user or not user.is_active:
                return {
                    'success': False,
                    'error': 'User not found or deactivated'
                }
            
            # Generate new tokens
            new_tokens = self.jwt_auth.generate_tokens(user)
            
            # Revoke old refresh token and store new one
            stored_token.is_revoked = True
            self._store_refresh_token(user.id, new_tokens['refresh_token'])
            self.db_session.commit()
            
            return {
                'success': True,
                'tokens': new_tokens,
                'message': 'Token refreshed successfully'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Token refresh failed: {str(e)}'
            }
    
    def revoke_refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        """Revoke a refresh token"""
        try:
            token_hash = self._hash_token(refresh_token)
            stored_token = self.db_session.query(RefreshToken).filter_by(
                token_hash=token_hash
            ).first()
            
            if stored_token:
                stored_token.is_revoked = True
                self.db_session.commit()
            
            return {
                'success': True,
                'message': 'Token revoked successfully'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Token revocation failed: {str(e)}'
            }
    
    def change_password(self, user_id: int, old_password: str, new_password: str) -> Dict[str, Any]:
        """Change user password"""
        try:
            # Get user
            user = self.db_session.query(User).get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            # Verify old password
            if not self.password_manager.verify_password(old_password, user.password_hash):
                return {
                    'success': False,
                    'error': 'Current password is incorrect'
                }
            
            # Validate new password
            password_validation = self.password_manager.validate_password_strength(new_password)
            if not password_validation['valid']:
                return {
                    'success': False,
                    'error': 'New password does not meet security requirements',
                    'details': password_validation['errors']
                }
            
            # Update password
            user.password_hash = self.password_manager.hash_password(new_password)
            user.updated_at = datetime.datetime.utcnow()
            
            # Revoke all refresh tokens
            self.db_session.query(RefreshToken).filter_by(
                user_id=user_id,
                is_revoked=False
            ).update({'is_revoked': True})
            
            self.db_session.commit()
            
            return {
                'success': True,
                'message': 'Password changed successfully'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Password change failed: {str(e)}'
            }
    
    def assign_role(self, user_id: int, role_name: str, assigned_by: int = None) -> Dict[str, Any]:
        """Assign role to user"""
        try:
            user = self.db_session.query(User).get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            role = self.db_session.query(Role).filter_by(name=role_name).first()
            if not role:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            # Check if user already has this role
            if role in user.roles:
                return {
                    'success': False,
                    'error': 'User already has this role'
                }
            
            user.roles.append(role)
            self.db_session.commit()
            
            return {
                'success': True,
                'message': f'Role {role_name} assigned to user'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Role assignment failed: {str(e)}'
            }
    
    def revoke_role(self, user_id: int, role_name: str) -> Dict[str, Any]:
        """Revoke role from user"""
        try:
            user = self.db_session.query(User).get(user_id)
            if not user:
                return {
                    'success': False,
                    'error': 'User not found'
                }
            
            role = self.db_session.query(Role).filter_by(name=role_name).first()
            if not role:
                return {
                    'success': False,
                    'error': 'Role not found'
                }
            
            # Check if user has this role
            if role not in user.roles:
                return {
                    'success': False,
                    'error': 'User does not have this role'
                }
            
            user.roles.remove(role)
            self.db_session.commit()
            
            return {
                'success': True,
                'message': f'Role {role_name} revoked from user'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Role revocation failed: {str(e)}'
            }
    
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db_session.query(User).get(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db_session.query(User).filter_by(email=email).first()
    
    def initialize_default_roles_and_permissions(self) -> Dict[str, Any]:
        """Initialize default roles and permissions"""
        try:
            # Create permissions
            for perm_name, description, resource, action in DEFAULT_PERMISSIONS:
                existing_perm = self.db_session.query(Permission).filter_by(name=perm_name).first()
                if not existing_perm:
                    permission = Permission(
                        name=perm_name,
                        description=description,
                        resource=resource,
                        action=action
                    )
                    self.db_session.add(permission)
            
            # Create roles
            for role_name, description, permissions in DEFAULT_ROLES:
                existing_role = self.db_session.query(Role).filter_by(name=role_name).first()
                if not existing_role:
                    role = Role(
                        name=role_name,
                        description=description
                    )
                    
                    # Add permissions to role
                    role_permissions = self.db_session.query(Permission).filter(
                        Permission.name.in_(permissions)
                    ).all()
                    role.permissions = role_permissions
                    
                    self.db_session.add(role)
            
            self.db_session.commit()
            
            return {
                'success': True,
                'message': 'Default roles and permissions initialized'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Initialization failed: {str(e)}'
            }
    
    def _store_refresh_token(self, user_id: int, refresh_token: str) -> None:
        """Store refresh token in database"""
        token_hash = self._hash_token(refresh_token)
        expires_at = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        
        refresh_token_obj = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
        
        self.db_session.add(refresh_token_obj)
    
    def _hash_token(self, token: str) -> str:
        """Hash token for storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    def cleanup_expired_tokens(self) -> Dict[str, Any]:
        """Clean up expired refresh tokens"""
        try:
            expired_count = self.db_session.query(RefreshToken).filter(
                RefreshToken.expires_at < datetime.datetime.utcnow()
            ).delete()
            
            self.db_session.commit()
            
            return {
                'success': True,
                'message': f'Cleaned up {expired_count} expired tokens'
            }
            
        except Exception as e:
            self.db_session.rollback()
            return {
                'success': False,
                'error': f'Token cleanup failed: {str(e)}'
            }