"""
Environment variable validation for security enhancement
PBI-SEC-ESSENTIAL implementation
"""
import os
import logging


class SecurityError(Exception):
    """Custom exception for security validation errors"""
    pass


def validate_debug_mode():
    """
    Ensure debug mode is disabled in production environment
    
    Raises:
        SecurityError: If debug mode is enabled in production
    """
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    
    if flask_env == 'production':
        # Check various ways DEBUG might be set
        debug_env = os.environ.get('DEBUG', '').lower()
        if debug_env in ['true', '1', 'yes', 'on']:
            raise SecurityError("Debug mode is not allowed in production environment")
        
        # Also check Flask's DEBUG config if it exists
        flask_debug = os.environ.get('FLASK_DEBUG', '').lower()
        if flask_debug in ['true', '1', 'yes', 'on']:
            raise SecurityError("Flask debug mode is not allowed in production environment")


def validate_cors_origins():
    """
    Validate CORS origins configuration for security
    
    Raises:
        SecurityError: If CORS configuration is insecure in production
    """
    flask_env = os.environ.get('FLASK_ENV', 'development').lower()
    
    if flask_env == 'production':
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        
        # Check for wildcard CORS in production
        if '*' in cors_origins:
            raise SecurityError("Wildcard CORS origins (*) are not allowed in production")
        
        # Warn if no CORS origins are specified in production
        if not cors_origins:
            logging.warning("No CORS_ORIGINS specified in production. Using default secure origins.")


def validate_production_environment():
    """
    Validate that production environment has secure configuration
    
    This function should be called during application startup to ensure
    the production environment is properly configured.
    
    Raises:
        SecurityError: If any security validation fails
    """
    try:
        validate_debug_mode()
        validate_cors_origins()
        
        # Log successful validation
        flask_env = os.environ.get('FLASK_ENV', 'development')
        if flask_env == 'production':
            logging.info("Production environment security validation passed")
        
    except SecurityError as e:
        logging.error(f"Security validation failed: {e}")
        raise


def validate_environment_or_exit():
    """
    Validate environment configuration and exit if validation fails
    
    This is a wrapper function that can be used in application startup
    to ensure the application doesn't start with insecure configuration.
    """
    try:
        validate_production_environment()
    except SecurityError as e:
        print(f"SECURITY ERROR: {e}")
        print("Application startup aborted due to security validation failure.")
        exit(1)