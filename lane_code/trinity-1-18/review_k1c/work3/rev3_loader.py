"""Review K1C3: JSON loader equivalence, boundary, and order after the pin check."""
import json, sys, os, inspect
from pathlib import Path
from unittest.mock import patch
WORK = Path('/scratch/jjyeung/orch_n30/k1_ops3/work/kc_guard/k1_build/work/kit_k1a/work')
sys.path[:0] = [str(WORK), str(WORK / 'refit')]
import k1_pipeline as K
K._native(); B = K.B
HERE = Path(__file__).resolve().parent / 'loader'; HERE.mkdir(exist_ok=True)
out = {}
# 1. Source text equality apart from the bound constant.
a = inspect.getsource(B.load).replace('20_000_000', 'BOUND'); b = inspect.getsource(K.load_candidates)
b = b.replace('JSON_BOUND_BYTES', 'BOUND').replace('load_candidates', 'load')
b = '\n'.join(l for l in b.splitlines() if '"""' not in l)
out['source_equal_modulo_bound'] = [x.strip() for x in a.splitlines()] == [x.strip() for x in b.splitlines()]
out['bound'] = K.JSON_BOUND_BYTES
# 2. Real files: every candidates.json in the convert root.
root = Path('/scratch/jjyeung/k1/run_convert_2'); small = large = eq = 0; sizes = []
for d in sorted(root.iterdir()):
    p = d / 'candidates.json'
    if not p.exists(): continue
    s = p.stat().st_size; sizes.append(s)
    got = K.load_candidates(p)
    if s <= 20_000_000:
        small += 1; eq += got == B.load(p)
    else:
        large += 1; eq += got == json.loads(p.read_bytes().decode())
out.update(files=len(sizes), small=small, large=large, equal=eq, max_bytes=max(sizes), over_64MiB=sum(s > K.JSON_BOUND_BYTES for s in sizes))
# 3. Exact boundary.
def pad(n):
    p = HERE / f'pad_{n}.json'; body = '{"a": 1}'; p.write_text(body + ' ' * (n - len(body))); return p
p0, p1 = pad(K.JSON_BOUND_BYTES), pad(K.JSON_BOUND_BYTES + 1)
out['at_bound_loads'] = K.load_candidates(p0) == {'a': 1}
try: K.load_candidates(p1); out['over_bound'] = 'loaded'
except ValueError as e: out['over_bound'] = str(e)
os.remove(p0); os.remove(p1)
# 4. Semantics corner cases vs B.load.
cases = {'dup': '{"a":1,"a":2}', 'nan': '[NaN, Infinity, -Infinity]', 'big': '[1e400, 12345678901234567890]', 'uni': '{"\\u00e9": "\u00e9"}', 'bad': '{"a":', 'trail': '{} x'}
sem = {}
for k, v in cases.items():
    p = HERE / f'{k}.json'; p.write_text(v)
    r = []
    for f in (B.load, K.load_candidates):
        try: r.append(repr(f(p)))
        except Exception as e: r.append(type(e).__name__ + ':' + str(e))
    sem[k] = r[0] == r[1]; os.remove(p)
out['semantics_equal'] = sem
# 5. Order: a pin failure stops cached() before the loader runs.
m = B.load('/scratch/jjyeung/orch_n30/k1_ops3/work/manifest_v2/a40fbc19.json'); c = m['captures'][0]
calls = []
def bad_checked(pin): calls.append('checked'); raise ValueError('pin')
def spy(p): calls.append('load'); return {}
with patch.object(B, 'checked', side_effect=bad_checked), patch.object(K, 'load_candidates', side_effect=spy):
    try: K.cached(c, root / B.digest(c['canonical'])[:16])
    except ValueError as e: out['pin_failure'] = str(e)
out['pin_failure_calls'] = calls
src = inspect.getsource(K.cached)
out['checked_before_load'] = src.index('B.checked(pin)') < src.index('load_candidates(')
out['only_call_site'] = inspect.getsource(K).count('load_candidates(') == 2
print(json.dumps(out, indent=1)); (Path(__file__).resolve().parent / 'rev3_loader.json').write_text(json.dumps(out, indent=1))
