"""Amend only the two authorized file pins; retain every other JSON value."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
V1 = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/codex_arkit_timing/K1_MANIFEST.arkit_timing.json')
V1_SHA = '91a2dbf9a0bdad1a45af44a5a3a2607d40f9f7a630f742fc4531544c00cade7c'

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()

def main():
    raw = V1.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == V1_SHA
    old = json.loads(raw)
    family = json.loads((ROOT / 'reference/FAMILY.json').read_text())
    new = deepcopy(old)
    diff = {}
    for key in ('config', 'data_receipt'):
        pin = family['worker_contract'][key]
        assert set(pin) == {'path', 'sha256'}
        new['gpu'][key] = deepcopy(pin)
        diff['gpu.' + key] = {'old': old['gpu'][key], 'new': pin}
    assert len(old['captures']) == len(new['captures']) == 300
    assert canonical(old['captures']) == canonical(new['captures'])
    assert canonical(old['gpu']['artifact']) == canonical(new['gpu']['artifact'])
    reverted = deepcopy(new)
    for key in ('config', 'data_receipt'):
        reverted['gpu'][key] = old['gpu'][key]
    assert canonical(reverted) == canonical(old)
    out = ROOT / 'manifest_v2'
    out.mkdir(exist_ok=True)
    data = (json.dumps(new, indent=2, sort_keys=True, allow_nan=False) + '\n').encode()
    (out / 'a40fbc19.json').write_bytes(data)
    result = dict(v1_sha256=V1_SHA, v2_sha256=hashlib.sha256(data).hexdigest(),
                  v1_binding_digest=hashlib.sha256(json.dumps(old, sort_keys=True, allow_nan=False).encode()).hexdigest(),
                  v2_binding_digest=hashlib.sha256(json.dumps(new, sort_keys=True, allow_nan=False).encode()).hexdigest(),
                  captures_equal=300, all_other_values_equal=True, diff=diff)
    (out / 'DIFF.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
