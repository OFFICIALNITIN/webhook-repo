"""
Application Configuration Module.

This module defines configuration classes for different environments
(development, production, testing). It uses the dotenv package to load
environment variables from a .env file.

Configuration Classes:
    - Config: Base configuration with default settings
    - DevelopmentConfig: Development environment with debug enabled
    - ProductionConfig: Production environment with debug disabled
    - TestingConfig: Testing environment with separate test database
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Base configuration class with default settings.
    
    All environment-specific configurations inherit from this class.
    Settings can be overridden via environment variables.
    """
    
    # Flask secret key for session management and security features
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # Application mode flags
    DEBUG = False
    TESTING = False
    
    # MongoDB connection settings
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017')
    MONGODB_DATABASE = 'webhook_db'        # Database name for webhook events
    MONGODB_COLLECTION = 'events'          # Collection name for storing events
    
    # Server binding configuration
    HOST = os.getenv('HOST', '0.0.0.0')    # Listen on all network interfaces
    PORT = int(os.getenv('PORT', 5000))    # Default application port


class DevelopmentConfig(Config):
    """Development configuration with debug mode enabled."""
    DEBUG = True


class ProductionConfig(Config):
    """Production configuration with debug mode disabled."""
    DEBUG = False


class TestingConfig(Config):
    """
    Testing configuration with a separate test database.
    
    Uses a different database name to avoid polluting production data
    during automated tests.
    """
    TESTING = True
    MONGODB_DATABASE = 'webhook_db_test'  # Separate database for testing


# Configuration mapping for easy lookup by environment name
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}


def get_config():
    """
    Get the appropriate configuration class based on FLASK_ENV.
    
    Returns:
        Config subclass: The configuration class matching the current environment.
                        Defaults to DevelopmentConfig if FLASK_ENV is not set.
    """
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
