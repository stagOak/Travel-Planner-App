import os
import requests
from openai import OpenAI
from typing import cast
from openai.types.chat import ChatCompletion
import subprocess
from dotenv import load_dotenv
from pathlib import Path
import sys

# load keys from the local .env file
load_dotenv()

# initialize API clients
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# text for LLM prompt - used in generate_packing_list() function
PACKING_PROMPT_TEMPLATE = """
Based on this weather forecast: "{weather_forecast}", generate a specific packing list for a 2-day trip to 
{destination}. Include standard travel essentials (charger, ID) and weather-specific clothing.
Output ONLY a plain, comma-separated list of items. No markdown, no numbers.
Example: Light jacket, Sunglasses, Toothbrush, Phone charger
"""

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

headers = {'User-Agent': 'Travel-Planner-App: steven.morin@comcast.net'}


def prompt_user():

    print(f"\nprompt user for travel destination and to do list format")

    # prompt the user for a travel destination
    print("\ntip: add the state code for specific cities (e.g., 'Portland, ME' or 'Portland, OR')")
    destination = input("\nwhere are you traveling to tomorrow? ").strip()
    if not destination:
        sys.exit(f"\ndestination entered was {destination} - cannot be empty.")

    # prompt the user for an explicit formatting instruction
    todo_list_format = input("\ndo you want the todo list as a markup file (MF/mf) or apple "
                             "reminder (AR/ar)? ").strip().upper()
    if todo_list_format not in ["MF", "AR"]:
        raise ValueError(f"\n{todo_list_format} is not a valid choice.")

    # smart split: check if the user used a comma to specify a state
    if "," in destination:
        parts = destination.split(",")
        city = parts[0].strip().title()
        state = parts[1].strip().upper()
        # combine them nicely for display text (e.g., "Portland, ME")
        user_destination = f"{city}, {state}"
    else:
        # fallback if no comma is provided
        user_destination = destination.title()

    return {
        "user_destination": user_destination,
        "todo_list_format": todo_list_format
    }


def report_out_nearest_area(destination: str, weather_url: str, data: dict) -> None:

    # extract the nearest area data from the payload
    area_name = data['nearest_area'][0]['areaName'][0]['value']
    region = data['nearest_area'][0]['region'][0]['value']
    country = data['nearest_area'][0]['country'][0]['value']
    lat = data['nearest_area'][0]['latitude']
    lon = data['nearest_area'][0]['longitude']

    # print out destination data
    print(f"\nyou entered a request for a weather forcast that was interpreted by this code as {destination}."
          f"\nthis is the request url that the code generated {weather_url}"
          f"\nthe request response returned a nearest area of {area_name} in the region {region} in the country of "
          f"{country}."
          f"\nlatitude {lat} and longitude {lon}.")


def unpack_wttr_in_response(destination: str, weather_url: str, data: dict):

    report_out_nearest_area(destination, weather_url, data)

    # access the first index block of the weather forecast data
    tomorrow = data['weather'][0]

    # break up the keys into string variables so spellcheck ignores them then extract forecast high and low temps
    max_key = "max" + "temp" + "F"
    min_key = "min" + "temp" + "F"
    max_f = tomorrow[max_key]
    min_f = tomorrow[min_key]

    # extract and format hourly weather description text
    raw_desc = tomorrow['hourly'][4]['weatherDesc'][0]['value']
    desc = raw_desc.strip()

    return {
        "destination": destination,
        "desc": desc,
        "max_f": max_f,
        "min_f": min_f
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


# def get_backup_weather(destination: str) -> str:
#     """Fallback function that runs if wttr.in fails."""
#
#     print(f"\n[backup] primary API failed. attempting fallback for {destination}...")
#
#     # open-Meteo needs lat/long coordinates, so we query their free geocoding endpoint first
#     geo_url = "https://geocoding-api.open-meteo.com/v1/search"
#     params = {
#         "name": destination,
#         "count": 5,
#         "language": "en",
#         "format": "json"
#     }
#
#     try:
#         geo_res = requests.get(geo_url, params=params, timeout=(3, 5))
#
#         geo_res.raise_for_status()
#         geo_data = geo_res.json()
#
#         if not geo_data.get("results"):
#             sys.exit(f"could not resolve location {destination} on backup service")
#
#         lat = geo_data["results"][0]["latitude"]
#         lon = geo_data["results"][0]["longitude"]
#         name = geo_data["results"][0]["name"]
#         admin1 = geo_data["results"][0]["admin1"]
#
#         print(f"\nbackup service {name}, {admin1} =? {destination}")
#
#         # fetch the actual current weather using the retrieved coordinates
#         weather_url = "https://api.open-meteo.com/v1/forecast"
#         weather_params = {
#             "latitude": lat,
#             "longitude": lon,
#             "daily": "temperature_2m_max,temperature_2m_min,weather_code",
#             "temperature_unit": "fahrenheit",
#             "forecast_days": 2
#
#         }
#         weather_res = requests.get(weather_url, params=weather_params, timeout=(3, 5))
#         weather_res.raise_for_status()
#         weather_data = weather_res.json()
#         daily = weather_data["daily"]
#
#         tomorrow_max = daily["temperature_2m_max"][1]
#         tomorrow_min = daily["temperature_2m_min"][1]
#         tomorrow_code = daily["weather_code"][1]
#
#         # Translate WMO integer to string description
#         tomorrow_desc = WMO_DESCRIPTIONS.get(tomorrow_code, f"Unknown condition ({tomorrow_code})")
#
#         return f"forecast for {destination}: {tomorrow_desc}, high: {tomorrow_max}°F, low: {tomorrow_min}°F."
#
#     except requests.exceptions.RequestException as fallback_err:
#         sys.exit(f"\nbackup API also failed: {fallback_err}")


def get_destination_weather(destination: str) -> str:

    print(f"\nstep 1: fetching weather forecast for {destination}...")

    formatted_city = destination.replace(" ", "+").replace(",", "")
    weather_url = f"https://wttr.in/{formatted_city}?format=j1"

    try:

        # fire the request with strict connection and read timeouts - (3, 5) means: 3 seconds to establish connection,
        # 5 seconds to receive data. if wttr.in freezes, it immediately aborts instead of hanging.
        response = requests.get(weather_url, headers=headers, timeout=(3, 5))

        # check for HTTP errors(4xx or 5xx codes) - throw exception for unsuccessful status code
        response.raise_for_status()

        # convert from JSON to python dictionary or list
        data = response.json()

        # if we get here the request was completed successfully
        return_dict = unpack_wttr_in_response(destination, weather_url, data)
        destination = return_dict["destination"]
        desc = return_dict["desc"]
        max_f = return_dict["max_f"]
        min_f = return_dict["min_f"]

        return f"forecast for {destination}: {desc}, high: {max_f}°F, low: {min_f}°F."

    except requests.exceptions.Timeout as timeout_err:
        # this block catches network-layer timing failures based on our timeout=(3, 5) configuration
        print(f"\nrequests.exceptions.Timeout - timeout_err: {timeout_err}")
        return get_backup_weather(destination)

    except requests.exceptions.HTTPError as http_err:
        # this block catches all standard HTTP error statuses triggered by response.raise_for_status()
        # 4xx Client Errors and 5xx Server Errors
        print(f"\nrequests.exceptions.HTTPError - http_err: {http_err}")
        return get_backup_weather(destination)

    except requests.exceptions.ConnectionError as connection_err:
        # this block catches foundational connection infrastructure failures before an HTTP code can even be issued
        print(f"\nrequests.exceptions.ConnectionError - connection_err: {connection_err}")
        return get_backup_weather(destination)

    except requests.exceptions.RequestException as req_err:
        # this block is a "catch-all" for the requests library. it catches rare, library-specific errors that did not
        # fit into the three categories above
        print(f"\nrequests.exceptions.RequestException - req_exp: {req_err}")
        return get_backup_weather(destination)

    except Exception as e:
        # this block handles internal Python runtime bugs rather than network/API codes. it catches things that would
        # completely crash your script
        sys.exit(f"\ninternal Python runtime bugs - e: {e}")


def ask_gpt(prompt_text: str) -> str:
    """a single isolated function to handle all OpenAI calls"""

    # sends a single-turn prompt to OpenAI's model, waiting for a complete, moderately creative text response all at
    # once. a single-turn prompt is a one-time, standalone input given to an AI model that results in a single response,
    # with no ongoing conversation or memory of past chats
    raw_response = OPENAI_CLIENT.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.5,
        stream=False
    )

    #  tell static type checker to treat the raw_response variable as a ChatCompletion object
    response = cast(ChatCompletion, raw_response)

    # extracts the text answer generated by the AI model from an API response
    content = response.choices[0].message.content

    return content if content is not None else ""


def generate_packing_list(destination: str, weather_forecast: str) -> list[str]:
    """uses the ask_gpt helper to parse the packing list cleanly."""

    print("\nstep 2: generating customized packing list via OpenAI...")

    prompt = PACKING_PROMPT_TEMPLATE.format(
        destination=destination,
        weather_forecast=weather_forecast
    )

    # ask an AI model for a list of things to pack
    raw_list = ask_gpt(prompt).strip()

    return [item.strip() for item in raw_list.split(",") if item.strip()]


def push_to_apple_reminders(destination: str, items: list[str]) -> None:
    """creates a free, native list in Apple Reminders and adds tasks."""

    print(f"\nstep 3: creating a free apple reminders list for {destination}...")

    # AppleScript commands to create a new list and insert tasks
    applescript = f'''
    tell application "Reminders"
        if not (exists list "{destination} Trip") then
            make new list with properties {{name:"{destination} Trip"}}
        end if
        tell list "{destination} Trip"
            {chr(10).join([f'make new reminder with properties {{name:"Pack {item}"}}' for item in items])}
        end tell
    end tell
    '''

    try:
        subprocess.run(["osascript", "-e", applescript], check=True, capture_output=True)
        print(f"\nsuccessfully added {len(items)} tasks to your Apple Reminders app!")
    except Exception as e:
        print(f"\ncould not push to reminders. is this script running on a mac? details: {e}")


def export_to_text_file(destination: str, items: list[str]) -> None:
    """generates a local checklist file in your project folder."""

    print(f"\nstep 3: creating a mark down (.md) reminders list for {destination}...")

    filename = f"{destination.lower().replace(' ', '_').replace(',', "")}_packing_list.md"

    script_dir = Path(__file__).resolve()
    save_path = script_dir.parents[2] / "src" / "travel_planner" / "data" / "processed" / filename
    with open(save_path, "w", encoding="utf-8") as file:
        file.write(f"# 🧳 Packing Checklist: Trip to {destination}\n")
        file.write("Generated automatically based on the latest weather forecast.\n\n")
        file.write("## Tasks & Gear:\n")
        for item in items:
            file.write(f"- [ ] Pack {item}\n")

    print(f"\nsuccessfully generated a free local checklist file: '{filename}'")


if __name__ == "__main__":
    pass
