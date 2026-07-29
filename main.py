import src.travel_planner.destination_weather as dw
import src.travel_planner.destination_prompt as dp
import src.travel_planner.chatgpt_packing_list_query as cgpt_plq
import src.travel_planner.packing_list_builder as plb


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
    packing_items = cgpt_plq.generate_packing_list(user_destination, forecast)
    print(f"\nitems to pack: {packing_items}\n")

    # choose your export target
    if todo_list_format == "MF":
        plb.export_to_text_file(user_destination, packing_items)
    elif todo_list_format == "AR":
        plb.push_to_apple_reminders(user_destination, packing_items)
