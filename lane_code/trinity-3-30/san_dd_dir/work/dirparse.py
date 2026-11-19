"""Parse direction traces (read in place through san_kit). Used by the lane san_dd_dir analyses and reproduce.py."""
import re, sys
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit')
import san_kit as K
T = ['object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard']
LV = {T[0]: 'E', T[1]: 'M', T[2]: 'H'}
OPP = {'L': 'R', 'R': 'L', 'F': 'B', 'B': 'F'}
QRE = re.compile(r"If I am standing by the (.+?) and (facing directly away from|facing away from|facing in the opposite direction of|facing) the (.+?), is the (.+?) to (?:my|the) ")

def triple(q):
    m = QRE.search(q)
    return (m[1], m[3], m[4], m[2]) if m else None

def rel(line, lv):
    """Relation code in one trace line. H: FL/FR/BL/BR; M: aL/aR (ahead), oL/oR (out), bL/bR/b (behind), back; E/M final: L/R."""
    l = line
    if lv == 'H':
        m = re.search(r"(in front of me|ahead of me|behind me),? on my (left|right)", l)
        if m: return ('F' if m[1] != 'behind me' else 'B') + m[2][0].upper()
        m = re.search(r"at my (front|back)-(left|right)", l)
        if m: return m[1][0].upper() + m[2][0].upper()
        return None
    if lv == 'M':
        m = re.search(r"ahead of me, slightly to (?:my|the) (left|right)", l)
        if m: return 'a' + m[1][0].upper()
        m = re.search(r"out to (?:my|the) (left|right)", l)
        if m: return 'o' + m[1][0].upper()
        m = re.search(r"behind me,? on my (left|right)", l)
        if m: return 'b' + m[1][0].upper()
        if re.search(r"at my back|behind me|to my back", l): return 'back' if l.startswith('So ') else 'b'
    m = re.search(r"(?:to|on) (?:my|the) (left|right)", l)
    return m[1][0].upper() if m else None

def med_answer(f, turned):
    """Medium answer implied by a stated forward band f, before (turned False) or after a half turn."""
    if f is None: return None
    if not turned: return 'back' if f[0] == 'b' else f[-1]
    if f[0] == 'a': return 'back'
    if f in ('b', 'back'): return None
    return OPP[f[-1]]

def implied(f, lv, turned):
    if f is None: return None
    if lv == 'M': return med_answer(f, turned)
    if lv == 'E': return OPP[f] if turned else f
    return (OPP[f[0]] + OPP[f[1]]) if turned else f

def parse(r):
    lv = LV[r['type']]
    think = (r['text'] or '').split('</think>')[0].strip()
    lines = [x.strip() for x in think.splitlines() if x.strip()]
    d = dict(lv=lv, lines=lines)
    o = lines[0] if lines else ''
    d['open'] = 'D' if o.startswith('Step 1:') else 'S' if o.startswith('Seen:') else 'X'
    d['open_verb'] = (re.match(r"Step 1: (\w+)", o) or [None, None])[1]
    d['frames'] = [int(x) for x in re.findall(r"frame (\d+)", o)]
    d['inq'] = 'in question' in o
    tl = [x for x in lines if 'half turn' in x or 'keep that heading' in x or 'no turn applies' in x or 'The question has me' in x]
    t = tl[0] if tl else ''
    d['turn'] = 'half' if 'half turn' in t else 'keep' if ('keep that heading' in t or 'no turn applies' in t) else ('other' if t else 'none')
    d['turn_line'] = t
    fl = [x for x in lines[1:] if x is not t and not x.startswith('So ') and rel(x, lv)]
    d['fwd_line'] = fl[0] if fl else ''
    d['fwd'] = rel(fl[0], lv) if fl else None
    sl = [x for x in lines if x.startswith('So ')]
    d['fin_line'] = sl[-1] if sl else ''
    d['fin'] = rel(sl[-1], lv) if sl else None
    d['fwd_says_away'] = bool(re.search(r"away|opposite", d['fwd_line']))
    return d

ANG = re.compile(r"lies (\d+) degrees (left|right) of straight ahead")
def parse544(r):
    think = (r['text'] or '').split('</think>')[0]
    m = ANG.search(think)
    d = dict(text=think)
    m2 = re.search(r"lies (\d+) degrees from straight ahead", think)
    d['unsigned'] = bool(m2) and not m
    if m: d['ang'] = int(m[1]) * (-1 if m[2] == 'left' else 1)
    elif m2: d['ang'] = int(m2[1])
    elif 'straight ahead' in think and 'degrees' not in think: d['ang'] = 0
    elif re.search(r"directly behind", think): d['ang'] = 180
    else: d['ang'] = None
    return d

def optword(r, key):
    v = r[key]
    for o in r['options']:
        if o.startswith(str(v) + '.'): return o[2:].strip().lower()
    return None

def code_of_word(w, lv):
    if w is None: return None
    if lv == 'H': return {'front-left': 'FL', 'front-right': 'FR', 'back-left': 'BL', 'back-right': 'BR'}.get(w)
    if lv == 'M': return {'left': 'L', 'right': 'R', 'back': 'back'}.get(w)
    return {'left': 'L', 'right': 'R'}.get(w)

def load(run, step, s='R0-dev'):
    rows = K.direct(run, step, s, types=T)
    for r in rows:
        r['P'] = parse(r) if not (run == 'S1' and step == 544) else parse544(r)
        lv = LV[r['type']]
        r['lv'] = lv
        r['gtc'] = code_of_word(optword(r, 'gt'), lv)
        r['prc'] = code_of_word(optword(r, 'pred'), lv)
        r['tri'] = triple(r['question'])
    return rows
