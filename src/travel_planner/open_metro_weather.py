import requests
import sys
import argparse


WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    71: "Slight snow fall", 73: "Moderate snow fall", 75: "Heavy snow fall",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}


def fetch_coordinates(destination: str) -> tuple:
    """Queries Open-Meteo Geocoding API to return (lat, lon, name, admin1)."""

    geo_url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {
        "name": destination,
        "count": 1,
        "language": "en",
        "format": "json"
    }

    try:
        res = requests.get(geo_url, params=params, timeout=(3, 5))
        res.raise_for_status()

        try:
            data = res.json()
        except ValueError:
            sys.exit(f"\n[error] geocoding API returned a non-JSON payload.")

        if not data.get("results"):
            sys.exit(f"\ncould not resolve location '{destination}' on backup service.")

        lat = data["results"][0]["latitude"]
        lon = data["results"][0]["longitude"]
        name = data["results"][0]["name"]
        admin1 = data["results"][0]["admin1"]

        return lat, lon, name, admin1
    except requests.exceptions.Timeout as timeout_err:
        sys.exit(f"\nrequests.exceptions.Timeout - timeout_err: {timeout_err}")
    except requests.exceptions.HTTPError as http_err:
        sys.exit(f"\nrequests.exceptions.HTTPError - http_err: {http_err}")
    except requests.exceptions.ConnectionError as connection_err:
        sys.exit(f"\nrequests.exceptions.ConnectionError - connection_err: {connection_err}")
    except requests.exceptions.RequestException as req_err:
        sys.exit(f"\nrequests.exceptions.RequestException - req_exp: {req_err}")


def fetch_tomorrow_forecast(lat: float, lon: float) -> tuple:
    """Queries Open-Meteo Weather API using coordinates to return forecast data tuples."""

    weather_url = "https://api.open-meteo.com/v1/forecast"
    weather_params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weather_code",
        "temperature_unit": "fahrenheit",
        "forecast_days": 2
    }

    try:
        res = requests.get(weather_url, params=weather_params, timeout=(3, 5))
        res.raise_for_status()

        try:
            data = res.json()
        except ValueError:
            sys.exit(f"\n[Error] Weather API returned a non-JSON payload.")

        daily = data["daily"]
        tomorrow_max = daily["temperature_2m_max"][1]
        tomorrow_min = daily["temperature_2m_min"][1]
        tomorrow_code = daily["weather_code"][1]

        return tomorrow_max, tomorrow_min, tomorrow_code
    except requests.exceptions.Timeout as timeout_err:
        sys.exit(f"\nrequests.exceptions.Timeout - timeout_err: {timeout_err}")
    except requests.exceptions.HTTPError as http_err:
        sys.exit(f"\nrequests.exceptions.HTTPError - http_err: {http_err}")
    except requests.exceptions.ConnectionError as connection_err:
        sys.exit(f"\nrequests.exceptions.ConnectionError - connection_err: {connection_err}")
    except requests.exceptions.RequestException as req_err:
        sys.exit(f"\nrequests.exceptions.RequestException - req_exp: {req_err}")


def get_backup_weather(destination: str) -> str:
    """Fallback function that orchestrates coordinates and weather data fetching."""

    print(f"\n[backup] primary API failed. attempting fallback for {destination}...")

    # get destination coordinate extraction
    lat, lon, name, admin1 = fetch_coordinates(destination)
    print(f"\nbackup service {name}, {admin1} =? {destination}")

    # get destination weather forecat
    t_max, t_min, t_code = fetch_tomorrow_forecast(lat, lon)

    # decode descriptive code condition string assumes WMO_DESCRIPTIONS dictionary is defined globally
    tomorrow_desc = WMO_DESCRIPTIONS.get(t_code, f"Unknown condition ({t_code})")

    return f"forecast for {destination}: {tomorrow_desc}, high: {t_max}°F, low: {t_min}°F."


if __name__ == "__main__":
    """
    This code demonstrates the cli use of fetch_coordinates to query the Open-Meteo Weather API.
    """

    # initialize the argument parser
    parser = argparse.ArgumentParser()

    # add parameters to the argument parser
    parser.add_argument("destination", type=str, help="travel destination")
    parser.add_argument("-v", "--verbose", action="store_true", help="Toggle verbose mode (Flag)")

    # parse the arguments from the terminal
    args = parser.parse_args()

    # begin processing
    if args.verbose:
        print("\nopen metro is being queried for coordinates for {}...".format(args.destination))

    lat_, lon_, name_, admin1_ = fetch_coordinates(args.destination)
    print(lat_, lon_, name_, admin1_)
