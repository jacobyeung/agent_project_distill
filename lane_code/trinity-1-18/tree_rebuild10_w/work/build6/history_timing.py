"""Inspect the retained diagnostic timing around a known scheduled position."""
import json
from pathlib import Path

B = Path(__file__).resolve().parent
rows = json.loads((B / 'proofs/suite_tree/diagnostic_temporary_sizes.json').read_text())
for index, row in enumerate(rows):
    if 296 <= index <= 307:
        print(json.dumps(dict(index=index, **row)))
