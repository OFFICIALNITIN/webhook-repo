"""
Flask Application Factory Module.

This module implements the application factory pattern for creating
Flask application instances. It handles:
- Application configuration loading
- Logging setup (file and console)
- CORS (Cross-Origin Resource Sharing) configuration
- Database initialization
- Blueprint registration

The factory pattern allows for easy creation of multiple app instances
with different configurations (useful for testing).
"""

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_cors import CORS

from config import get_config
from .extensions import init_db, close_db
from .routes import api


def create_app(config_class=None):
    """
    Application factory function to create and configure the Flask app.
    
    Args:
        config_class: Optional configuration class. If not provided,
                     the configuration is determined by FLASK_ENV.
    
    Returns:
        Flask: The configured Flask application instance.
    """
    # Create Flask application instance
    app = Flask(__name__)
    
    # Load configuration from the appropriate config class
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize logging for the application
    setup_logging(app)
    
    # Enable CORS for API endpoints to allow cross-origin requests
    # This is essential for frontend applications hosted on different domains
    CORS(app, resources={
        r"/api/*": {"origins": "*"},      # Allow all origins for API routes
        r"/webhook/*": {"origins": "*"},  # Allow GitHub to send webhook requests
        r"/health": {"origins": "*"}      # Allow health check from any origin
    })
    
    # Initialize database connection within application context
    with app.app_context():
        init_db(app)
    
    # Register the API blueprint containing all routes
    app.register_blueprint(api)
    
    # Register teardown function for cleanup (currently a placeholder)
    @app.teardown_appcontext
    def teardown_db(exception=None):
        """Clean up resources when the application context is torn down."""
        pass
    
    app.logger.info("Flask application initialized successfully")
    
    return app


def setup_logging(app):
    """
    Configure application logging with file and console handlers.
    
    Sets up:
    - RotatingFileHandler: Writes logs to 'logs/webhook.log' with rotation
    - StreamHandler: Outputs logs to the console
    
    The log level is determined by the DEBUG configuration setting.
    
    Args:
        app: The Flask application instance.
    """
    # Set log level based on debug mode
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO
    
    # Ensure the logs directory exists
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Configure file handler with log rotation
    # Rotates when file reaches ~10MB, keeps 10 backup files
    file_handler = RotatingFileHandler(
        'logs/webhook.log',
        maxBytes=10240000,   # 10 MB max file size
        backupCount=10       # Keep 10 backup log files
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(log_level)
    
    # Configure console handler for terminal output
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(log_level)
    
    # Apply handlers to the root logger
    logging.basicConfig(level=log_level, handlers=[file_handler, console_handler])
    
    # Also attach handlers directly to Flask's logger
    app.logger.setLevel(log_level)
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
