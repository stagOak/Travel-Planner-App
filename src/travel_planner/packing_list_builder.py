import subprocess
from pathlib import Path


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
    save_path = script_dir.parents[2] / "data" / "processed" / filename
    with open(save_path, "w", encoding="utf-8") as file:
        file.write(f"# 🧳 Packing Checklist: Trip to {destination}\n")
        file.write("Generated automatically based on the latest weather forecast.\n\n")
        file.write("## Tasks & Gear:\n")
        for item in items:
            file.write(f"- [ ] Pack {item}\n")

    print(f"\nsuccessfully generated a free local checklist file: '{filename}'")
