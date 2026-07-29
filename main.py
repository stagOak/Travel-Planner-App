import src.travel_planner.travel_planner as tp
import src.travel_planner.destination_weather as dw
import src.travel_planner.destination_prompt as dp

# the execution block that runs when you trigger main.py
if __name__ == "__main__":

    print("\n\n=== weather travel planner ===")

    # get user travel destination and list format
    return_dict = dp.prompt_user()
    user_destination = return_dict["user_destination"]
    todo_list_format = return_dict["todo_list_format"]

    # get weather forcast for the travel destination
    forecast = dw.get_destination_weather(user_destination)
    print(f"\nforecast: {forecast}\n")

    # get packing list
    packing_items = tp.generate_packing_list(user_destination, forecast)
    print(f"\nitems to pack: {packing_items}\n")

    # choose your export target
    if todo_list_format == "MF":
        tp.export_to_text_file(user_destination, packing_items)
    elif todo_list_format == "AR":
        tp.push_to_apple_reminders(user_destination, packing_items)
