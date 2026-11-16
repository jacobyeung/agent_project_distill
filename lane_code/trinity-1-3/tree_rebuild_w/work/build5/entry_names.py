"""Inspect the names of exploratory entrypoint failures without importing them."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
values=json.loads((L/'fixtures/references/B3_BANK_ENTRYPOINTS.json').read_text())
for i in (31,32,40,41,62):print(i,values[i])
