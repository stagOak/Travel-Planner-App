import sys


def simple_user_destination_prompt():

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
