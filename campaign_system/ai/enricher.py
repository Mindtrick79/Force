# AI enrichment and segmentation logic

import os
import pandas as pd
from dotenv import load_dotenv
import openai
import requests
from pathlib import Path
import re
import subprocess

def load_api_keys():
    env_paths = [
        Path(__file__).parent.parent / '.env',
        Path(__file__).parent.parent.parent / '.env'
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(dotenv_path=env_path)
    return os.getenv('OPENAI_API_KEY'), os.getenv('GOOGLE_MAPS_API_KEY')

def call_openai(prompt, api_key):
    import openai
    client = openai.OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": "You are a helpful assistant for lead enrichment."},
                  {"role": "user", "content": prompt}],
        max_tokens=50
    )
    return response.choices[0].message.content.strip()

def call_google_maps(address, city, state, api_key):
    # Build address string
    address_str = f"{address}, {city}, {state}"
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address_str)}&key={api_key}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data['status'] == 'OK':
            for comp in data['results'][0]['address_components']:
                if 'postal_code' in comp['types']:
                    zip_code = comp['long_name']
                    if re.match(r'^\d{5}$', zip_code):
                        return zip_code
        return None
    except Exception as e:
        print(f"Google Maps API error: {e}")
        return None

def call_google_maps_full(address, city, state, zip_code, api_key):
    # Build address string with available info
    parts = [address, city, state, zip_code]
    address_str = ', '.join([str(p) for p in parts if p])
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={requests.utils.quote(address_str)}&key={api_key}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if data['status'] == 'OK':
            comps = data['results'][0]['address_components']
            zip_val = city_val = state_val = ''
            for comp in comps:
                if 'postal_code' in comp['types']:
                    zip_val = comp['long_name']
                if 'locality' in comp['types']:
                    city_val = comp['long_name']
                if 'administrative_area_level_1' in comp['types']:
                    state_val = comp['short_name']
            return zip_val, city_val, state_val
        return None, None, None
    except Exception as e:
        print(f"Google Maps API error: {e}")
        return None, None, None

def get_col(row, options):
    for opt in options:
        if opt in row and pd.notna(row[opt]) and str(row[opt]).strip():
            return str(row[opt]).strip()
    return ''

def set_col(row, options, value):
    for opt in options:
        if opt in row:
            row[opt] = value
            return
    # If none found, set the first option as new column
    row[options[0]] = value

def enrich_zip(row, gmaps_key, openai_key, debug=False, log_file=None):
    zip_val = str(row.get('Zip', '')).strip()
    address = str(row.get('Service Address', '')).strip()
    city = str(row.get('Service Address City', '')).strip()
    state = str(row.get('State', '')).strip()
    # Only enrich if we have enough info
    if (not zip_val or not re.match(r'^\d{5}$', zip_val)) and (address or city or state):
        # Try Google Maps first
        zip_gmaps = call_google_maps(address, city, state, gmaps_key) if gmaps_key else None
        if zip_gmaps:
            row['Zip'] = zip_gmaps
            source = 'Google Maps'
        else:
            # Fallback to OpenAI
            prompt = f"Given the following info, what is the correct 5-digit ZIP code?\n"
            prompt += f"Address: {address}\nCity: {city}\nState: {state}\nRespond with only the ZIP code."
            try:
                result = call_openai(prompt, openai_key)
                zip_ai = re.findall(r'\d{5}', result)
                if zip_ai:
                    row['Zip'] = zip_ai[0]
                    source = 'OpenAI'
                else:
                    row['Zip'] = ''
                    source = 'Not found'
            except Exception as e:
                row['Zip'] = ''
                source = f'Error: {e}'
        # Logging
        log_entry = f"ENRICH ZIP: {address}, {city}, {state}\nResult: {row['Zip']} (Source: {source})\n{'-'*40}\n"
        if debug:
            print(log_entry)
        if log_file:
            with open(log_file, 'a') as f:
                f.write(log_entry)
    return row

def enrich_location(row, api_key, debug=False, log_file=None):
    zip_val = row.get('zip') or row.get('service_address_zip')
    state_val = row.get('state') or row.get('service_address_state')
    city_val = row.get('region') or row.get('service_address_city')
    if (not zip_val) or (not state_val) or (not city_val):
        prompt = f"Given the following info, fill in missing ZIP, State, and City if possible.\n"
        prompt += f"Address: {row.get('service_address', '')}\n"
        prompt += f"City: {row.get('service_address_city', '')}\n"
        prompt += f"State: {row.get('service_address_state', '')}\n"
        prompt += f"ZIP: {row.get('service_address_zip', '')}\n"
        prompt += f"Phone: {row.get('phone_clean', '')}\n"
        prompt += f"Respond as: ZIP, State, City. If unknown, use blank."
        try:
            result = call_openai(prompt, api_key)
            log_entry = f"PROMPT:\n{prompt}\nRESPONSE:\n{result}\n{'-'*40}\n"
            if debug:
                print(log_entry)
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(log_entry)
            parts = [x.strip() for x in result.split(',')]
            zip_code, state, city = '', '', ''
            if len(parts) == 3:
                zip_code, state, city = parts
            if not zip_val:
                row['zip'] = zip_code
            if not state_val:
                row['state'] = state
            if not city_val:
                row['region'] = city
        except Exception as e:
            error_msg = f"AI enrichment failed: {e}\nPROMPT:\n{prompt}\n"
            print(error_msg)
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(error_msg)
    return row

def tag_lead(row):
    # Example: Tag high value if company present, cold if missing phone/email
    tags = []
    if row.get('company') and isinstance(row['company'], str) and len(row['company']) > 0:
        tags.append('High Value')
    if not row.get('email_clean') and not row.get('phone_clean'):
        tags.append('Cold Lead')
    row['tags'] = ';'.join(tags)
    return row

def call_ollama(prompt, model_name="mistral"):
    cmd = ["ollama", "run", model_name, prompt]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(timeout=30)
        if proc.returncode == 0 and stdout:
            return stdout.strip()
        else:
            print(f"Ollama error: {stderr}")
            return ""
    except Exception as e:
        print(f"Ollama error: {e}")
        return ""

def enrich_row_full(row, gmaps_key, openai_key, debug=False, log_file=None):
    zip_opts = ['zip', 'Zip', 'service_address_zip']
    city_opts = ['region', 'Region', 'service_address_city', 'Service Address City']
    state_opts = ['state', 'State', 'service_address_state', 'Service Address State']
    address_opts = ['service_address', 'Service Address']
    zip_val = get_col(row, zip_opts)
    city = get_col(row, city_opts)
    state = get_col(row, state_opts)
    address = get_col(row, address_opts)
    needs_zip = not zip_val or not re.match(r'^\d{5}$', zip_val)
    needs_city = not city
    needs_state = not state
    if needs_zip or needs_city or needs_state:
        zip_g, city_g, state_g = call_google_maps_full(address, city, state, zip_val, gmaps_key) if gmaps_key else (None, None, None)
        updated = False
        if needs_zip and zip_g and re.match(r'^\d{5}$', zip_g):
            set_col(row, zip_opts, zip_g)
            updated = True
        if needs_city and city_g:
            set_col(row, city_opts, city_g)
            updated = True
        if needs_state and state_g:
            set_col(row, state_opts, state_g)
            updated = True
        source = 'Google Maps' if updated else 'Not found'
        if (needs_zip and (not get_col(row, zip_opts) or not re.match(r'^\d{5}$', get_col(row, zip_opts)))) or (needs_city and not get_col(row, city_opts)) or (needs_state and not get_col(row, state_opts)):
            prompt = f"Given the following info, what are the correct ZIP, City, and State?\n"
            prompt += f"Address: {address}\nCity: {city}\nState: {state}\nZIP: {zip_val}\nRespond as: ZIP, City, State. If unknown, use blank."
            result = call_ollama(prompt)
            parts = [x.strip() for x in result.split(',')]
            if len(parts) == 3:
                zip_ai, city_ai, state_ai = parts
                if needs_zip and re.match(r'^\d{5}$', zip_ai):
                    set_col(row, zip_opts, zip_ai)
                    updated = True
                if needs_city and city_ai:
                    set_col(row, city_opts, city_ai)
                    updated = True
                if needs_state and state_ai:
                    set_col(row, state_opts, state_ai)
                    updated = True
            source = 'Ollama' if updated else 'Not found'
            log_entry = f"ENRICH: {address}, {city}, {state}, {zip_val}\nResult: ZIP={get_col(row, zip_opts)}, City={get_col(row, city_opts)}, State={get_col(row, state_opts)} (Source: {source})\n{'-'*40}\n"
            if debug:
                print(log_entry)
            if log_file:
                with open(log_file, 'a') as f:
                    f.write(log_entry)
    return row

def enrich_and_sort(input_path, output_path):
    openai_key, gmaps_key = load_api_keys()
    df = pd.read_csv(input_path)
    log_file = os.path.join(os.path.dirname(__file__), 'enrichment_debug.log')
    open(log_file, 'w').close()
    debug_count = 0
    def enrich_row(row):
        nonlocal debug_count
        debug = False
        log = None
        if debug_count < 10:
            debug = True
            log = log_file
            debug_count += 1
        return enrich_row_full(row, gmaps_key, openai_key, debug=debug, log_file=log)
    df = df.apply(enrich_row, axis=1)
    # Sort by ZIP (use the first found zip column)
    zip_col = None
    for col in ['zip', 'Zip', 'service_address_zip']:
        if col in df.columns:
            zip_col = col
            break
    if zip_col:
        df = df.sort_values(by=zip_col, na_position='last')
    df.to_csv(output_path, index=False)
    print(f"Enriched and sorted leads saved to {output_path}")
    print(f"Sample:\n{df.head(3)}")

if __name__ == '__main__':
    input_csv = os.path.join(os.path.dirname(__file__), '../data/leads_cleaned.csv')
    output_csv = os.path.join(os.path.dirname(__file__), '../data/leads_enriched.csv')
    enrich_and_sort(input_csv, output_csv)
