"""
Utility Functions Module.

This module provides helper functions for processing GitHub webhook payloads.
It handles parsing of different event types and ensures data consistency.

Functions:
- format_timestamp: Converts ISO timestamps to human-readable format
- parse_push_event: Extracts data from push event payloads
- parse_pull_request_event: Extracts data from PR event payloads
- validate_event_data: Validates event data before storage

Event Data Schema:
    {
        'request_id': str,    # Commit SHA or PR number
        'author': str,        # Username who triggered the event
        'action': str,        # PUSH, PULL_REQUEST, or MERGE
        'from_branch': str,   # Source branch
        'to_branch': str,     # Target branch
        'timestamp': str      # Formatted timestamp string
    }
"""

from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


def format_timestamp(timestamp_str=None):
    """
    Convert ISO 8601 timestamp to a human-readable format.
    
    Handles various timestamp formats from GitHub and converts them
    to a standardized UTC format for display.
    
    Args:
        timestamp_str (str, optional): ISO 8601 formatted timestamp string.
                                       If None, uses current UTC time.
    
    Returns:
        str: Formatted timestamp string (e.g., "30 January 2026 - 09:25 PM UTC")
    """
    try:
        if timestamp_str:
            # Handle 'Z' suffix (Zulu time = UTC)
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            # Parse ISO format and convert to UTC
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            dt = dt.astimezone(timezone.utc)
        else:
            # Use current UTC time if no timestamp provided
            dt = datetime.now(timezone.utc)
        
        # Format: "DD Month YYYY - HH:MM AM/PM UTC"
        return dt.strftime("%d %B %Y - %I:%M %p UTC")
    except Exception as e:
        # Fallback to current time if parsing fails
        logger.warning(f"Error parsing timestamp '{timestamp_str}': {e}")
        return datetime.now(timezone.utc).strftime("%d %B %Y - %I:%M %p UTC")


def parse_push_event(payload):
    """
    Parse a GitHub push event payload into a standardized event format.
    
    Extracts relevant information from the push webhook payload including
    the commit ID, author, and branch information.
    
    Args:
        payload (dict): The GitHub webhook payload for a push event.
    
    Returns:
        dict: Standardized event data with the following keys:
            - request_id: The head commit SHA
            - author: Name of the user who pushed
            - action: 'PUSH'
            - from_branch: Source branch name
            - to_branch: Target branch name (same as from_branch for pushes)
            - timestamp: Formatted timestamp string
    
    Raises:
        ValueError: If the payload is invalid or missing required fields.
    """
    try:
        # Get the head (latest) commit information
        head_commit = payload.get('head_commit', {})
        request_id = head_commit.get('id', payload.get('after', 'unknown'))
        
        # Get the pusher (person who pushed the code)
        pusher = payload.get('pusher', {})
        author = pusher.get('name', 'unknown')
        
        # Extract branch name from the ref (e.g., 'refs/heads/main' -> 'main')
        ref = payload.get('ref', '')
        to_branch = ref.replace('refs/heads/', '') if ref.startswith('refs/heads/') else ref
        
        # For push events, source and target branches are the same
        from_branch = to_branch
        
        # Get commit timestamp
        timestamp_str = head_commit.get('timestamp')
        
        return {
            'request_id': request_id,
            'author': author,
            'action': 'PUSH',
            'from_branch': from_branch,
            'to_branch': to_branch,
            'timestamp': format_timestamp(timestamp_str)
        }
    except Exception as e:
        logger.error(f"Error parsing push event: {e}")
        raise ValueError(f"Invalid push event payload: {e}")


def parse_pull_request_event(payload):
    """
    Parse a GitHub pull request event payload into a standardized event format.
    
    Handles both regular PR events and merge events, extracting relevant
    information such as PR number, author, and branch details.
    
    Args:
        payload (dict): The GitHub webhook payload for a pull_request event.
    
    Returns:
        dict: Standardized event data with the following keys:
            - request_id: The pull request number
            - author: Username of the PR author
            - action: 'PULL_REQUEST' or 'MERGE'
            - from_branch: Source (head) branch
            - to_branch: Target (base) branch
            - timestamp: Formatted timestamp string (merged_at for merges)
    
    Raises:
        ValueError: If the payload is invalid or missing required fields.
    """
    try:
        # Extract pull request object from payload
        pull_request = payload.get('pull_request', {})
        
        # Get PR number from payload or nested object
        request_id = str(payload.get('number', pull_request.get('number', 'unknown')))
        
        # Get the PR author (user who opened the PR)
        user = pull_request.get('user', {})
        author = user.get('login', 'unknown')
        
        # Extract branch information
        # head = source branch (where changes come from)
        # base = target branch (where changes go to)
        head = pull_request.get('head', {})
        base = pull_request.get('base', {})
        from_branch = head.get('ref', 'unknown')
        to_branch = base.get('ref', 'unknown')
        
        # Check if this is a merge event
        is_merged = pull_request.get('merged', False)
        
        if is_merged:
            # For merges, use 'MERGE' action and merged_at timestamp
            action = 'MERGE'
            timestamp_str = pull_request.get('merged_at')
        else:
            # For regular PR events, use 'PULL_REQUEST' action
            action = 'PULL_REQUEST'
            # Prefer updated_at, fallback to created_at
            timestamp_str = pull_request.get('updated_at') or pull_request.get('created_at')
        
        return {
            'request_id': request_id,
            'author': author,
            'action': action,
            'from_branch': from_branch,
            'to_branch': to_branch,
            'timestamp': format_timestamp(timestamp_str)
        }
    except Exception as e:
        logger.error(f"Error parsing pull_request event: {e}")
        raise ValueError(f"Invalid pull_request event payload: {e}")


def validate_event_data(event_data):
    """
    Validate event data before storing in the database.
    
    Ensures that all required fields are present and that the action
    type is one of the supported values.
    
    Args:
        event_data (dict): The event data to validate.
    
    Returns:
        bool: True if validation passes.
    
    Raises:
        ValueError: If any required field is missing or action is invalid.
    """
    # Define required fields for all events
    required_fields = ['request_id', 'author', 'action', 'from_branch', 'to_branch', 'timestamp']
    
    # Check for missing or None fields
    for field in required_fields:
        if field not in event_data or event_data[field] is None:
            raise ValueError(f"Missing required field: {field}")
    
    # Validate action type
    valid_actions = ['PUSH', 'PULL_REQUEST', 'MERGE']
    if event_data['action'] not in valid_actions:
        raise ValueError(f"Invalid action: {event_data['action']}. Must be one of {valid_actions}")
    
    return True
