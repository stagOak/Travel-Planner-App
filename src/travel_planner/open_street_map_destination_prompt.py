from geopy.geocoders import Nominatim
import sys
import argparse

import logging
from typing import List, Dict, Any

from src.utils.api_utils import send_api_request, APIError

logger = logging.getLogger(__name__)

# initialize the OpenStreetMap geocoder
# critical: OpenStreetMap requires a custom 'user_agent' string to identify your app
geolocator = Nominatim(user_agent="Travel-Planner-App")


def get_critical_location_options(query: str) -> List[Dict[str, Any]]:
    """
    Fetches up to 5 location match options from Nominatim.
    Shuts down the application completely if a network or server error occurs.
    """
    custom_headers = {
        "User-Agent": "Travel-Planner-App"
    }

    query_params = {
        "q": query,
        "countrycodes": "us",
        "addressdetails": 1,
        "format": "jsonv2",
        "limit": 5             # CHANGED: Request top 5 options from the API
    }

    try:
        response = send_api_request(
            base_url="https://nominatim.openstreetmap.org",  # Fixed base URL
            endpoint="search",
            method="GET",
            headers=custom_headers,
            params=query_params,
            timeout=10,
            max_retries=3,
            backoff_factor=2.0
        )

        if not response:
            logger.warning(f"No location matches found for: '{query}'")
            return []

        # Ensure the response payload is handled uniformly as a list
        return response if isinstance(response, list) else [response]

    except APIError as e:
        logger.critical(f"CRITICAL FAULT: Application failed to return API response: {e}")
        sys.exit(1)


def present_and_select_location(options: List[Dict[str, Any]]) -> Dict[str, Any] | None:
    """
    Displays location choices cleanly to the user in the console
    and safely prompts them to choose the correct destination match.
    """
    if not options:
        print("\n[!] No matching locations available to choose from.")
        return None

    print(f"\nFound {len(options)} matching locations. Please select the best match:")
    print("-" * 60)

    # 1. Enumerate and display options dynamically
    for index, choice in enumerate(options, start=1):
        display_name = choice.get("display_name", "Unknown Location Location Name")
        lat = choice.get("lat")
        lon = choice.get("lon")
        print(f" [{index}] {display_name}")
        print(f"     Coordinates: (Lat: {lat}, Lon: {lon})")
        print("-" * 60)

    # 2. Infinite validation loop for secure numeric input processing
    while True:
        try:
            user_input = input(f"Enter choice number (1-{len(options)}) or 'q' to cancel: ").strip()

            if user_input.lower() == 'q':
                print("[*] Selection canceled by user.")
                return None

            selection_index = int(user_input)

            if 1 <= selection_index <= len(options):
                # Map back to 0-indexed Python array bounds
                chosen_location = options[selection_index - 1]
                print(f"\nSelected: {chosen_location.get('display_name')}")
                return chosen_location
            else:
                print(f"[!] Invalid entry. Number must be between 1 and {len(options)}.")

        except ValueError:
            print("[! Invalid input. Please enter a valid number or 'q'.")
