# Shared helpers: load cached routed rows, parse units, gaps, conversions; MRA on the scored truth (row['gt']).
import os, sys, re, pickle, math
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
S = K._scorer(); sc = S.scorers
from rows.expected_calls import expected_calls
PKL = '/tmp/san_dd_dist/routed.pkl'
def load():
    if not os.path.isfile(PKL):
        out = {}
        for step in (200, 544):
            out[('A', step)] = K.routed(step, types=['object_abs_distance', 'room_size_estimation'], part='A')
            out[('B', step)] = K.routed(step, part='B')
        out['SOURCES'] = sorted(set(K.SOURCES)); pickle.dump(out, open(PKL, 'wb'))
    return pickle.load(open(PKL, 'rb'))
FAC = {'m': 1.0, 'ft': 1 / .3048, 'in': 1 / .0254, 'cm': 100.0}
def unit(q):
    f = sc.unit_factor(q)
    return {100.: 'cm', 1 / .3048: 'ft', 1 / .0254: 'in', 1.: 'm', 1000.: 'mm'}[f]
TH = [0.5 + 0.05 * i for i in range(10)]
def mra(pred, gt):
    try: p = float(pred); g = float(gt)
    except (TypeError, ValueError): return 0.0
    if g == 0: return float(p == 0)
    e = abs(p - g) / abs(g)
    return sum(e < 1 - t for t in TH) / 10.0
def num(s):
    m = re.match(r'\s*([-+]?\d*\.?\d+)', str(s or ''))
    return float(m[1]) if m else None
def gaps(r):
    return [v['distance'] for v in (sc.printed(c) for c in r['calls']) if v and v['kind'] == 'gap']
CONV = re.compile(r'Converting to ([a-z]+):\s*(-?\d+(?:\.\d+)?)\s*(?:m\s*)?[x×*]\s*(-?\d+(?:\.\d+)?)\s*=\s*(-?\d+(?:\.\d+)?)', re.I)
def post(r):
    """Text after the last tool response (the usage path)."""
    t = r['text']; i = t.rfind('</tool_response>')
    return t[i + len('</tool_response>'):] if i >= 0 else t
def objs(q, typ='object_abs_distance'):
    out = []
    for c in expected_calls(q, typ):
        m = re.search(r'obj="([^"]*)"', c)
        if m: out.append(m[1])
    return out
def template(q):
    t = q
    for o in sorted(set(objs(q)), key=len, reverse=True):
        t = re.sub(r'\b' + re.escape(o) + r'\b', '{x}', t, flags=re.I)
    t = re.sub(r'\b(centimeters?|centimetres?|meters?|metres?|feet|foot|inches|inch)\b', '{u}', t, flags=re.I)
    return t
