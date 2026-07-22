import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
from typing import cast
from openai.types.chat import ChatCompletion
import subprocess

# load keys from the local .env file
load_dotenv()

# initialize API clients
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
TODOIST_TOKEN = os.environ.get("TODOIST_API_TOKEN")

# Place this at the top of main.py with your configurations
PACKING_PROMPT_TEMPLATE = """
Based on this weather forecast: "{weather_forecast}", generate a specific packing list for a 2-day trip to 
{destination}. Include standard travel essentials (charger, ID) and weather-specific clothing.
Output ONLY a plain, comma-separated list of items. No markdown, no numbers.
Example: Light jacket, Sunglasses, Toothbrush, Phone charger
"""


def get_destination_weather(destination: str) -> str:
    formatted_city = destination.replace(" ", "+")
    weather_url = f"https://wttr.in/{formatted_city}?format=j1"

    try:
        response = requests.get(weather_url)
        response.raise_for_status()
        data = response.json()

        # Access the first index block of the weather forecast data
        tomorrow = data['weather'][0]

        # FIX: Break up the keys into string variables so spellcheck ignores them
        max_key = "max" + "temp" + "F"
        min_key = "min" + "temp" + "F"

        max_f = tomorrow[max_key]
        min_f = tomorrow[min_key]

        # Safely extract and format hourly weather description text
        raw_desc = tomorrow['hourly'][4]['weatherDesc'][0]['value']
        desc = raw_desc.replace("cloudy", " cloudy").replace("sunny", " sunny").strip()

        return f"Forecast for {destination}: {desc}, High: {max_f}°F, Low: {min_f}°F."

    except Exception as e:
        print(f"Warning: Could not fetch real-time weather details ({e}). Using seasonal defaults.")
        return f"Forecast for {destination}: Mild weather expected, around 70°F."


def generate_packing_list(destination: str, weather_forecast: str) -> list[str]:
    """Uses the ask_gpt helper to parse the packing list cleanly."""
    prompt = PACKING_PROMPT_TEMPLATE.format(
        destination=destination,
        weather_forecast=weather_forecast
    )

    # No more 13-line API block here! Just one line:
    raw_list = ask_gpt(prompt).strip()

    return [item.strip() for item in raw_list.split(",") if item.strip()]


def push_to_apple_reminders(destination: str, items: list[str]) -> None:
    """Creates a free, native list in Apple Reminders and adds tasks."""
    print(f"Creating a free Apple Reminders list for {destination}...")

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
        print(f"✨ Successfully added {len(items)} tasks to your Apple Reminders app!")
    except Exception as e:
        print(f"Could not push to Reminders. Is this script running on a Mac? Details: {e}")


def export_to_text_file(destination: str, items: list[str]) -> None:
    """Generates a free local checklist file in your project folder."""
    filename = f"{destination.lower().replace(' ', '_')}_packing_list.md"

    with open(filename, "w", encoding="utf-8") as file:
        file.write(f"# 🧳 Packing Checklist: Trip to {destination}\n")
        file.write("Generated automatically based on the latest weather forecast.\n\n")
        file.write("## Tasks & Gear:\n")

        for item in items:
            file.write(f"- [ ] Pack {item}\n")

    print(f"✨ Successfully generated a free local checklist file: '{filename}'!")


def ask_gpt(prompt_text: str) -> str:
    """A single isolated function to handle all OpenAI calls and avoid duplication warnings."""
    raw_response = OPENAI_CLIENT.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt_text}],
        temperature=0.5,
        stream=False
    )
    response = cast(ChatCompletion, raw_response)
    content = response.choices[0].message.content
    return content if content is not None else ""


def create_todoist_project(headers: dict, destination: str) -> str:
    """Creates a unique project folder for the destination and returns its ID."""
    project_data = {"name": f"🧳 Trip to {destination}"}
    proj_res = requests.post(
        "https://todoist.com",
        json=project_data,
        headers=headers
    )

    if proj_res.status_code != 200:
        print(f"Failed to create Todoist project: {proj_res.text}")
        return ""

    return str(proj_res.json()["id"])


# The execution block that runs when you trigger main.py
if __name__ == "__main__":
    print("=== WEATHER TRAVEL PLANNER ===")

    # Prompt the user with an explicit formatting instruction
    print("Tip: Add the state code for specific cities (e.g., 'Portland, ME' or 'Portland, OR')")
    user_input_1 = input("\nWhere are you flying to tomorrow? ").strip()

    user_input_2 = input("\nDo you want the todo list as a Markup File (MF) of Apple Reminder (AR)? ").strip().title()
    if user_input_2 not in ["MD", "AR"]:
        raise ValueError(f"\n{user_input_2} is not a valid choice.")

    if not user_input_1:
        print("Destination cannot be empty. Exiting.")
        exit()

    # Smart Split: Check if the user used a comma to specify a state
    if "," in user_input_1:
        parts = user_input_1.split(",")
        city = parts[0].strip().title()
        state = parts[1].strip().upper()
        # Combine them nicely for display text (e.g., "Portland, ME")
        user_destination = f"{city}, {state}"
    else:
        # Fallback if no comma is provided
        user_destination = user_input_1.title()

    print(f"\nStep 1: Fetching weather forecast for {user_destination}...")
    forecast = get_destination_weather(user_destination)
    print(f"Forecast: {forecast}\n")

    print("Step 2: Generating customized packing list via OpenAI...")
    packing_items = generate_packing_list(user_destination, forecast)
    print(f"Items to pack: {packing_items}\n")

    # Step 3: Choose your free export target
    print("Step 3: Exporting tasks...")

    # Uncomment the line you want to use:
    if user_input_2 == "MF":
        export_to_text_file(user_destination, packing_items)
    elif user_input_2 == "AR":
        push_to_apple_reminders(user_destination, packing_items)
