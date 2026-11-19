from pathlib import Path
import json
B=Path(__file__).resolve().parent
value=json.loads((B/'proofs/receipts/RESULT.json').read_text())
assert not value['absent'] and not value['missing_order_pins']
for name in ('receipts','prepared','children'):
    assert value[name] and all(r['status']=='PASS' for r in value[name])
    print(name,len(value[name]))
hashes={r['pin']['sha256'] for name in ('receipts','prepared','children') for r in value[name]}
for prefix in ('9a7f3310','93b21a3a','30612832','ca0616db','ddff748d','4e16dba9'):
    assert any(h.startswith(prefix) for h in hashes),prefix
print('Every required receipt and pose child passed.')
