import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from .test_ollama import call_ollama

TRAINING_DATA = [
    {
        "prompt": "Given the following info, what are the correct ZIP, City, and State?\nAddress: 722 Aramis Drive, Creve Coeur 63141\nCity: Creve Coeur\nState: \nZIP: 63141\nRespond as: ZIP, City, State. If unknown, use blank.",
        "completion": "63141, Creve Coeur, MO"
    },
    {
        "prompt": "Given the following info, what are the correct ZIP, City, and State?\nAddress: 519 BENTON ST, VALLEY PARK 63088\nCity: VALLEY PARK\nState: \nZIP: 63088\nRespond as: ZIP, City, State. If unknown, use blank.",
        "completion": "63088, Valley Park, MO"
    },
    # Add more examples as needed
]

def save_training_data(filename="ollama_training_data.json"):
    with open(filename, "w") as f:
        json.dump(TRAINING_DATA, f, indent=2)
    print(f"Training data saved to {filename}")

def load_api_key():
    load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
    return os.getenv('OPENAI_API_KEY')

def fetch_example_from_chatgpt(prompt, api_key=None):
    if api_key is None:
        api_key = load_api_key()
    if not api_key:
        print("No OpenAI API key found.")
        return None
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant for lead enrichment. Respond with only the ZIP, City, State as a comma-separated string."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50
    )
    completion = response.choices[0].message.content.strip()
    return {"prompt": prompt, "completion": completion}

def add_chatgpt_example():
    prompt = input("Enter a prompt for ChatGPT (or leave blank to use default): ")
    if not prompt:
        prompt = "Given the following info, what are the correct ZIP, City, and State?\nAddress: 123 Main St, Springfield\nCity: Springfield\nState: IL\nZIP: \nRespond as: ZIP, City, State. If unknown, use blank."
    example = fetch_example_from_chatgpt(prompt)
    if example:
        TRAINING_DATA.append(example)
        print(f"Added example: {example}")
        save_training_data()

def enrich_lead(lead):
    prompt = "Given the following info, what are the correct ZIP, City, and State?\nAddress: {}\nCity: {}\nState: {}\nZIP: {}\nRespond as: ZIP, City, State. If unknown, use blank.".format(lead.get("address", ""), lead.get("city", ""), lead.get("state", ""), lead.get("zip", ""))
    result = call_ollama(prompt)
    if result:
        # (Assume result is a comma-separated string, e.g. "63101, St. Louis, MO")
        parts = [x.strip() for x in result.split(",")]
        if len(parts) >= 3:
            lead["zip"] = parts[0]
            lead["city"] = parts[1]
            lead["state"] = parts[2]
    return lead

if __name__ == "__main__":
    print("1. Save current training data\n2. Add new example from ChatGPT\n")
    choice = input("Choose an option: ")
    if choice == '2':
        add_chatgpt_example()
    else:
        save_training_data() 