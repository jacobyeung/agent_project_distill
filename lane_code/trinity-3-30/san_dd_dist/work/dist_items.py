# Per-item distance records at steps 200 and 544 (in memory); imported by the analysis scripts.
import sys; sys.path.insert(0, '/scratch/jjyeung/orch_n30/san_dd_dist/work')
from common import *
def ground_info(c):
    t = c.get('response') or ''
    o = re.search(r'obj="([^"]*)"', c['call']); o = o[1] if o else None
    ns = 'not seen' in t
    fr = re.search(r'frames ([\d,]+) \(best (\d+)\)', t)
    sz = re.search(r'size ([\d.]+) x ([\d.]+) x ([\d.]+) m', t)
    ce = re.search(r'centre \(([-\d.]+), ([-\d.]+), ([-\d.]+)\) m', t)
    nb = len(re.findall(r'^B\d+:', t, re.M))
    return dict(obj=o, not_seen=ns, unavailable=('unavailable' in t), frames=[int(x) for x in fr[1].split(',')] if fr else [],
                best=int(fr[2]) if fr else None, size=[float(x) for x in sz.groups()] if sz else None,
                centre=[float(x) for x in ce.groups()] if ce else None, nboxes=nb, text=t)
def build(d):
    R = {}
    for step in (200, 544):
        for r in d[('A', step)]:
            if r['type'] != 'object_abs_distance': continue
            u = unit(r['question']); F = FAC[u]; g = gaps(r); p = post(r)
            conv = CONV.findall(p) if r['calls'] else CONV.findall(r['text'])
            gr = [ground_info(c) for c in r['calls'] if c['family'] == 'ground']
            gapresp = [c.get('response') for c in r['calls'] if c['family'] == 'gap']
            a = num(r['answer']); t = float(r['gt'])
            R[(step, r['id'])] = dict(id=r['id'], step=step, unit=u, F=F, q=r['question'], tmpl=template(r['question']), objs=objs(r['question']),
                room=r['room'], gt=t, gt_m=t / F, ans=a, score=r['score'], called=r['ncalls'] > 0, calls=[c['call'] for c in r['calls']],
                gap=g[-1] if g else None, gapresp=gapresp, grounds=gr, conv=conv, post=p, text=r['text'], scale=r['scale'], tokens=r['tokens'])
    return R
def usage(x, tol_abs=0.011, tol_rel=0.01):
    """Classify the answer against the printed gap: follows (= gap x F), metres (= gap, non-metre unit), other, nogap, nocall."""
    if not x['called']: return 'nocall'
    if x['gap'] is None: return 'nogap'
    g, F, a = x['gap'], x['F'], x['ans']
    if a is None: return 'noanswer'
    near = lambda v: abs(a - v) <= max(tol_abs, tol_rel * abs(v))
    if near(g * F): return 'follows'
    if x['unit'] != 'm' and near(g): return 'metres'
    return 'other'

UW = {'ft': r'(?:ft|feet|foot)', 'in': r'(?:in|inch|inches)', 'cm': r'(?:cm|centimet(?:er|re)s?)', 'm': r'(?:m|met(?:er|re)s?)'}
def conv_written(x):
    """A conversion is written when the text after the last response (before </think>) states a number in the asked unit or a 'Convert' clause."""
    if x['unit'] == 'm': return False
    p = (x['post'].split('</think>')[0] if x['called'] else '').replace('5 cm grid', 'grid')
    return bool(re.search(r'\d\s*' + UW[x['unit']] + r'\b', p) or re.search(r'Conver(?:t|ted|ting) to', p))
def conv_right(x):
    return conv_written(x) and usage(x) == 'follows'
