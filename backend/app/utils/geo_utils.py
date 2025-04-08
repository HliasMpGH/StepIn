"""Geospatial utility functions for meeting locations."""
import math
from typing import List, Tuple, Dict, Any

# Approximate kilometers per degree
KM_PER_DEG_LAT = 111.0
# Earth radius in kilometers
EARTH_RADIUS_KM = 6371.0

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the distance between two geographic points using the Haversine formula.
    
    Args:
        lat1: Latitude of point 1 in degrees
        lon1: Longitude of point 1 in degrees
        lat2: Latitude of point 2 in degrees
        lon2: Longitude of point 2 in degrees
        
    Returns:
        Distance between the points in kilometers
    """
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = EARTH_RADIUS_KM * c
    
    return distance

def get_bounding_box(lat: float, lon: float, distance_km: float) -> Tuple[float, float, float, float]:
    """
    Calculate a bounding box around a point given a distance.
    
    Args:
        lat: Latitude of center point in degrees
        lon: Longitude of center point in degrees
        distance_km: Distance in kilometers
        
    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon) defining the bounding box
    """
    # Approximate degrees per kilometer
    km_per_deg_lon = KM_PER_DEG_LAT * math.cos(math.radians(lat))
    
    # Calculate the bounding box
    lat_change = distance_km / KM_PER_DEG_LAT
    lon_change = distance_km / km_per_deg_lon
    
    min_lat = lat - lat_change
    max_lat = lat + lat_change
    min_lon = lon - lon_change
    max_lon = lon + lon_change
    
    return (min_lat, min_lon, max_lat, max_lon)

def format_location_for_display(lat: float, lon: float) -> str:
    """
    Format a location for display in a user-friendly format.
    
    Args:
        lat: Latitude in degrees
        lon: Longitude in degrees
        
    Returns:
        Formatted location string
    """
    lat_direction = "N" if lat >= 0 else "S"
    lon_direction = "E" if lon >= 0 else "W"
    
    lat_abs = abs(lat)
    lon_abs = abs(lon)
    
    lat_deg = int(lat_abs)
    lon_deg = int(lon_abs)
    
    lat_min = (lat_abs - lat_deg) * 60
    lon_min = (lon_abs - lon_deg) * 60
    
    return f"{lat_deg}°{lat_min:.2f}'{lat_direction}, {lon_deg}°{lon_min:.2f}'{lon_direction}"

def meeting_to_geojson(meeting: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert a meeting to GeoJSON format for map display.
    
    Args:
        meeting: Meeting dictionary with lat, long, and other properties
        
    Returns:
        GeoJSON Feature representation of the meeting
    """
    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [meeting["long"], meeting["lat"]]
        },
        "properties": {
            "meeting_id": meeting["meeting_id"],
            "title": meeting["title"],
            "description": meeting["description"],
            "start_time": meeting["t1"],
            "end_time": meeting["t2"],
            "participants": meeting.get("participants", [])
        }
    }

def meetings_to_geojson_collection(meetings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Convert a list of meetings to a GeoJSON FeatureCollection.
    
    Args:
        meetings: List of meeting dictionaries
        
    Returns:
        GeoJSON FeatureCollection containing all meetings
    """
    features = [meeting_to_geojson(meeting) for meeting in meetings]
    return {
        "type": "FeatureCollection",
        "features": features
    }