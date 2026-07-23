import travel_planner as tp


# the execution block that runs when you trigger main.py
if __name__ == "__main__":

    print("=== WEATHER TRAVEL PLANNER ===")

    print(f"\nPrompt User for travel destination and to do list format")
    return_dict = tp.prompt_user()
    user_destination = return_dict["user_destination"]
    todo_list_format = return_dict["todo_list_format"]

    print(f"\nStep 1: Fetching weather forecast for {user_destination}...")
    forecast = tp.get_destination_weather(user_destination)
    print(f"Forecast: {forecast}\n")

    print("Step 2: Generating customized packing list via OpenAI...")
    packing_items = tp.generate_packing_list(user_destination, forecast)
    print(f"Items to pack: {packing_items}\n")

    # Step 3: Choose your free export target
    print("Step 3: Exporting tasks...")

    # Uncomment the line you want to use:
    if todo_list_format == "MF":
        tp.export_to_text_file(user_destination, packing_items)
    elif todo_list_format == "AR":
        tp.push_to_apple_reminders(user_destination, packing_items)
