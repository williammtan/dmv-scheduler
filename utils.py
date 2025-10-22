import pgeocode
from math import radians, sin, cos, sqrt, atan2
import subprocess
from datetime import datetime

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in miles
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

def distance_between_zips(zip1, zip2, country='US', unit='miles'):
    nomi = pgeocode.Nominatim(country)
    info1 = nomi.query_postal_code(zip1)
    info2 = nomi.query_postal_code(zip2)
    if info1 is None or info2 is None:
        raise ValueError("Invalid ZIP code(s)")
    dist = haversine(info1['latitude'], info1['longitude'], info2['latitude'], info2['longitude'])
    return dist if unit == 'miles' else dist * 1.60934  # km

def send_dmv_summary_email(recipient_email, found_locations, found_schedules, found_distances, send_if_exists=True):
    """
    Sends a neat email summary of DMV appointment findings using the built-in 'mail' command.
    Sorts locations from shortest to furthest distance and shows all available times for each.
    
    Args:
    - recipient_email (str): The email address to send the summary to.
    - found_locations (list[str]): List of location names.
    - found_schedules (list[list[datetime]]): List of lists, where each sublist contains datetime objects for appointments at that location.
    - found_distances (list[float]): List of distances corresponding to each location (in miles or km; assumes same unit).
    
    Note: If found_distances is empty or incomplete, sorting is skipped and locations are shown in original order.
    """
    # Zip the data together for sorting
    data = list(zip(found_locations, found_schedules, found_distances if found_distances else [0] * len(found_locations)))
    if(len(data) == 0):
        print("Warning: No locations found, not sending email due to `send_if_exists`=True")
        return
    
    # Sort by distance (shortest to furthest) if distances are provided
    if found_distances:
        data.sort(key=lambda x: x[2])
    else:
        print("Warning: No distances provided; showing in original order.")
    
    # Format the email body
    body = "DMV Appointments Summary\n\n"
    body += "Here are the available DMV appointment locations, sorted from shortest to furthest distance (if distances were provided):\n\n"
    
    for location, schedules, distance in data:
        body += f"Location: {location}\n"
        if found_distances:
            body += f"Distance: {distance} miles\n"
        body += "Available Dates:\n"
        for dt in schedules:
            formatted_date = dt.strftime("%B %d, %Y %I:%M %p")  # e.g., October 08, 2025 12:00 AM
            body += f"- {formatted_date}\n"
        body += "\n"  # Separator between locations
    
    body += "If no dates are shown for a location, none were found.\n"
    body += "This summary is based on the latest findings as of the current date.\n"
    
    # Use the mail command to send the email
    subject = "DMV Appointments Summary"
    try:
        subprocess.run(['mail', '-s', subject, recipient_email], input=body.encode(), check=True)
        print("Email sent successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error sending email: {e}")
        raise
