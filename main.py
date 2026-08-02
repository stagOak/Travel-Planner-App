import src.travel_planner.simple_destination_prompt as dp
import src.travel_planner.chatgpt_packing_list_query as cgpt_plq
import src.travel_planner.packing_list_document_builder as plb
import src.travel_planner.open_street_map_destination_prompt as osmdp
import src.travel_planner.open_meteo_weather as ow
import src.utils.config_and_api_key_validation as cv
from src.utils.logger_utils import setup_logger

# initialize logger
logger = setup_logger()


def main():

    cv.validate_environment()

    logger.info("Application started successfully.")
    try:
        print("\n=== weather travel planner ===")

        # get user travel destination and list format
        return_dict = dp.simple_user_destination_prompt()
        user_destination = return_dict["user_destination"]
        todo_list_format = return_dict["todo_list_format"]

        # fetch the 5 raw locations that match the input user destination
        location_options = osmdp.get_critical_location_options(user_destination)

        # funnel them into your interface prompt helper and select the one you wanted
        selected_location = osmdp.present_and_select_location(location_options)

        if selected_location:

            # Safely proceed with downstream data processing routing (e.g. Weather updates)
            print(f"Targeting coordinates: {selected_location['lat']}, {selected_location['lon']}")

            forecast = ow.get_open_meteo_destination_weather(user_destination, selected_location['lat'],
                                                             selected_location['lon'])

            print(f"\n{forecast}")

            # get packing list
            packing_items = cgpt_plq.generate_packing_list(user_destination, forecast)
            print(f"\nitems to pack: {packing_items}\n")

            # choose your export target
            if todo_list_format == "MF":
                plb.export_to_text_file(user_destination, packing_items)
            elif todo_list_format == "AR":
                plb.push_to_apple_reminders(user_destination, packing_items)
    except Exception as e:
        logger.error(f"Application crashed: {e}", exc_info=True)


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
