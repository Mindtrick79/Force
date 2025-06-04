import subprocess

def call_ollama(prompt, model_name="mistral"):
    cmd = ["ollama", "run", model_name, prompt]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        stdout, stderr = proc.communicate(timeout=30)
        if proc.returncode == 0 and stdout:
            print(f"Ollama output: {stdout.strip()}")
            return stdout.strip()
        else:
            print(f"Ollama error: {stderr}")
            return ""
    except Exception as e:
        print(f"Ollama error: {e}")
        return ""

if __name__ == "__main__":
    prompt = "Given the following info, what are the correct ZIP, City, and State?\nAddress: 1000 Market St, St. Louis\nCity: St. Louis\nState: MO\nZIP: \nRespond as: ZIP, City, State. If unknown, use blank."
    call_ollama(prompt) 