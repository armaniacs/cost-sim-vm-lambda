"""
Unit tests for environment validator security module
Tests all security validation functions comprehensively
"""
import pytest
import os
from unittest.mock import patch, MagicMock
import logging
import sys

from app.security.env_validator import (
    SecurityError,
    validate_debug_mode,
    validate_cors_origins,
    validate_production_environment,
    validate_environment_or_exit
)


class TestSecurityError:
    """Test SecurityError custom exception"""
    
    def test_security_error_creation(self):
        """Test SecurityError can be created and raised"""
        error = SecurityError("Test security error")
        assert str(error) == "Test security error"
        assert isinstance(error, Exception)
    
    def test_security_error_inheritance(self):
        """Test SecurityError inherits from Exception"""
        error = SecurityError("Test error")
        assert isinstance(error, Exception)
        assert isinstance(error, SecurityError)


class TestValidateDebugMode:
    """Test debug mode validation function"""
    
    def test_debug_mode_development_allowed(self):
        """Test debug mode is allowed in development environment"""
        with patch.dict(os.environ, {'FLASK_ENV': 'development', 'DEBUG': 'true'}):
            # Should not raise any exception
            validate_debug_mode()
    
    def test_debug_mode_testing_allowed(self):
        """Test debug mode is allowed in testing environment"""
        with patch.dict(os.environ, {'FLASK_ENV': 'testing', 'DEBUG': 'true'}):
            # Should not raise any exception
            validate_debug_mode()
    
    def test_debug_mode_production_debug_true_raises_error(self):
        """Test debug mode raises error when DEBUG=true in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': 'true'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_debug_mode_production_debug_1_raises_error(self):
        """Test debug mode raises error when DEBUG=1 in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': '1'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_debug_mode_production_debug_yes_raises_error(self):
        """Test debug mode raises error when DEBUG=yes in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': 'yes'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_debug_mode_production_debug_on_raises_error(self):
        """Test debug mode raises error when DEBUG=on in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': 'on'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_flask_debug_production_flask_debug_true_raises_error(self):
        """Test FLASK_DEBUG=true raises error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'FLASK_DEBUG': 'true'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Flask debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_flask_debug_production_flask_debug_1_raises_error(self):
        """Test FLASK_DEBUG=1 raises error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'FLASK_DEBUG': '1'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Flask debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_flask_debug_production_flask_debug_yes_raises_error(self):
        """Test FLASK_DEBUG=yes raises error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'FLASK_DEBUG': 'yes'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Flask debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_flask_debug_production_flask_debug_on_raises_error(self):
        """Test FLASK_DEBUG=on raises error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'FLASK_DEBUG': 'on'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_debug_mode()
            assert "Flask debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_debug_mode_production_debug_false_allowed(self):
        """Test debug mode is allowed when DEBUG=false in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': 'false'}):
            # Should not raise any exception
            validate_debug_mode()
    
    def test_debug_mode_production_no_debug_env_allowed(self):
        """Test no debug environment variables in production is allowed"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True):
            # Should not raise any exception
            validate_debug_mode()
    
    def test_debug_mode_case_insensitive(self):
        """Test debug mode validation is case insensitive"""
        with patch.dict(os.environ, {'FLASK_ENV': 'PRODUCTION', 'DEBUG': 'TRUE'}):
            with pytest.raises(SecurityError):
                validate_debug_mode()
    
    def test_debug_mode_default_flask_env(self):
        """Test debug mode validation with default FLASK_ENV"""
        with patch.dict(os.environ, {}, clear=True):
            # Default is development, so DEBUG=true should be allowed
            with patch.dict(os.environ, {'DEBUG': 'true'}):
                validate_debug_mode()


class TestValidateCorsOrigins:
    """Test CORS origins validation function"""
    
    def test_cors_origins_development_wildcard_allowed(self):
        """Test wildcard CORS origins are allowed in development"""
        with patch.dict(os.environ, {'FLASK_ENV': 'development', 'CORS_ORIGINS': '*'}):
            # Should not raise any exception
            validate_cors_origins()
    
    def test_cors_origins_production_wildcard_raises_error(self):
        """Test wildcard CORS origins raise error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': '*'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_cors_origins()
            assert "Wildcard CORS origins (*) are not allowed in production" in str(exc_info.value)
    
    def test_cors_origins_production_partial_wildcard_raises_error(self):
        """Test partial wildcard CORS origins raise error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': 'https://example.com,*'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_cors_origins()
            assert "Wildcard CORS origins (*) are not allowed in production" in str(exc_info.value)
    
    def test_cors_origins_production_wildcard_in_domain_raises_error(self):
        """Test wildcard in domain raises error in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': 'https://*.example.com'}):
            with pytest.raises(SecurityError) as exc_info:
                validate_cors_origins()
            assert "Wildcard CORS origins (*) are not allowed in production" in str(exc_info.value)
    
    def test_cors_origins_production_valid_origins_allowed(self):
        """Test valid specific origins are allowed in production"""
        valid_origins = 'https://app.example.com,https://admin.example.com'
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': valid_origins}):
            # Should not raise any exception
            validate_cors_origins()
    
    def test_cors_origins_production_no_origins_warning(self):
        """Test no CORS origins in production logs warning"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True):
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_cors_origins()
                mock_logging.warning.assert_called_once_with(
                    "No CORS_ORIGINS specified in production. Using default secure origins."
                )
    
    def test_cors_origins_production_empty_origins_warning(self):
        """Test empty CORS origins in production logs warning"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': ''}):
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_cors_origins()
                mock_logging.warning.assert_called_once_with(
                    "No CORS_ORIGINS specified in production. Using default secure origins."
                )
    
    def test_cors_origins_case_insensitive_env(self):
        """Test CORS validation is case insensitive for FLASK_ENV"""
        with patch.dict(os.environ, {'FLASK_ENV': 'PRODUCTION', 'CORS_ORIGINS': '*'}):
            with pytest.raises(SecurityError):
                validate_cors_origins()
    
    def test_cors_origins_testing_environment(self):
        """Test CORS origins in testing environment are allowed"""
        with patch.dict(os.environ, {'FLASK_ENV': 'testing', 'CORS_ORIGINS': '*'}):
            # Should not raise any exception
            validate_cors_origins()


class TestValidateProductionEnvironment:
    """Test production environment validation function"""
    
    def test_validate_production_environment_success(self):
        """Test successful production environment validation"""
        valid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'false',
            'CORS_ORIGINS': 'https://app.example.com'
        }
        with patch.dict(os.environ, valid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_production_environment()
                mock_logging.info.assert_called_once_with(
                    "Production environment security validation passed"
                )
    
    def test_validate_production_environment_development_success(self):
        """Test production validation in development environment"""
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}):
            # Should not raise any exception and not log production message
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_production_environment()
                # Should not call info with production message
                mock_logging.info.assert_not_called()
    
    def test_validate_production_environment_debug_error(self):
        """Test production environment validation fails with debug enabled"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'true'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                with pytest.raises(SecurityError) as exc_info:
                    validate_production_environment()
                
                # Check that error was logged
                mock_logging.error.assert_called_once()
                error_call = mock_logging.error.call_args[0][0]
                assert "Security validation failed:" in error_call
                
                # Check exception message
                assert "Debug mode is not allowed in production environment" in str(exc_info.value)
    
    def test_validate_production_environment_cors_error(self):
        """Test production environment validation fails with wildcard CORS"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'CORS_ORIGINS': '*'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                with pytest.raises(SecurityError) as exc_info:
                    validate_production_environment()
                
                # Check that error was logged
                mock_logging.error.assert_called_once()
                error_call = mock_logging.error.call_args[0][0]
                assert "Security validation failed:" in error_call
                
                # Check exception message
                assert "Wildcard CORS origins (*) are not allowed in production" in str(exc_info.value)
    
    def test_validate_production_environment_multiple_errors(self):
        """Test production environment validation with multiple errors"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'true',
            'CORS_ORIGINS': '*'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                with pytest.raises(SecurityError):
                    validate_production_environment()
                
                # Should log the first error encountered
                mock_logging.error.assert_called_once()


class TestValidateEnvironmentOrExit:
    """Test environment validation with exit functionality"""
    
    def test_validate_environment_or_exit_success(self):
        """Test successful environment validation does not exit"""
        valid_env = {
            'FLASK_ENV': 'development',
            'DEBUG': 'true'
        }
        with patch.dict(os.environ, valid_env):
            # Should not raise SystemExit or any exception
            validate_environment_or_exit()
    
    def test_validate_environment_or_exit_production_success(self):
        """Test successful production environment validation does not exit"""
        valid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'false',
            'CORS_ORIGINS': 'https://app.example.com'
        }
        with patch.dict(os.environ, valid_env):
            # Should not raise SystemExit or any exception
            validate_environment_or_exit()
    
    def test_validate_environment_or_exit_debug_error_exits(self):
        """Test environment validation exits on debug error"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'true'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    validate_environment_or_exit()
                
                # Check exit code
                assert exc_info.value.code == 1
                
                # Check printed messages
                assert mock_print.call_count == 2
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("SECURITY ERROR:" in call for call in print_calls)
                assert any("Application startup aborted" in call for call in print_calls)
    
    def test_validate_environment_or_exit_cors_error_exits(self):
        """Test environment validation exits on CORS error"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'CORS_ORIGINS': '*'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit) as exc_info:
                    validate_environment_or_exit()
                
                # Check exit code
                assert exc_info.value.code == 1
                
                # Check that error messages were printed
                assert mock_print.call_count == 2
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                assert any("SECURITY ERROR:" in call and "Wildcard CORS origins" in call for call in print_calls)
                assert any("Application startup aborted" in call for call in print_calls)
    
    def test_validate_environment_or_exit_error_message_format(self):
        """Test error message format in validate_environment_or_exit"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'yes'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('builtins.print') as mock_print:
                with pytest.raises(SystemExit):
                    validate_environment_or_exit()
                
                # Check specific error message format
                print_calls = [call[0][0] for call in mock_print.call_args_list]
                security_error_msg = [call for call in print_calls if "SECURITY ERROR:" in call][0]
                assert "Debug mode is not allowed in production environment" in security_error_msg


class TestEnvironmentVariableEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_flask_env_uppercase_handling(self):
        """Test FLASK_ENV handling with various cases"""
        test_cases = ['PRODUCTION', 'production', 'Production', 'pRoDuCtIoN']
        
        for flask_env in test_cases:
            with patch.dict(os.environ, {'FLASK_ENV': flask_env, 'DEBUG': 'true'}):
                with pytest.raises(SecurityError):
                    validate_debug_mode()
    
    def test_debug_values_edge_cases(self):
        """Test various debug value edge cases"""
        # Values that should NOT trigger debug mode in production
        safe_values = ['false', 'False', '0', 'no', 'off', 'disabled', '']
        
        for debug_val in safe_values:
            with patch.dict(os.environ, {'FLASK_ENV': 'production', 'DEBUG': debug_val}):
                # Should not raise exception
                validate_debug_mode()
    
    def test_cors_origins_complex_patterns(self):
        """Test complex CORS origins patterns"""
        # These should all raise errors in production due to wildcards
        wildcard_patterns = [
            '*',
            'https://*.example.com',
            'https://app.example.com,*',
            'https://app.example.com,https://*.other.com',
            '*.example.com',
            'https://app.*.com'
        ]
        
        for cors_pattern in wildcard_patterns:
            with patch.dict(os.environ, {'FLASK_ENV': 'production', 'CORS_ORIGINS': cors_pattern}):
                with pytest.raises(SecurityError) as exc_info:
                    validate_cors_origins()
                assert "Wildcard CORS origins" in str(exc_info.value)
    
    def test_environment_combinations(self):
        """Test various environment variable combinations"""
        # Valid production configurations
        valid_configs = [
            {
                'FLASK_ENV': 'production',
                'DEBUG': 'false',
                'CORS_ORIGINS': 'https://app.example.com'
            },
            {
                'FLASK_ENV': 'production',
                'FLASK_DEBUG': '0',
                'CORS_ORIGINS': 'https://app.example.com,https://admin.example.com'
            },
            {
                'FLASK_ENV': 'production',
                # No debug settings (should be safe)
                'CORS_ORIGINS': 'https://secure.example.com'
            }
        ]
        
        for config in valid_configs:
            with patch.dict(os.environ, config, clear=True):
                # Should not raise any exceptions
                validate_production_environment()
    
    def test_empty_environment_handling(self):
        """Test handling of completely empty environment"""
        with patch.dict(os.environ, {}, clear=True):
            # Should default to development and not raise errors
            validate_debug_mode()
            validate_cors_origins()
            validate_production_environment()
            validate_environment_or_exit()


class TestLoggingIntegration:
    """Test logging integration across all functions"""
    
    def test_production_validation_success_logging(self):
        """Test successful production validation logs appropriate message"""
        valid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'false',
            'CORS_ORIGINS': 'https://example.com'
        }
        with patch.dict(os.environ, valid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_production_environment()
                
                # Should log success message
                mock_logging.info.assert_called_once_with(
                    "Production environment security validation passed"
                )
                mock_logging.error.assert_not_called()
                mock_logging.warning.assert_not_called()
    
    def test_cors_warning_logging(self):
        """Test CORS warning logging in production"""
        with patch.dict(os.environ, {'FLASK_ENV': 'production'}, clear=True):
            with patch('app.security.env_validator.logging') as mock_logging:
                validate_cors_origins()
                
                # Should log warning for missing CORS origins
                mock_logging.warning.assert_called_once_with(
                    "No CORS_ORIGINS specified in production. Using default secure origins."
                )
    
    def test_error_logging_in_production_validation(self):
        """Test error logging when production validation fails"""
        invalid_env = {
            'FLASK_ENV': 'production',
            'DEBUG': 'true'
        }
        with patch.dict(os.environ, invalid_env):
            with patch('app.security.env_validator.logging') as mock_logging:
                with pytest.raises(SecurityError):
                    validate_production_environment()
                
                # Should log the error
                mock_logging.error.assert_called_once()
                error_message = mock_logging.error.call_args[0][0]
                assert "Security validation failed:" in error_message
                assert "Debug mode is not allowed" in error_message