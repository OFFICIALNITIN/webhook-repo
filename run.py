"""
Application Entry Point.

This module serves as the main entry point for the Flask application.
It initializes the Flask app using the application factory pattern
and starts the development server when run directly.

Usage:
    python run.py

Environment Variables:
    HOST: The host address to bind the server (default: '0.0.0.0')
    PORT: The port number to listen on (default: 5000)
    FLASK_ENV: The environment mode ('development' or 'production')
"""

import os
from app import create_app

# Create Flask application instance using the factory pattern
app = create_app()

if __name__ == '__main__':
    # Server configuration from environment variables with sensible defaults
    host = os.getenv('HOST', '0.0.0.0')  # Bind to all network interfaces
    port = int(os.getenv('PORT', 5000))   # Default Flask port
    debug = os.getenv('FLASK_ENV', 'development') == 'development'  # Enable debug mode in development
    
    # Start the Flask development server
    app.run(host=host, port=port, debug=debug)
