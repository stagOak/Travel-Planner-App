from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import sys
import argparse

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
