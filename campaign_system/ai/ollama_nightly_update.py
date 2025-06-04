import json
import os
from dotenv import load_dotenv
from openai import OpenAI
from datetime import datetime

TRAINING_DATA_FILE = os.path.join(os.path.dirname(__file__), 'ollama_training_data.json')

# Load API key
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=OPENAI_API_KEY)

def load_training_data():
    if os.path.exists(TRAINING_DATA_FILE):
        with open(TRAINING_DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_training_data(data):
    with open(TRAINING_DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"[{datetime.now()}] Training data updated.")

def fetch_new_examples():
    # Placeholder: In production, this could analyze recent errors, logs, or gaps
    # For now, we'll just use a static prompt
    prompts = [
        "Given the following info, what are the correct ZIP, City, and State?\nAddress: 1000 Market St, St. Louis\nCity: St. Louis\nState: MO\nZIP: \nRespond as: ZIP, City, State. If unknown, use blank.",
        "Given the following info, what are the correct ZIP, City, and State?\nAddress: 1 Cardinal Way, St. Louis\nCity: St. Louis\nState: MO\nZIP: \nRespond as: ZIP, City, State. If unknown, use blank."
    ]
    examples = []
    for prompt in prompts:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for lead enrichment. Respond with only the ZIP, City, State as a comma-separated string."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=50
        )
        completion = response.choices[0].message.content.strip()
        examples.append({"prompt": prompt, "completion": completion})
    return examples

def nightly_update():
    data = load_training_data()
    new_examples = fetch_new_examples()
    # Avoid duplicates
    for ex in new_examples:
        if ex not in data:
            data.append(ex)
    save_training_data(data)

if __name__ == "__main__":
    nightly_update() 