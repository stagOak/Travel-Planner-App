# Travel Planner Application

## This project provides a simple example of Master Tool-Chaining (The Gateway to Workflows)

Automated workflows rely on one tool feeding data directly into another.

The Concept: The GPT calls Tool A, processes the output, and automatically feeds it into Tool B without user intervention.

Practice Project: Create a "Weather Travel Planner." 

When a user says "I'm traveling to Chicago tomorrow," the GPT should:

1. Call your Weather MCP to check the destination forecast.

2. Pass that forecast to a Packing List MCP to auto-generate a custom checklist.

3. Pass the checklist to a to do list creation tool MCP to create a task list for the user.

In this project step 2 is the only step that involves ChatGPT. 

In step 2 a prompt is programmatically sent to OpenAI ChatGPT requesting the generation of a packing list. 

The response (a packing list) is then sent to a tool that generates either a .md file or an Apple Reminder for the user.

## System Component Architecture
<img src="images/system_component_architecture.png" alt="System Component Architecture" width="60%">
<img src="images/system_component_architecture_legend.png" alt="System Component Architecture Legend" width="60%">

## Screenshot of Execution
<img src="images/screenshot_of_execution.png" alt="Screenshot of Execution" width="60%">

## Screenshot of .md Packing List
<img src="images/md_file_packing_list.png" alt="Screenshot of .md Packing List" width="60%">

## Screenshot of Apple Reminder Packing List
<img src="images/apple_reminder_packing_list.png" alt="Screenshot of Apple reminder Packing List" width="60%">

# Prerequisites

## Set Up a Virtual Environment

### Step 1: Create the Virtual Environment
Run the following command in your project root directory:

* **macOS / Linux:**
  ```bash
  python -m venv .venv
  ```
  or
* ```bash
  python3 -m venv .venv
  ```

### Step 2: Activate the Environment

* **macOS / Linux:**
  ```bash
  source .venv/bin/activate
  ```

*Your terminal prompt will now show `(.venv)`, indicating the environment is active.*

### Step 3: Install Dependencies from `requirements.txt`

```bash
pip install -r requirements.txt
```

## OpenAI API Account Setup

Follow these steps to create an account and fund it to start making API calls.

### 1. Create a Free Account
* Visit the [OpenAI Developer Platform](https://openai.com).
* Create an account.

### 2. Add Funds to Your Balance
OpenAI requires a minimum pre-funded balance of $6 to activate API access for paid models.

### 3. Set Spending Limits (Crucial Step)
Always set usage thresholds to avoid unexpected charges from runaway loops or compromised API keys.

## API Configuration Guide

This project separates public configuration from private credentials. Follow these two quick steps to set up your environment:

### 1. Set Up Your Private Keys
Private credentials must be stored locally in an environment file. They are explicitly blocked from git tracking to prevent accidental leaks.
* Create a file named `.env` in the project **root directory**.
* Open the `.env` file and add your actual API keys using this format:
  ```text
  OPENAI_API_KEY=sk-your-actual-secret-key-here
  ```

### 2. Choose Your Active Provider
You can publicly swap between different API providers without changing any underlying source code.
* Open the `config.yaml` file in the project **root directory**.
* Update the `active_key_name` property to match the text name of the variable you defined inside your `.env` file:
  ```yaml
  active_key_name: "OPENAI_API_KEY"
  ```

> **Security Warning:** Never commit your `.env` file to your GitHub/GitLab repository. `.env` is listed inside the `.gitignore` file.

## Running the Application

To run the project, always execute main.py from your terminal at the **project root directory** (where your `config.yaml` and `.env` files live). This ensures all relative configuration paths resolve correctly.

### Execution Command

Open your terminal, navigate to the project root, and execute:

```bash
python main.py
```

_Note: Depending on your system configuration, you may need to use `python3 main.py`._

### What to Expect on Startup

* **Success:** If your configurations match up, your terminal will print:
  ```text
  Configuration verified. Active provider: OPENAI_API_KEY
  ```
* **Failure:** If your setup is incorrect, the program will gracefully halt and print step-by-step instructions on what needs to be fixed in your `.env` or `config.yaml` file.

