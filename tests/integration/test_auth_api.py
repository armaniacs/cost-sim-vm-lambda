"""
Integration tests for authentication API endpoints
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from flask import Flask

from app.main import create_app
from app.auth.models import User, Role, Permission


class TestAuthenticationAPI:
    """Test suite for authentication API endpoints"""

    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['JWT_SECRET_KEY'] = 'test-secret-key'
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()

    @pytest.fixture
    def mock_auth_service(self):
        """Mock authentication service"""
        with patch('app.api.auth_api.AuthService') as mock_service:
            yield mock_service

    def test_login_success(self, client, mock_auth_service):
        """Test successful login"""
        # Mock successful authentication
        mock_service_instance = Mock()
        mock_service_instance.authenticate_user.return_value = {
            'success': True,
            'message': 'Authentication successful',
            'user': {
                'id': 1,
                'email': 'test@example.com',
                'first_name': 'John',
                'last_name': 'Doe'
            },
            'tokens': {
                'access_token': 'access_token',
                'refresh_token': 'refresh_token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        }
        mock_auth_service.return_value = mock_service_instance

        # Test login request
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert 'tokens' in data
        assert data['user']['email'] == 'test@example.com'
        assert data['tokens']['access_token'] == 'access_token'

    def test_login_invalid_credentials(self, client, mock_auth_service):
        """Test login with invalid credentials"""
        # Mock failed authentication
        mock_service_instance = Mock()
        mock_service_instance.authenticate_user.return_value = {
            'success': False,
            'error': 'Invalid credentials'
        }
        mock_auth_service.return_value = mock_service_instance

        # Test login request
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com',
            'password': 'wrong_password'
        })

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Invalid credentials'

    def test_login_validation_error(self, client):
        """Test login with validation errors"""
        # Test with invalid email
        response = client.post('/api/v1/auth/login', json={
            'email': 'invalid_email',
            'password': 'password123'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Validation error'

    def test_login_missing_data(self, client):
        """Test login with missing data"""
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com'
            # Missing password
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Validation error'

    def test_register_success(self, client, mock_auth_service):
        """Test successful user registration"""
        # Mock successful user creation
        mock_service_instance = Mock()
        mock_service_instance.create_user.return_value = {
            'success': True,
            'message': 'User created successfully',
            'user': {
                'id': 1,
                'email': 'new@example.com',
                'first_name': 'John',
                'last_name': 'Doe'
            }
        }
        mock_auth_service.return_value = mock_service_instance

        # Test registration request
        response = client.post('/api/v1/auth/register', json={
            'email': 'new@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'John',
            'last_name': 'Doe'
        })

        assert response.status_code == 201
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'user' in data
        assert data['user']['email'] == 'new@example.com'

    def test_register_existing_user(self, client, mock_auth_service):
        """Test registration with existing user"""
        # Mock user already exists
        mock_service_instance = Mock()
        mock_service_instance.create_user.return_value = {
            'success': False,
            'error': 'User with this email already exists'
        }
        mock_auth_service.return_value = mock_service_instance

        # Test registration request
        response = client.post('/api/v1/auth/register', json={
            'email': 'existing@example.com',
            'password': 'StrongPassword123!'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'User with this email already exists'

    def test_register_weak_password(self, client, mock_auth_service):
        """Test registration with weak password"""
        # Mock weak password error
        mock_service_instance = Mock()
        mock_service_instance.create_user.return_value = {
            'success': False,
            'error': 'Password does not meet security requirements',
            'details': ['Password must be at least 8 characters long']
        }
        mock_auth_service.return_value = mock_service_instance

        # Test registration request
        response = client.post('/api/v1/auth/register', json={
            'email': 'new@example.com',
            'password': 'weak'
        })

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Password does not meet security requirements'
        assert 'details' in data

    def test_refresh_token_success(self, client, mock_auth_service):
        """Test successful token refresh"""
        # Mock successful token refresh
        mock_service_instance = Mock()
        mock_service_instance.refresh_access_token.return_value = {
            'success': True,
            'message': 'Token refreshed successfully',
            'tokens': {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
                'token_type': 'Bearer',
                'expires_in': 3600
            }
        }
        mock_auth_service.return_value = mock_service_instance

        # Test refresh request
        response = client.post('/api/v1/auth/refresh', json={
            'refresh_token': 'valid_refresh_token'
        })

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'tokens' in data
        assert data['tokens']['access_token'] == 'new_access_token'

    def test_refresh_token_invalid(self, client, mock_auth_service):
        """Test token refresh with invalid token"""
        # Mock invalid token
        mock_service_instance = Mock()
        mock_service_instance.refresh_access_token.return_value = {
            'success': False,
            'error': 'Invalid refresh token'
        }
        mock_auth_service.return_value = mock_service_instance

        # Test refresh request
        response = client.post('/api/v1/auth/refresh', json={
            'refresh_token': 'invalid_refresh_token'
        })

        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Invalid refresh token'

    def test_logout_success(self, client, mock_auth_service):
        """Test successful logout"""
        # Mock authentication and logout
        mock_service_instance = Mock()
        mock_service_instance.revoke_refresh_token.return_value = {
            'success': True,
            'message': 'Token revoked successfully'
        }
        mock_auth_service.return_value = mock_service_instance

        # Mock JWT authentication
        with patch('app.api.auth_api.requires_auth') as mock_requires_auth:
            mock_requires_auth.return_value = lambda f: f  # Pass through decorator
            
            # Test logout request
            response = client.post('/api/v1/auth/logout', json={
                'refresh_token': 'valid_refresh_token'
            })

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'Logged out successfully'

    def test_get_current_user_success(self, client):
        """Test getting current user information"""
        # Mock user object
        mock_user = Mock()
        mock_user.to_dict.return_value = {
            'id': 1,
            'email': 'test@example.com',
            'first_name': 'John',
            'last_name': 'Doe'
        }

        # Mock JWT authentication
        with patch('app.api.auth_api.requires_auth') as mock_requires_auth:
            mock_requires_auth.return_value = lambda f: f  # Pass through decorator
            
            with patch('app.api.auth_api.g') as mock_g:
                mock_g.current_user = mock_user
                
                # Test get current user request
                response = client.get('/api/v1/auth/me')

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert 'user' in data
                assert data['user']['email'] == 'test@example.com'

    def test_change_password_success(self, client, mock_auth_service):
        """Test successful password change"""
        # Mock successful password change
        mock_service_instance = Mock()
        mock_service_instance.change_password.return_value = {
            'success': True,
            'message': 'Password changed successfully'
        }
        mock_auth_service.return_value = mock_service_instance

        # Mock JWT authentication
        with patch('app.api.auth_api.requires_auth') as mock_requires_auth:
            mock_requires_auth.return_value = lambda f: f  # Pass through decorator
            
            with patch('app.api.auth_api.g') as mock_g:
                mock_g.current_user = Mock(id=1)
                
                # Test change password request
                response = client.post('/api/v1/auth/change-password', json={
                    'old_password': 'old_password',
                    'new_password': 'NewPassword123!'
                })

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['message'] == 'Password changed successfully'

    def test_change_password_wrong_old_password(self, client, mock_auth_service):
        """Test password change with wrong old password"""
        # Mock wrong old password
        mock_service_instance = Mock()
        mock_service_instance.change_password.return_value = {
            'success': False,
            'error': 'Current password is incorrect'
        }
        mock_auth_service.return_value = mock_service_instance

        # Mock JWT authentication
        with patch('app.api.auth_api.requires_auth') as mock_requires_auth:
            mock_requires_auth.return_value = lambda f: f  # Pass through decorator
            
            with patch('app.api.auth_api.g') as mock_g:
                mock_g.current_user = Mock(id=1)
                
                # Test change password request
                response = client.post('/api/v1/auth/change-password', json={
                    'old_password': 'wrong_password',
                    'new_password': 'NewPassword123!'
                })

                assert response.status_code == 400
                data = json.loads(response.data)
                assert data['success'] is False
                assert data['error'] == 'Current password is incorrect'

    def test_assign_role_success(self, client, mock_auth_service):
        """Test successful role assignment"""
        # Mock successful role assignment
        mock_service_instance = Mock()
        mock_service_instance.assign_role.return_value = {
            'success': True,
            'message': 'Role manager assigned to user'
        }
        mock_auth_service.return_value = mock_service_instance

        # Mock JWT authentication with permission
        with patch('app.api.auth_api.requires_permission') as mock_requires_permission:
            mock_requires_permission.return_value = lambda f: f  # Pass through decorator
            
            with patch('app.api.auth_api.g') as mock_g:
                mock_g.current_user = Mock(id=1)
                
                # Test assign role request
                response = client.post('/api/v1/auth/users/2/roles', json={
                    'role_name': 'manager'
                })

                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                assert data['message'] == 'Role manager assigned to user'

    def test_revoke_role_success(self, client, mock_auth_service):
        """Test successful role revocation"""
        # Mock successful role revocation
        mock_service_instance = Mock()
        mock_service_instance.revoke_role.return_value = {
            'success': True,
            'message': 'Role manager revoked from user'
        }
        mock_auth_service.return_value = mock_service_instance

        # Mock JWT authentication with permission
        with patch('app.api.auth_api.requires_permission') as mock_requires_permission:
            mock_requires_permission.return_value = lambda f: f  # Pass through decorator
            
            # Test revoke role request
            response = client.delete('/api/v1/auth/users/2/roles/manager')

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['message'] == 'Role manager revoked from user'

    def test_initialize_auth_success(self, client, mock_auth_service):
        """Test successful authentication initialization"""
        # Mock successful initialization
        mock_service_instance = Mock()
        mock_service_instance.initialize_default_roles_and_permissions.return_value = {
            'success': True,
            'message': 'Default roles and permissions initialized'
        }
        mock_auth_service.return_value = mock_service_instance

        # Test initialization request
        response = client.post('/api/v1/auth/init')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Default roles and permissions initialized'

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get('/api/v1/auth/health')

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['success'] is True
        assert data['message'] == 'Authentication service is healthy'
        assert 'timestamp' in data

    def test_invalid_json_request(self, client):
        """Test request with invalid JSON"""
        response = client.post('/api/v1/auth/login', 
                             data='invalid json',
                             content_type='application/json')

        assert response.status_code == 400

    def test_missing_json_request(self, client):
        """Test request with missing JSON data"""
        response = client.post('/api/v1/auth/login')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['error'] == 'No JSON data provided'

    def test_internal_server_error(self, client, mock_auth_service):
        """Test internal server error handling"""
        # Mock service exception
        mock_service_instance = Mock()
        mock_service_instance.authenticate_user.side_effect = Exception('Database error')
        mock_auth_service.return_value = mock_service_instance

        # Test login request
        response = client.post('/api/v1/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })

        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['success'] is False
        assert data['error'] == 'Internal server error'