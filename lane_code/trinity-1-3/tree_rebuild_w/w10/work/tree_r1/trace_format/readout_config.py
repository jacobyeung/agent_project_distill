"""Artifact configuration for shape validation and refusal budgets."""
import json
from pathlib import Path

def load():
    return json.loads(Path(__file__).with_suffix('.json').read_text())
