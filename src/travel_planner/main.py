import os
from openai import OpenAI
from dotenv import load_dotenv

import travel_planner as tp

# load keys from the local .env file
load_dotenv()

# initialize API clients
OPENAI_CLIENT = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


# the execution block that runs when you trigger main.py
if __name__ == "__main__":

    print("=== WEATHER TRAVEL PLANNER ===")

    # Prompt the user with an explicit formatting instruction
    print("Tip: Add the state code for specific cities (e.g., 'Portland, ME' or 'Portland, OR')")
    user_input_1 = input("\nWhere are you flying to tomorrow? ").strip()

    user_input_2 = input("\nDo you want the todo list as a Markup File (MF) of Apple Reminder (AR)? ").strip().upper()
    if user_input_2 not in ["MF", "AR"]:
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
    forecast = tp.get_destination_weather(user_destination)
    print(f"Forecast: {forecast}\n")

    print("Step 2: Generating customized packing list via OpenAI...")
    packing_items = tp.generate_packing_list(user_destination, forecast)
    print(f"Items to pack: {packing_items}\n")

    # Step 3: Choose your free export target
    print("Step 3: Exporting tasks...")

    # Uncomment the line you want to use:
    if user_input_2 == "MF":
        tp.export_to_text_file(user_destination, packing_items)
    elif user_input_2 == "AR":
        tp.push_to_apple_reminders(user_destination, packing_items)
