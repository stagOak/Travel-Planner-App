import sys
from pathlib import Path
import yaml

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
YAML_PATH = ROOT_DIR / "config.yaml"
ENV_PATH = ROOT_DIR / ".env"


def validate_environment():
    """Pure structural check: Verifies files and key matching without loading anything."""

    errors = []

    # verify config.yaml exists and parse it
    if not YAML_PATH.exists():
        print(f"\n[ERROR] missing critical configuration file: '{YAML_PATH.name}' at project root.")
        sys.exit(1)

    try:
        with open(YAML_PATH, "r") as file:
            config = yaml.safe_load(file) or {}
        active_key_name = config.get("active_key_name")
    except Exception as e:
        print(f"\n[ERROR] failed to parse config.yaml: {e}")
        sys.exit(1)

    if not active_key_name:
        errors.append(f"\n[ERROR] 'active_key_name' is empty or missing in config.yaml.")

    # verify .env exists and scan its text content for the key name
    if not ENV_PATH.exists():
        errors.append(f"\n[ERROR] missing secrets file: '{ENV_PATH.name}' at project root.")
    elif active_key_name:
        try:
            with open(ENV_PATH, "r") as file:
                env_content = file.read()

            # checks if the exact variable name (e.g., "OPENAI_API_KEY=") is in the file text
            if f"{active_key_name}=" not in env_content:
                errors.append(
                    f"\n[ERROR] key mismatch: config.yaml points to '{active_key_name}', "
                    f"but it was not found inside your .env file."
                )
        except Exception as e:
            print(f"\n[ERROR] failed to read .env file: {e}")
            sys.exit(1)

    # crash early if structural checks fail
    if errors:
        print("\n==========================================")
        print("      CRITICAL CONFIGURATION ERROR        ")
        print("==========================================")
        for error in errors:
            print(error)
        print("\nplease reference the API Configuration Guide in README.md to fix this.")
        print("==========================================\n")
        sys.exit(1)

    print(f"\n[SUCCESS] Configuration verified. Active provider: {active_key_name}")


# usage at script entry point
if __name__ == "__main__":
    validate_environment()
    # Your app runs safely below here using 'api_key'
