# Force

Force is a small lead enrichment tool that predicts missing ZIP codes, cities and states.
It relies on a locally running Ollama/Mistral model but can fall back to OpenAI or the
Google Maps API when necessary. A nightly script downloads fresh training examples from
ChatGPT so the local model stays accurate.

## Quick start

1. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

2. **Add a `.env` file** containing your `OPENAI_API_KEY` (and optionally
   `GOOGLE_MAPS_API_KEY`) in the project root.

3. **Test the local model**

   ```bash
   python3 campaign_system/ai/test_ollama.py
   ```

4. **Enrich leads** – call `enrich_lead()` from `campaign_system/ai/ollama_trainer.py`
   or use the functions in `campaign_system/ai/enricher.py`.

5. **Nightly updates** – schedule `ollama_nightly_update.py` via cron to pull
   new prompt/completion pairs from ChatGPT.

See `campaign_system/ai/README.md` for more details.
