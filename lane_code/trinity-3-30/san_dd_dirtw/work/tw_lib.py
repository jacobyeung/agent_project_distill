"""Shared parsing for lane san_dd_dirtw: toward direction items, R0-dev / dev-S1, steps 544, R1-100, R1-200."""
import sys, re, collections
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
T = ['object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard']
LV = {'object_rel_direction_easy': 'easy', 'object_rel_direction_medium': 'medium', 'object_rel_direction_hard': 'hard'}
QRE = re.compile(r"standing by the (.+?) and facing (?:toward |towards )?the (.+?), is the (.+?) to (?:the |my )", re.I)
def objs(q):
    m = QRE.search(q); return (m.group(1), m.group(2), m.group(3)) if m else (None, None, None)
def opt(r, letter):
    if letter is None: return None
    L = str(letter).strip().rstrip('.').upper()
    for o in r['options']:
        if o.split('.')[0].strip().upper() == L: return o.split('.', 1)[1].strip().lower()
    return str(letter).strip().lower()
ANG = re.compile(r"lies (\d+(?:\.\d+)?) degrees (left|right) of straight ahead")
def angle544(t):
    """signed angle, left positive, in (-180, 180]; None if unparsed"""
    t = (t or '').split('</think>')[0]
    m = ANG.search(t)
    if m:
        a = float(m.group(1)); return a if m.group(2) == 'left' else -a
    m = re.search(r"lies (\d+(?:\.\d+)?) degrees from straight ahead", t)
    if m: return ('u', float(m.group(1)))
    if re.search(r"lies (?:straight|directly) ahead", t): return 0.0
    if re.search(r"lies (?:straight|directly) behind", t): return 180.0
    return None
def stated(t, lv):
    """relation the trace states in its last 'So ...' line (or Step 2), normalized to the option vocabulary"""
    th = (t or '').split('</think>')[0]
    lines = [l for l in th.split('\n') if l.strip()]
    so = [l for l in lines if l.startswith('So ')]
    s = (so[-1] if so else (lines[-1] if lines else '')).lower()
    for q in ('front-left', 'front-right', 'back-left', 'back-right'):
        if q in s: return q
    B = re.search(r"\bbehind\b|\bback\b", s) is not None
    if lv == 'hard':
        f = 'back' if B else ('front' if ('front' in s or 'ahead' in s) else None)
        sd = 'left' if 'left' in s else ('right' if 'right' in s else None)
        return '%s-%s' % (f, sd) if f and sd else None
    if B: return 'back'
    if 'left' in s: return 'left'
    if 'right' in s: return 'right'
    return None
def adist(x, y):
    if isinstance(x, tuple): return min(adist(x[1], y), adist(-x[1], y))
    d = abs(x - y) % 360; return min(d, 360 - d)
def sep_lines(lv, truth, ans):
    """signed angles (left positive) of the lines separating truth's region from answer's region; [] if none (opposite quadrant)"""
    if lv == 'easy': return [0.0, 180.0]
    if lv == 'medium':
        s = {truth, ans}
        if s == {'left', 'right'}: return [0.0]
        if s == {'left', 'back'}: return [135.0]
        if s == {'right', 'back'}: return [-135.0]
        return []
    tf, ts = truth.split('-'); af, as_ = ans.split('-')
    if tf == af and ts != as_: return [0.0] if tf == 'front' else [180.0]
    if ts == as_ and tf != af: return [90.0] if ts == 'left' else [-90.0]
    return []
def axis(lv, truth, ans):
    """what differs: 'side', 'fb' (front/back, incl. medium side<->back), 'both'"""
    if truth == ans: return 'none'
    if lv == 'easy': return 'side'
    if lv == 'medium': return 'side' if {truth, ans} == {'left', 'right'} else 'fb'
    tf, ts = truth.split('-'); af, as_ = ans.split('-')
    return 'side' if tf == af else ('fb' if ts == as_ else 'both')
def load(setname='R0-dev', steps=(('S1', 544), ('R1', 100), ('R1', 200))):
    D = {}
    for run, st in steps:
        D[st] = {r['id']: r for r in K.direct(run, st, setname, types=T)}
    return D
def phrase(r):
    """the Step 2 relation phrase of a step-100/200 trace ('slightly to my left', 'out to my right', 'behind me, on my left', ...)"""
    t = (r['text'] or '').split('</think>')[0]
    o = objs(r['question']); tg = o[2] or ''
    m = re.search(r"I find the " + re.escape(tg) + r" (.+?)(?: when I stand|\.\s*$|\.\n|$)", t, re.M)
    if not m: return None
    p = m.group(1)
    return re.sub(r"\b(left|right)\b", "X", p)
_N = r"the ([a-z0-9][a-z0-9 '\-/]*?)"
_OBS = [re.compile(r"(?:standing|stand|position(?:ed)?|placed|located|be|am|I'm|i am|situated|stationed)\s+(?:right\s+)?(?:by|beside|next to|at|near|close to|alongside)\s+" + _N + r"(?=,| and | with |\.|;| facing| looking| gazing| oriented| while)", re.I),
        re.compile(r"(?:From|from|At|at)\s+(?:beside |next to |by |a position beside |a spot beside |a position next to |the place of |the spot of |the location of |the position of )?" + _N + r"(?=,| I | look| you| facing| gazing| oriented| with)", re.I)]
_FAC = [re.compile(r"(?:facing|face|faces|look toward|looking toward|look towards|looking towards|looking at|look at|gazing at|gaze at|turned toward|turn toward|oriented toward|oriented towards|pointed at|looking directly at|looking directly toward|looking straight at|staring at|eyes on)\s+(?:toward |towards )?" + _N + r"(?=,|\.|;| and |\?| from| would| is| can| does| which| where)", re.I),
        re.compile(r"with " + _N + r" (?:ahead of|in front of|straight ahead|directly ahead)", re.I)]
_TGT = [re.compile(r"(?:right|back|behind|left|rear)[,]? is " + _N + r"\?", re.I),
        re.compile(r"(?:is|describes|Where is|where is|lies|locate|would|does|can you confirm if|confirm whether|whether)\s+" + _N + r"(?= to | on | relative| located|:| lie| in |\?| positioned| from| when| be | sit| situated| appear| fall)", re.I)]
def objs_any(q):
    o = objs(q)
    if None not in o: return o
    q1 = q.split('\n')[0]; out = []
    for pats in (_OBS, _FAC, _TGT):
        hit = None
        for p in pats:
            m = p.search(q1)
            if m: hit = m.group(1).lower(); break
        out.append(hit)
    return tuple(out)
_STOP = {'place', 'point', 'standpoint', 'viewpoint', 'position', 'spot', 'location', 'perspective', 'quadrant', 'direction', 'side', 'left', 'right',
         'back', 'front', 'directions', 'origin', 'positive y-axis', 'quadrants', 'following', 'way', 'room', 'video', 'center', 'centre', 'one'}
_NP = re.compile(r"\bthe ([a-z0-9][a-z0-9'\-/ ]*?)(?=[,.?;:]| and | to | on | is | in | at | of | from | when | facing| looking| gazing| would| can | does | located| situated| found| toward| with | as | while | relative| positioned| be | ahead| directly| straight| sit| lie| appear)", re.I)
def names3(q):
    o = objs(q)
    if None not in o: return o
    seen = []
    for m in _NP.finditer(q.split('\n')[0]):
        n = m.group(1).lower().strip()
        if n in _STOP or n in seen: continue
        seen.append(n)
        if len(seen) == 3: break
    return tuple(seen) if len(seen) == 3 else (None, None, None)
