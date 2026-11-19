from pathlib import Path
import json
B=Path(__file__).resolve().parent
v=json.loads((B/'proofs/receipts/RESULT.json').read_text())
print(json.dumps({k:v[k] for k in ('absent','missing_order_pins','children')},indent=2))
