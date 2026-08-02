import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Find the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
YAML_PATH = ROOT_DIR / "config.yaml"
ENV_PATH = ROOT_DIR / ".env"


def get_secret_key():

    # load the single .env file into the system environment
    load_dotenv(dotenv_path=ENV_PATH)

    # read the choice from the non-hidden config.yaml
    with open(YAML_PATH, "r") as file:
        config = yaml.safe_load(file)

    target_variable = config.get("active_key_name")

    # 3. Pull the actual key from the environment based on that choice
    api_key = os.getenv(target_variable)

    if not api_key:
        raise ValueError(f"key for '{target_variable}' not found in .env file.")

    return api_key


if __name__ == "__main__":
    api_key_ = get_secret_key()
    print(api_key_)
