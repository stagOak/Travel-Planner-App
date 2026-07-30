import requests
import sys

import src.travel_planner.open_meteo_weather as bw

headers = {'User-Agent': 'Travel-Planner-App: steven.morin@comcast.net'}


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
        return bw.get_backup_weather(destination)

    except requests.exceptions.HTTPError as http_err:
        # this block catches all standard HTTP error statuses triggered by response.raise_for_status()
        # 4xx Client Errors and 5xx Server Errors
        print(f"\nrequests.exceptions.HTTPError - http_err: {http_err}")
        return bw.get_backup_weather(destination)

    except requests.exceptions.ConnectionError as connection_err:
        # this block catches foundational connection infrastructure failures before an HTTP code can even be issued
        print(f"\nrequests.exceptions.ConnectionError - connection_err: {connection_err}")
        return bw.get_backup_weather(destination)

    except requests.exceptions.RequestException as req_err:
        # this block is a "catch-all" for the requests library. it catches rare, library-specific errors that did not
        # fit into the three categories above
        print(f"\nrequests.exceptions.RequestException - req_exp: {req_err}")
        return bw.get_backup_weather(destination)

    except Exception as e:
        # this block handles internal Python runtime bugs rather than network/API codes. it catches things that would
        # completely crash your script
        sys.exit(f"\ninternal Python runtime bugs - e: {e}")
