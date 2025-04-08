"""Time and date utilities for the StepIn application."""
from datetime import datetime, timedelta
from typing import Union, Optional, Tuple

def parse_iso_datetime(date_str: str) -> datetime:
    """
    Parse an ISO format datetime string.
    
    Args:
        date_str: ISO datetime string
        
    Returns:
        Parsed datetime object
    """
    return datetime.fromisoformat(date_str)

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object as a string.
    
    Args:
        dt: Datetime object
        format_str: Format string (default: Y-m-d H:M:S)
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)

def get_current_time() -> datetime:
    """
    Get the current UTC time.
    
    Returns:
        Current UTC datetime
    """
    return datetime.utcnow()

def get_time_delta(dt1: Union[str, datetime], dt2: Union[str, datetime]) -> timedelta:
    """
    Get the time difference between two datetimes.
    
    Args:
        dt1: First datetime (string or datetime object)
        dt2: Second datetime (string or datetime object)
        
    Returns:
        Timedelta between the two times
    """
    if isinstance(dt1, str):
        dt1 = parse_iso_datetime(dt1)
    if isinstance(dt2, str):
        dt2 = parse_iso_datetime(dt2)
        
    return dt2 - dt1

def is_meeting_active(start_time: Union[str, datetime], 
                      end_time: Union[str, datetime]) -> bool:
    """
    Check if a meeting is currently active based on start and end times.
    
    Args:
        start_time: Meeting start time
        end_time: Meeting end time
        
    Returns:
        True if the meeting is active, False otherwise
    """
    now = get_current_time()
    
    if isinstance(start_time, str):
        start_time = parse_iso_datetime(start_time)
    if isinstance(end_time, str):
        end_time = parse_iso_datetime(end_time)
        
    return start_time <= now <= end_time

def get_next_meeting_times(interval_minutes: int = 30) -> Tuple[str, str]:
    """
    Get start and end times for a new meeting beginning at the next interval.
    
    Args:
        interval_minutes: Interval in minutes (default: 30)
        
    Returns:
        Tuple of (start_time, end_time) as ISO format strings
    """
    now = get_current_time()
    
    # Round up to the next interval
    minutes = now.minute
    rounded_minutes = ((minutes + interval_minutes) // interval_minutes) * interval_minutes
    
    # Create the start time
    start_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(minutes=rounded_minutes)
    
    # Default meeting duration: 1 hour
    end_time = start_time + timedelta(hours=1)
    
    return start_time.isoformat(), end_time.isoformat()