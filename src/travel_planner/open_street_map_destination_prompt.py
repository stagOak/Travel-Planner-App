from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sys
import argparse

import logging
from typing import List, Dict, Any

from src.utils.api_utils import send_api_request, APIError

logger = logging.getLogger(__name__)

# initialize the OpenStreetMap geocoder
# critical: OpenStreetMap requires a custom 'user_agent' string to identify your app
geolocator = Nominatim(user_agent="Travel-Planner-App")


def str2bool(v):
    """Convert string user input into a strict Python boolean."""
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected (True/False).')


def search_osm_destination(query: str, prints: bool = False):

    try:

        # search for the location. 'country_codes="us"' restricts all search results strictly to the USA
        # 'addressdetails=True' tells OSM to break down the response into city, state, etc.
        location = geolocator.geocode(
            query,
            country_codes="us",
            addressdetails=True,
            timeout=10
        )

        if location:

            address = location.raw.get('address', {})

            # extract data safely using fallback logic
            # natural locations (like parks) won't have a 'city' key, so we check for 'town' or 'county'
            city_or_town = address.get('city') or address.get('town') or address.get('village') or address.get('county')
            state = address.get('state', 'Unknown State')

            if prints:
                print(f"\n")
                print("-" * 30)
                print(f"Searched for: '{query}'")
                print(f"Matched Name: {location.address.split(',')[0]}")  # Gets the exact name of the place
                print(f"Region/Local Area: {city_or_town}")
                print(f"State: {state}")
                print(f"Latitude: {location.latitude}")
                print(f"Longitude: {location.longitude}")
                print("-" * 30)

            return {
                'query': query,
                'location': location.address.split(',')[0],
                'city_or_town': city_or_town,
                'state': state,
                'latitude': location.latitude,
                'longitude': location.longitude,
            }
        else:
            print(f"no results found in the USA for: '{query}'")

    except GeocoderTimedOut:
        sys.exit("the search request timed out. please try again.")


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


if __name__ == "__main__":
    """
    # prints arg use
    # python open_street_map_destination_prompt.py casper --prints True
    # no prints: python open_street_map_destination_prompt.py casper
    # no prints: python open_street_map_destination_prompt.py casper --prints False
    
    # OpenStreetMap (osm) geocoder test queries
    # 1. Test a classic non-city natural landmark
    # search_osm_destination("Yellowstone National Park")
    # 2. Test a standard city
    # search_osm_destination("Seattle")
    # 3. Test a specific point of interest
    # search_osm_destination("Disneyland California")
    """

    # initialize the argument parser
    parser = argparse.ArgumentParser(description="A script that accepts terminal parameters.")

    # add parameters to the argument parser
    parser.add_argument("destination", type=str, help="tomorrows destination")
    parser.add_argument(
        '--prints',
        type=str2bool,
        nargs='?',
        const=True,
        default=False,
        help='Enable or disable printing (default: %(default)s)'
    )
    # parser.add_argument("prints", nargs='?', type=bool, default=False, help="if True then print out results")
    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode (Flag)")

    # parse the arguments from the terminal
    args = parser.parse_args()

    # prints arg use
    # python src/travel_planner/open_street_map_destination_prompt.py casper --prints True
    # no prints: python src/travel_planner/open_street_map_destination_prompt.py casper
    # no prints: python src/travel_planner/open_street_map_destination_prompt.py casper --prints False

    # begin processing
    if args.verbose:
        print("\nOpenStreetMap is being queried for {}...".format(args.destination))

    # query OpenStreetMap (osm) geocoder
    return_dict = search_osm_destination(args.destination, args.prints)

    if return_dict is not None:
        search_query = return_dict["query"]
        result_location = return_dict["location"]
        result_city_or_town = return_dict["city_or_town"]
        result_state = return_dict["state"]
        result_lat = return_dict["latitude"]
        result_lon = return_dict["longitude"]

        print(f"\n\nmain.py prints:"
              f"\n   search_query: {search_query}"
              f"\n   result_location: {result_location}"
              f"\n   result_city_or_town: {result_city_or_town}"
              f"\n   result_state: {result_state}"
              f"\n   result_lat: {result_lat}"
              f"\n   result_lon: {result_lon}")
