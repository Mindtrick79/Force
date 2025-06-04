import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import campaign_system.ai.ollama_trainer as ot

class Dummy:
    def __init__(self):
        self.called = False
    def __call__(self, prompt):
        self.called = True
        return "12345, Springfield, IL"

def test_enrich_lead(monkeypatch):
    dummy = Dummy()
    monkeypatch.setattr(ot, "call_ollama", dummy)
    lead = {"address": "123 Main St", "city": "Springfield", "state": "IL", "zip": ""}
    result = ot.enrich_lead(lead)
    assert dummy.called
    assert result["zip"] == "12345"
    assert result["city"] == "Springfield"
    assert result["state"] == "IL"
