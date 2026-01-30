"""
MongoDB Database Extension Module.

This module manages the MongoDB connection for the webhook application.
It implements a singleton pattern for the database client to ensure
only one connection pool is maintained throughout the application lifecycle.

Features:
- Connection pooling with configurable pool sizes
- Automatic retry logic for failed connections
- TLS/SSL support for secure connections (MongoDB Atlas)
- Index creation for optimized queries

Module-level Globals:
    _mongo_client: The shared MongoDB client instance
    _database: The current database reference
    _events_collection: The events collection reference
"""

from pymongo import MongoClient, ReadPreference
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import logging
import certifi
import time

logger = logging.getLogger(__name__)

# Module-level singletons for database connection
# These are initialized once and reused throughout the application
_mongo_client = None
_database = None
_events_collection = None


def init_db(app):
    """
    Initialize the MongoDB database connection.
    
    This function establishes a connection to MongoDB with retry logic
    and creates necessary indexes. It uses a singleton pattern to prevent
    multiple connections from being created.
    
    Args:
        app: Flask application instance containing configuration.
        
    Raises:
        ConnectionFailure: If unable to connect after max retries.
        ServerSelectionTimeoutError: If server selection times out.
    """
    global _mongo_client, _database, _events_collection
    
    # Skip if already initialized (singleton pattern)
    if _mongo_client is not None:
        logger.info("MongoDB client already initialized, skipping...")
        return
    
    # Extract connection settings from app configuration
    mongodb_uri = app.config.get('MONGODB_URI', 'mongodb://localhost:27017')
    database_name = app.config.get('MONGODB_DATABASE', 'webhook_db')
    collection_name = app.config.get('MONGODB_COLLECTION', 'events')
    
    # Retry configuration for connection resilience
    max_retries = 3      # Number of connection attempts
    retry_delay = 2      # Seconds to wait between retries
    
    for attempt in range(max_retries):
        try:
            # Create MongoDB client with connection pool settings
            _mongo_client = MongoClient(
                mongodb_uri,
                maxPoolSize=50,              # Maximum connections in the pool
                minPoolSize=10,              # Minimum connections to maintain
                maxIdleTimeMS=30000,         # Close idle connections after 30s
                serverSelectionTimeoutMS=30000,  # Timeout for server selection
                tlsCAFile=certifi.where(),   # Use certifi's CA bundle for TLS
                retryWrites=True,            # Enable automatic write retries
                w='majority'                 # Write concern for data durability
            )
            
            # Verify connection by pinging the server
            _mongo_client.admin.command('ping', read_preference=ReadPreference.PRIMARY_PREFERRED)
            logger.info(f"Successfully connected to MongoDB at {mongodb_uri}")
            
            # Get database and collection references
            _database = _mongo_client[database_name]
            _events_collection = _database[collection_name]
            
            # Create index on timestamp for efficient queries
            # Descending order (-1) for fetching latest events first
            _events_collection.create_index([('timestamp', -1)])
            logger.info(f"Database: {database_name}, Collection: {collection_name}")
            return
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.warning(f"Connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                # Wait before retrying
                time.sleep(retry_delay)
            else:
                # All retries exhausted, raise the error
                logger.error(f"Failed to connect to MongoDB after {max_retries} attempts")
                raise


def get_db():
    """
    Get the MongoDB database instance.
    
    Returns:
        Database: The MongoDB database object.
        
    Raises:
        RuntimeError: If the database hasn't been initialized.
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _database


def get_events_collection():
    """
    Get the events collection for storing webhook events.
    
    Returns:
        Collection: The MongoDB collection for events.
        
    Raises:
        RuntimeError: If the database hasn't been initialized.
    """
    if _events_collection is None:
        raise RuntimeError("Database not initialized. Call init_db first.")
    return _events_collection


def close_db():
    """
    Close the MongoDB connection gracefully.
    
    This should be called during application shutdown to release
    database resources properly.
    """
    global _mongo_client
    if _mongo_client:
        _mongo_client.close()
        logger.info("MongoDB connection closed")
