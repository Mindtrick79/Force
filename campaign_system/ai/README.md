# AI Enrichment Module (campaign_system/ai)

## Overview

This module uses Ollama (with GPU acceleration) to locally enrich lead data (ZIP, city, state) using a fine-tuned Mistral model. In addition, a nightly update script (ollama_nightly_update.py) fetches new enrichment examples from ChatGPT (OpenAI) and updates the training data.

## Prerequisites

- Python 3 (with a virtual environment (venv) activated)
- Ollama (server running, e.g. via `ollama serve`)
- An OpenAI API key (stored in a `.env` file in the project root) for nightly updates.

## Workflow

### 1. Local Enrichment (Ollama)

- **Test Enrichment:**  
  Run the test script (test_ollama.py) to verify that Ollama (using GPU) is working:
  ```bash
  python3 campaign_system/ai/test_ollama.py
  ```
  (Ensure that the Ollama server is running (e.g. via `ollama serve`) and that your GPU is detected.)

- **Integrate Enrichment:**  
  The function `enrich_lead(lead)` (in ollama_trainer.py) uses Ollama (via test_ollama.call_ollama) to update a lead's ZIP, city, and state fields.

### 2. Nightly Update (ollama_nightly_update.py)

- **Purpose:**  
  Every night (scheduled via cron) the script fetches new enrichment examples from ChatGPT (using your OpenAI API key) and appends them to the training data (ollama_training_data.json).

- **Cron Setup:**  
  (Example crontab entry (adjust paths as needed):)
  ```
  0 2 * * * cd /home/charles/AI\ Projects/FORCE && /home/charles/AI\ Projects/FORCE/venv/bin/python campaign_system/ai/ollama_nightly_update.py >> /home/charles/AI\ Projects/FORCE/logs/ollama_update.log 2>&1
  ```

- **Logs:**  
  Output (and errors) are logged to `/home/charles/AI Projects/FORCE/logs/ollama_update.log`.

### 3. GPU Utilization

- Ollama (when running) uses your NVIDIA GPU (e.g. "NVIDIA GeForce RTX 3050 Ti Laptop GPU") for inference.  
- (You can monitor GPU usage via tools like `nvidia-smi`.)

## Files

- **test_ollama.py:**  
  A minimal script to test Ollama's local enrichment (using a sample prompt).

- **ollama_trainer.py:**  
  Contains the integration (enrich_lead) and functions to save/load training data (and fetch new examples from ChatGPT).

- **ollama_nightly_update.py:**  
  A scheduled script (via cron) that fetches new enrichment examples from ChatGPT and updates the training data.

- **ollama_training_data.json:**  
  (Generated) JSON file containing the training examples (prompt/completion pairs).

- **.env:**  
  (Not committed) Contains your OpenAI API key (for nightly updates).

- **.gitignore:**  
  (Already set up) Ignores (among others) the .env file and logs.

## Next Steps

- (Optional) Add post-processing (e.g. remove extra commentary) on Ollama's output.
- (Optional) Further fine-tune or expand the training data.

## GitHub Deployment

### Packing and Pushing to GitHub

1. **Ensure your .env (with your OpenAI API key) is ignored (via .gitignore) so that it isn't committed.**

2. **Commit your changes (for example, using the following commands):**

   ```bash
   # (Ensure you are in the project root, e.g. /home/charles/AI Projects/FORCE)
   git add campaign_system/ai/*.py campaign_system/ai/README.md
   git commit -m "Integrate Ollama (GPU) enrichment and nightly update pipeline"
   ```

3. **Push your branch (for example, if you are on branch "main"):**

   ```bash
   git push origin main
   ```

4. **Verify on GitHub:**  
   Check your remote repository (e.g. on GitHub) to confirm that your changes (including the README, test_ollama.py, ollama_trainer.py, and ollama_nightly_update.py) are pushed. 