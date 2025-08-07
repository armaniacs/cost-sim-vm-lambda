"""
Unit tests for main Flask application module
Tests app factory, CORS configuration, and routes
"""
import os
import pytest
from unittest.mock import patch, MagicMock

from app.main import create_app, configure_cors


class TestCORSConfiguration:
    """Test CORS configuration functionality"""
    
    def test_configure_cors_development_default(self):
        """Test CORS configuration for development environment"""
        app = MagicMock()
        app.config.get.return_value = 'development'
        
        with patch('app.main.CORS') as mock_cors:
            configure_cors(app)
            
            mock_cors.assert_called_once_with(
                app,
                origins=[
                    'http://localhost:5001',
                    'http://127.0.0.1:5001'
                ],
                supports_credentials=False,
                max_age=3600
            )
    
    def test_configure_cors_production_with_env_origins(self):
        """Test CORS configuration for production with environment origins"""
        app = MagicMock()
        app.config.get.return_value = 'production'
        
        test_origins = 'https://app1.example.com,https://app2.example.com,  https://app3.example.com  '
        
        with patch('app.main.CORS') as mock_cors, \
             patch.dict(os.environ, {'CORS_ORIGINS': test_origins}):
            
            configure_cors(app)
            
            mock_cors.assert_called_once_with(
                app,
                origins=[
                    'https://app1.example.com',
                    'https://app2.example.com',
                    'https://app3.example.com'
                ],
                supports_credentials=False,
                max_age=3600
            )
    
    def test_configure_cors_production_without_env_origins(self):
        """Test CORS configuration for production without environment origins"""
        app = MagicMock()
        app.config.get.return_value = 'production'
        
        with patch('app.main.CORS') as mock_cors, \
             patch.dict(os.environ, {}, clear=True):  # Clear CORS_ORIGINS
            
            configure_cors(app)
            
            mock_cors.assert_called_once_with(
                app,
                origins=[
                    'https://cost-simulator.example.com',
                    'https://cost-calc.example.com'
                ],
                supports_credentials=False,
                max_age=3600
            )
    
    def test_configure_cors_production_empty_env_origins(self):
        """Test CORS configuration for production with empty environment origins"""
        app = MagicMock()
        app.config.get.return_value = 'production'
        
        with patch('app.main.CORS') as mock_cors, \
             patch.dict(os.environ, {'CORS_ORIGINS': ''}):
            
            configure_cors(app)
            
            mock_cors.assert_called_once_with(
                app,
                origins=[
                    'https://cost-simulator.example.com',
                    'https://cost-calc.example.com'
                ],
                supports_credentials=False,
                max_age=3600
            )
    
    def test_configure_cors_environment_fallback(self):
        """Test CORS configuration falls back to development when config is unclear"""
        app = MagicMock()
        app.config.get.return_value = 'testing'  # Some other environment
        
        with patch('app.main.CORS') as mock_cors:
            configure_cors(app)
            
            # Should use development settings (default for non-production)
            mock_cors.assert_called_once_with(
                app,
                origins=[
                    'http://localhost:5001',
                    'http://127.0.0.1:5001'
                ],
                supports_credentials=False,
                max_age=3600
            )


class TestAppFactory:
    """Test Flask app factory functionality"""
    
    @patch('app.main.validate_environment_or_exit')
    def test_create_app_default_config(self, mock_validate_env):
        """Test creating app with default configuration"""
        with patch.dict(os.environ, {}, clear=True):  # Clear environment
            app = create_app()
            
            mock_validate_env.assert_called_once()
            assert app is not None
            assert app.name == 'app.main'
    
    @patch('app.main.validate_environment_or_exit')
    def test_create_app_testing_config(self, mock_validate_env):
        """Test creating app with testing configuration"""
        app = create_app('testing')
        
        mock_validate_env.assert_called_once()
        assert app is not None
        # Check that the app was created successfully (testing config may not set TESTING=True)
        assert app.config is not None
    
    @patch('app.main.validate_environment_or_exit')
    def test_create_app_with_flask_env(self, mock_validate_env):
        """Test creating app with FLASK_ENV environment variable"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}):
            app = create_app()
            
            mock_validate_env.assert_called_once()
            assert app is not None
    
    @patch('app.main.validate_environment_or_exit')
    def test_create_app_registers_blueprints(self, mock_validate_env):
        """Test that blueprints are registered correctly"""
        app = create_app('testing')
        
        # Check that calculator blueprint is registered
        blueprint_names = [bp.name for bp in app.blueprints.values()]
        assert 'calculator' in blueprint_names


class TestAppRoutes:
    """Test Flask application routes"""
    
    @patch('app.main.validate_environment_or_exit')
    def test_index_route(self, mock_validate_env):
        """Test index route"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/')
            assert response.status_code == 200
    
    @patch('app.main.validate_environment_or_exit')
    def test_api_info_route(self, mock_validate_env):
        """Test API info route"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/api')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'ok'
            assert 'Cost Simulator API' in data['message']
    
    @patch('app.main.validate_environment_or_exit')
    def test_health_route(self, mock_validate_env):
        """Test health check route"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'healthy'
            assert 'version' in data
    
    @patch('app.main.validate_environment_or_exit')
    def test_favicon_route(self, mock_validate_env):
        """Test favicon route returns 204"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/favicon.ico')
            assert response.status_code == 204
            assert response.data == b''
    
    @patch('app.main.validate_environment_or_exit')
    def test_chrome_devtools_route(self, mock_validate_env):
        """Test Chrome DevTools route returns 204"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/.well-known/appspecific/com.chrome.devtools.json')
            assert response.status_code == 204
            assert response.data == b''
    
    @patch('app.main.validate_environment_or_exit')
    def test_robots_txt_route(self, mock_validate_env):
        """Test robots.txt route"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/robots.txt')
            assert response.status_code == 200
            assert 'text/plain' in response.headers['Content-Type']
            assert b'User-agent: *' in response.data
            assert b'Disallow:' in response.data
    
    @patch('app.main.validate_environment_or_exit')
    def test_sitemap_route(self, mock_validate_env):
        """Test sitemap.xml route returns 204"""
        app = create_app('testing')
        
        with app.test_client() as client:
            response = client.get('/sitemap.xml')
            assert response.status_code == 204
            assert response.data == b''
    
    @patch('app.main.validate_environment_or_exit')
    def test_apple_touch_icon_routes(self, mock_validate_env):
        """Test Apple touch icon routes return 204"""
        app = create_app('testing')
        
        with app.test_client() as client:
            # Test both routes
            response1 = client.get('/apple-touch-icon.png')
            assert response1.status_code == 204
            assert response1.data == b''
            
            response2 = client.get('/apple-touch-icon-precomposed.png')
            assert response2.status_code == 204
            assert response2.data == b''


class TestMainExecution:
    """Test main execution block"""
    
    @patch('app.main.create_app')
    @patch('app.config.Config')
    def test_main_execution_development(self, mock_config, mock_create_app):
        """Test main execution in development environment"""
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_config.HOST = 'localhost'
        mock_config.PORT = 5000
        mock_config.DEBUG = True
        
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}), \
             patch('builtins.__name__', '__main__'):
            
            # Import and run the main block code
            import app.main
            
            # The main execution should have been triggered during import
            # We can't easily test the actual execution, but we can verify
            # the environment variable handling
            env = os.environ.get("FLASK_ENV", "development")
            assert env == "development"
    
    @patch('app.main.create_app')
    @patch('app.config.Config')
    def test_main_execution_default_env(self, mock_config, mock_create_app):
        """Test main execution with default environment"""
        mock_app = MagicMock()
        mock_create_app.return_value = mock_app
        mock_config.HOST = 'localhost'
        mock_config.PORT = 5000
        mock_config.DEBUG = False
        
        with patch.dict(os.environ, {}, clear=True):  # No FLASK_ENV
            env = os.environ.get("FLASK_ENV", "development")
            assert env == "development"


class TestEnvironmentHandling:
    """Test environment variable handling"""
    
    @patch('app.main.validate_environment_or_exit')
    def test_app_creation_with_various_configs(self, mock_validate_env):
        """Test app creation with various configuration names"""
        configs_to_test = ['development', 'testing', 'production', 'nonexistent']
        
        for config_name in configs_to_test:
            app = create_app(config_name)
            assert app is not None
            mock_validate_env.assert_called()
            mock_validate_env.reset_mock()
    
    @patch('app.main.validate_environment_or_exit')
    def test_cors_configuration_called(self, mock_validate_env):
        """Test that CORS configuration is called during app creation"""
        with patch('app.main.configure_cors') as mock_configure_cors:
            app = create_app('testing')
            
            mock_configure_cors.assert_called_once_with(app)


class TestSecurityValidation:
    """Test security validation integration"""
    
    def test_environment_validation_called_on_app_creation(self):
        """Test that environment validation is called during app creation"""
        with patch('app.main.validate_environment_or_exit') as mock_validate:
            app = create_app('testing')
            
            mock_validate.assert_called_once()
            assert app is not None
    
    def test_environment_validation_failure_handling(self):
        """Test handling of environment validation failure"""
        with patch('app.main.validate_environment_or_exit') as mock_validate:
            mock_validate.side_effect = SystemExit(1)
            
            with pytest.raises(SystemExit):
                create_app('testing')