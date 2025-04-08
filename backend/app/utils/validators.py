"""Input validation utilities for the StepIn application."""
from datetime import datetime
from typing import List, Dict, Any, Optional

def validate_email(email: str) -> bool:
    """
    Validate an email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Simple validation - improve as needed
    return '@' in email and '.' in email.split('@')[1]

def validate_meeting_times(t1: str, t2: str) -> bool:
    """
    Validate meeting start and end times.
    
    Args:
        t1: Start time in ISO format
        t2: End time in ISO format
        
    Returns:
        True if valid, False otherwise
    """
    try:
        start_time = datetime.fromisoformat(t1)
        end_time = datetime.fromisoformat(t2)
        
        # End time must be after start time
        return end_time > start_time
    except ValueError:
        return False
    
def validate_coordinates(lat: float, long: float) -> bool:
    """
    Validate geographical coordinates.
    
    Args:
        lat: Latitude in degrees
        long: Longitude in degrees
        
    Returns:
        True if valid, False otherwise
    """
    return -90 <= lat <= 90 and -180 <= long <= 180

def validate_meeting_data(meeting_data: Dict[str, Any]) -> List[str]:
    """
    Validate meeting data for creation or update.
    
    Args:
        meeting_data: Meeting data dictionary
        
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Required fields
    required_fields = ['title', 't1', 't2', 'lat', 'long']
    for field in required_fields:
        if field not in meeting_data:
            errors.append(f"Missing required field: {field}")
    
    # If missing required fields, don't continue validation
    if errors:
        return errors
    
    # Validate times
    if not validate_meeting_times(meeting_data['t1'], meeting_data['t2']):
        errors.append("End time must be after start time")
    
    # Validate coordinates
    if not validate_coordinates(meeting_data['lat'], meeting_data['long']):
        errors.append("Invalid coordinates")
    
    # Validate title length
    if len(meeting_data['title']) < 3 or len(meeting_data['title']) > 100:
        errors.append("Title must be between 3 and 100 characters")
    
    return errors