"""
API Routes Module.

This module defines the Flask routes for the webhook application:
- /health: Health check endpoint for monitoring
- /webhook/receiver: GitHub webhook receiver endpoint
- /api/events: REST API endpoint to retrieve stored events

Supported GitHub Events:
- push: Code pushed to repository
- pull_request: Pull request opened, updated, or merged
- ping: Webhook configuration verification

Event Types Stored:
- PUSH: Direct code pushes
- PULL_REQUEST: Pull request activities
- MERGE: Merged pull requests
"""

from flask import Blueprint, request, jsonify
import logging
from .extensions import get_events_collection
from .utils import parse_push_event, parse_pull_request_event, validate_event_data

logger = logging.getLogger(__name__)

# Create API blueprint for route registration
api = Blueprint('api', __name__)


@api.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint for monitoring and load balancer verification.
    
    Performs a simple database connectivity test by attempting
    to fetch one document from the events collection.
    
    Returns:
        tuple: JSON response with health status and HTTP status code.
            - 200: Service is healthy
            - 503: Service is unhealthy (database connection failed)
    """
    try:
        # Verify database connectivity
        collection = get_events_collection()
        collection.find_one()
        return jsonify({'status': 'healthy', 'database': 'connected'}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({'status': 'unhealthy', 'error': str(e)}), 503


@api.route('/webhook/receiver', methods=['POST'])
def webhook_receiver():
    """
    GitHub webhook receiver endpoint.
    
    This endpoint receives webhook payloads from GitHub and processes
    them based on the event type. Supported events:
    - push: Stores push events with commit info
    - pull_request: Stores PR events (opened, updated, merged)
    - ping: Responds to webhook configuration tests
    
    The event type is determined by the 'X-GitHub-Event' header.
    
    Returns:
        tuple: JSON response with processing status and HTTP status code.
            - 201: Event successfully processed and stored
            - 200: Event acknowledged (ping or skipped actions)
            - 400: Invalid request (missing header or payload)
            - 500: Internal server error
    """
    try:
        # Extract the GitHub event type from the header
        event_type = request.headers.get('X-GitHub-Event')
        
        # Validate presence of required header
        if not event_type:
            logger.warning("Missing X-GitHub-Event header")
            return jsonify({
                'status': 'error',
                'message': 'Missing X-GitHub-Event header'
            }), 400
        
        # Parse the JSON payload from the request body
        payload = request.get_json()
        
        # Validate payload is present and valid JSON
        if not payload:
            logger.warning("Empty or invalid JSON payload")
            return jsonify({
                'status': 'error',
                'message': 'Invalid or empty JSON payload'
            }), 400
        
        event_data = None
        
        # ----- Handle PUSH events -----
        if event_type == 'push':
            event_data = parse_push_event(payload)
            logger.info(f"Received push event from {event_data['author']}")
        
        # ----- Handle PULL REQUEST events -----
        elif event_type == 'pull_request':
            action = payload.get('action', '')
            pull_request = payload.get('pull_request', {})
            is_merged = pull_request.get('merged', False)
            
            # Check if this is a merge event (PR closed AND merged)
            if action == 'closed' and is_merged:
                event_data = parse_pull_request_event(payload)
                logger.info(f"Received merge event for PR #{event_data['request_id']}")
            # Handle standard PR actions (opened, updated, etc.)
            elif action in ['opened', 'synchronize', 'reopened', 'edited']:
                event_data = parse_pull_request_event(payload)
                logger.info(f"Received pull_request event for PR #{event_data['request_id']}")
            else:
                # Skip untracked PR actions (e.g., 'closed' without merge)
                logger.debug(f"Skipping pull_request action: {action}")
                return jsonify({
                    'status': 'skipped',
                    'message': f'Pull request action "{action}" not tracked'
                }), 200
        
        # ----- Handle PING events (webhook verification) -----
        elif event_type == 'ping':
            logger.info("Received ping event from GitHub")
            return jsonify({
                'status': 'success',
                'message': 'Webhook configured successfully'
            }), 200
        
        # ----- Unsupported event types -----
        else:
            logger.debug(f"Unsupported event type: {event_type}")
            return jsonify({
                'status': 'skipped',
                'message': f'Event type "{event_type}" not supported'
            }), 200
        
        # ----- Store the event in MongoDB -----
        if event_data:
            # Validate event data structure before storing
            validate_event_data(event_data)
            
            # Insert the event into MongoDB
            collection = get_events_collection()
            result = collection.insert_one(event_data)
            
            # Convert ObjectId to string for JSON serialization
            event_data['_id'] = str(result.inserted_id)
            
            logger.info(f"Stored event: {event_data['action']} by {event_data['author']}")
            
            return jsonify({
                'status': 'success',
                'message': 'Event processed and stored',
                'event': event_data
            }), 201
        
        # Fallback error if event_data wasn't set (shouldn't happen)
        return jsonify({
            'status': 'error',
            'message': 'Failed to process event'
        }), 500
        
    except ValueError as e:
        # Handle validation errors from parse functions
        logger.error(f"Validation error: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400
        
    except Exception as e:
        # Catch-all for unexpected errors
        logger.exception(f"Error processing webhook: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error'
        }), 500


@api.route('/api/events', methods=['GET'])
def get_events():
    """
    Retrieve stored webhook events from the database.
    
    Query Parameters:
        limit (int): Maximum number of events to return (1-100, default: 10)
    
    Returns:
        tuple: JSON array of events and HTTP status code.
            - 200: Successfully retrieved events
            - 500: Failed to retrieve events (database error)
    
    Events are returned in reverse chronological order (newest first).
    The '_id' field is excluded from the response.
    """
    try:
        # Get limit parameter with bounds checking (1-100)
        limit = request.args.get('limit', 10, type=int)
        limit = min(max(1, limit), 100)  # Clamp between 1 and 100
        
        collection = get_events_collection()
        
        # Query events, exclude MongoDB _id, sort by newest first
        events = list(collection.find(
            {},           # Empty filter = all documents
            {'_id': 0}    # Projection: exclude _id field
        ).sort('_id', -1).limit(limit))
        
        logger.info(f"Retrieved {len(events)} events")
        
        return jsonify(events), 200
        
    except Exception as e:
        logger.exception(f"Error retrieving events: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve events'
        }), 500
