"""
Unit tests for authentication service
"""
import pytest
import datetime
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session

from app.auth.service import AuthService
from app.auth.models import User, Role, Permission
from app.auth.jwt_auth import PasswordManager


class TestAuthService:
    """Test suite for AuthService"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        return Mock(spec=Session)

    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create AuthService instance with mocked dependencies"""
        with patch('app.auth.service.get_db_session', return_value=mock_db_session):
            service = AuthService()
            service.db_session = mock_db_session
            return service

    def test_create_user_success(self, auth_service, mock_db_session):
        """Test successful user creation"""
        # Mock password validation
        with patch.object(PasswordManager, 'validate_password_strength') as mock_validate:
            mock_validate.return_value = {'valid': True, 'errors': []}
            
            # Mock password hashing
            with patch.object(PasswordManager, 'hash_password') as mock_hash:
                mock_hash.return_value = 'hashed_password'
                
                # Mock database queries
                mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
                mock_viewer_role = Mock(spec=Role)
                mock_viewer_role.name = 'viewer'
                mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_viewer_role
                
                # Test user creation
                result = auth_service.create_user(
                    email='test@example.com',
                    password='ValidPassword123!',
                    first_name='John',
                    last_name='Doe'
                )
                
                assert result['success'] is True
                assert 'user' in result
                assert result['message'] == 'User created successfully'
                mock_db_session.add.assert_called_once()
                mock_db_session.commit.assert_called_once()

    def test_create_user_weak_password(self, auth_service):
        """Test user creation with weak password"""
        with patch.object(PasswordManager, 'validate_password_strength') as mock_validate:
            mock_validate.return_value = {
                'valid': False,
                'errors': ['Password too weak']
            }
            
            result = auth_service.create_user(
                email='test@example.com',
                password='weak'
            )
            
            assert result['success'] is False
            assert result['error'] == 'Password does not meet security requirements'
            assert 'details' in result

    def test_create_user_existing_email(self, auth_service, mock_db_session):
        """Test user creation with existing email"""
        with patch.object(PasswordManager, 'validate_password_strength') as mock_validate:
            mock_validate.return_value = {'valid': True, 'errors': []}
            
            # Mock existing user
            existing_user = Mock(spec=User)
            mock_db_session.query.return_value.filter_by.return_value.first.return_value = existing_user
            
            result = auth_service.create_user(
                email='existing@example.com',
                password='ValidPassword123!'
            )
            
            assert result['success'] is False
            assert result['error'] == 'User with this email already exists'

    def test_authenticate_user_success(self, auth_service, mock_db_session):
        """Test successful user authentication"""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.email = 'test@example.com'
        mock_user.is_active = True
        mock_user.password_hash = 'hashed_password'
        mock_user.to_dict.return_value = {'id': 1, 'email': 'test@example.com'}
        
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock password verification
        with patch.object(PasswordManager, 'verify_password') as mock_verify:
            mock_verify.return_value = True
            
            # Mock JWT token generation
            mock_tokens = {
                'access_token': 'access_token',
                'refresh_token': 'refresh_token'
            }
            with patch.object(auth_service.jwt_auth, 'generate_tokens') as mock_generate:
                mock_generate.return_value = mock_tokens
                
                # Mock token storage
                with patch.object(auth_service, '_store_refresh_token'):
                    result = auth_service.authenticate_user(
                        email='test@example.com',
                        password='password'
                    )
                    
                    assert result['success'] is True
                    assert 'user' in result
                    assert 'tokens' in result
                    assert result['tokens'] == mock_tokens
                    mock_db_session.commit.assert_called_once()

    def test_authenticate_user_invalid_credentials(self, auth_service, mock_db_session):
        """Test authentication with invalid credentials"""
        # Mock user not found
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        
        result = auth_service.authenticate_user(
            email='nonexistent@example.com',
            password='password'
        )
        
        assert result['success'] is False
        assert result['error'] == 'Invalid credentials'

    def test_authenticate_user_inactive_account(self, auth_service, mock_db_session):
        """Test authentication with inactive account"""
        # Mock inactive user
        mock_user = Mock(spec=User)
        mock_user.is_active = False
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        result = auth_service.authenticate_user(
            email='inactive@example.com',
            password='password'
        )
        
        assert result['success'] is False
        assert result['error'] == 'Account is deactivated'

    def test_authenticate_user_wrong_password(self, auth_service, mock_db_session):
        """Test authentication with wrong password"""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.is_active = True
        mock_user.password_hash = 'hashed_password'
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_user
        
        # Mock password verification failure
        with patch.object(PasswordManager, 'verify_password') as mock_verify:
            mock_verify.return_value = False
            
            result = auth_service.authenticate_user(
                email='test@example.com',
                password='wrong_password'
            )
            
            assert result['success'] is False
            assert result['error'] == 'Invalid credentials'

    def test_refresh_access_token_success(self, auth_service, mock_db_session):
        """Test successful token refresh"""
        # Mock token verification
        mock_token_data = {
            'user_id': 1,
            'type': 'refresh'
        }
        with patch.object(auth_service.jwt_auth, 'verify_token') as mock_verify:
            mock_verify.return_value = mock_token_data
            
            # Mock stored token
            from app.auth.models import RefreshToken
            mock_stored_token = Mock(spec=RefreshToken)
            mock_stored_token.is_valid.return_value = True
            mock_stored_token.is_revoked = False
            mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_stored_token
            
            # Mock user
            mock_user = Mock(spec=User)
            mock_user.id = 1
            mock_user.is_active = True
            mock_db_session.query.return_value.get.return_value = mock_user
            
            # Mock new token generation
            mock_new_tokens = {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token'
            }
            with patch.object(auth_service.jwt_auth, 'generate_tokens') as mock_generate:
                mock_generate.return_value = mock_new_tokens
                
                # Mock token storage
                with patch.object(auth_service, '_store_refresh_token'):
                    with patch.object(auth_service, '_hash_token'):
                        result = auth_service.refresh_access_token('refresh_token')
                        
                        assert result['success'] is True
                        assert 'tokens' in result
                        assert result['tokens'] == mock_new_tokens
                        assert mock_stored_token.is_revoked is True
                        mock_db_session.commit.assert_called_once()

    def test_refresh_access_token_invalid_token(self, auth_service):
        """Test token refresh with invalid token"""
        # Mock token verification failure
        with patch.object(auth_service.jwt_auth, 'verify_token') as mock_verify:
            mock_verify.return_value = None
            
            result = auth_service.refresh_access_token('invalid_token')
            
            assert result['success'] is False
            assert result['error'] == 'Invalid refresh token'

    def test_change_password_success(self, auth_service, mock_db_session):
        """Test successful password change"""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.password_hash = 'old_hashed_password'
        mock_db_session.query.return_value.get.return_value = mock_user
        
        # Mock password verification and hashing
        with patch.object(PasswordManager, 'verify_password') as mock_verify:
            mock_verify.return_value = True
            
            with patch.object(PasswordManager, 'validate_password_strength') as mock_validate:
                mock_validate.return_value = {'valid': True, 'errors': []}
                
                with patch.object(PasswordManager, 'hash_password') as mock_hash:
                    mock_hash.return_value = 'new_hashed_password'
                    
                    result = auth_service.change_password(
                        user_id=1,
                        old_password='old_password',
                        new_password='NewPassword123!'
                    )
                    
                    assert result['success'] is True
                    assert result['message'] == 'Password changed successfully'
                    assert mock_user.password_hash == 'new_hashed_password'
                    mock_db_session.commit.assert_called_once()

    def test_change_password_wrong_old_password(self, auth_service, mock_db_session):
        """Test password change with wrong old password"""
        # Mock user
        mock_user = Mock(spec=User)
        mock_user.password_hash = 'old_hashed_password'
        mock_db_session.query.return_value.get.return_value = mock_user
        
        # Mock password verification failure
        with patch.object(PasswordManager, 'verify_password') as mock_verify:
            mock_verify.return_value = False
            
            result = auth_service.change_password(
                user_id=1,
                old_password='wrong_password',
                new_password='NewPassword123!'
            )
            
            assert result['success'] is False
            assert result['error'] == 'Current password is incorrect'

    def test_assign_role_success(self, auth_service, mock_db_session):
        """Test successful role assignment"""
        # Mock user and role
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.roles = []
        mock_db_session.query.return_value.get.return_value = mock_user
        
        mock_role = Mock(spec=Role)
        mock_role.name = 'manager'
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_role
        
        result = auth_service.assign_role(
            user_id=1,
            role_name='manager'
        )
        
        assert result['success'] is True
        assert result['message'] == 'Role manager assigned to user'
        assert mock_role in mock_user.roles
        mock_db_session.commit.assert_called_once()

    def test_assign_role_already_has_role(self, auth_service, mock_db_session):
        """Test role assignment when user already has role"""
        # Mock user and role
        mock_role = Mock(spec=Role)
        mock_role.name = 'manager'
        
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.roles = [mock_role]
        mock_db_session.query.return_value.get.return_value = mock_user
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_role
        
        result = auth_service.assign_role(
            user_id=1,
            role_name='manager'
        )
        
        assert result['success'] is False
        assert result['error'] == 'User already has this role'

    def test_revoke_role_success(self, auth_service, mock_db_session):
        """Test successful role revocation"""
        # Mock user and role
        mock_role = Mock(spec=Role)
        mock_role.name = 'manager'
        
        mock_user = Mock(spec=User)
        mock_user.id = 1
        mock_user.roles = [mock_role]
        mock_db_session.query.return_value.get.return_value = mock_user
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = mock_role
        
        result = auth_service.revoke_role(
            user_id=1,
            role_name='manager'
        )
        
        assert result['success'] is True
        assert result['message'] == 'Role manager revoked from user'
        mock_user.roles.remove.assert_called_once_with(mock_role)
        mock_db_session.commit.assert_called_once()

    def test_initialize_default_roles_and_permissions(self, auth_service, mock_db_session):
        """Test initialization of default roles and permissions"""
        # Mock queries to return no existing roles/permissions
        mock_db_session.query.return_value.filter_by.return_value.first.return_value = None
        mock_db_session.query.return_value.filter.return_value.all.return_value = []
        
        result = auth_service.initialize_default_roles_and_permissions()
        
        assert result['success'] is True
        assert result['message'] == 'Default roles and permissions initialized'
        
        # Verify that permissions and roles were added
        assert mock_db_session.add.call_count > 0
        mock_db_session.commit.assert_called_once()

    def test_cleanup_expired_tokens(self, auth_service, mock_db_session):
        """Test cleanup of expired tokens"""
        # Mock query for expired tokens
        mock_query = mock_db_session.query.return_value.filter.return_value
        mock_query.delete.return_value = 5  # 5 expired tokens deleted
        
        result = auth_service.cleanup_expired_tokens()
        
        assert result['success'] is True
        assert result['message'] == 'Cleaned up 5 expired tokens'
        mock_db_session.commit.assert_called_once()


class TestPasswordManager:
    """Test suite for PasswordManager"""

    def test_hash_password(self):
        """Test password hashing"""
        password = 'test_password'
        hashed = PasswordManager.hash_password(password)
        
        assert hashed != password
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_success(self):
        """Test successful password verification"""
        password = 'test_password'
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test failed password verification"""
        password = 'test_password'
        wrong_password = 'wrong_password'
        hashed = PasswordManager.hash_password(password)
        
        assert PasswordManager.verify_password(wrong_password, hashed) is False

    def test_validate_password_strength_valid(self):
        """Test validation of strong password"""
        strong_password = 'StrongPassword123!'
        result = PasswordManager.validate_password_strength(strong_password)
        
        assert result['valid'] is True
        assert result['errors'] == []

    def test_validate_password_strength_too_short(self):
        """Test validation of too short password"""
        short_password = 'Aa1!'
        result = PasswordManager.validate_password_strength(short_password)
        
        assert result['valid'] is False
        assert 'Password must be at least 8 characters long' in result['errors']

    def test_validate_password_strength_missing_uppercase(self):
        """Test validation of password missing uppercase"""
        password = 'password123!'
        result = PasswordManager.validate_password_strength(password)
        
        assert result['valid'] is False
        assert 'Password must contain at least one uppercase letter' in result['errors']

    def test_validate_password_strength_missing_lowercase(self):
        """Test validation of password missing lowercase"""
        password = 'PASSWORD123!'
        result = PasswordManager.validate_password_strength(password)
        
        assert result['valid'] is False
        assert 'Password must contain at least one lowercase letter' in result['errors']

    def test_validate_password_strength_missing_digit(self):
        """Test validation of password missing digit"""
        password = 'Password!'
        result = PasswordManager.validate_password_strength(password)
        
        assert result['valid'] is False
        assert 'Password must contain at least one digit' in result['errors']

    def test_validate_password_strength_missing_special_char(self):
        """Test validation of password missing special character"""
        password = 'Password123'
        result = PasswordManager.validate_password_strength(password)
        
        assert result['valid'] is False
        assert 'Password must contain at least one special character' in result['errors']

    def test_validate_password_strength_multiple_errors(self):
        """Test validation of weak password with multiple errors"""
        weak_password = 'weak'
        result = PasswordManager.validate_password_strength(weak_password)
        
        assert result['valid'] is False
        assert len(result['errors']) > 1
        assert 'Password must be at least 8 characters long' in result['errors']
        assert 'Password must contain at least one uppercase letter' in result['errors']
        assert 'Password must contain at least one digit' in result['errors']
        assert 'Password must contain at least one special character' in result['errors']