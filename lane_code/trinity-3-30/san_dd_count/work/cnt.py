"""Shared parser for lane san_dd_count: trace forms and inventories for counting / relative count. Read-only."""
import sys, re
sys.path.insert(0, '/scratch/jjyeung/orch_n30/swarm_an/kit'); import san_kit as K
CK = [('S1', 544), ('R1', 100), ('R1', 200)]
def think(t): return t.split('</think>')[0] if t else ''
STOP = set('how many of the count number numberof total provide please indicate are is there me tell what exact know like to i d would could you find we can do have in this room let see all any a an determine give quantity amount present located here and with among altogether objects compared relative than as more fewer same equal numerous greater less outnumber outnumbered by contain whether if s youd id'.split())
def cats(q):
    out = []
    for c in re.findall(r"((?:[A-Za-z\-']+ ){0,3}[A-Za-z\-']+)\(s\)", q):
        w = c.lower().replace("'", ' ').split()
        while w and w[0] in STOP: w = w[1:]
        out.append(' '.join(w))
    return out
def tbin(g):
    g = int(float(g)); return '2' if g <= 2 else ('3' if g == 3 else ('4' if g == 4 else '5+'))
FS_PAT = re.compile(r'(list each distinct .+? once, by the frame where it first appears|locate each distinct .+? at its first appearance|'
                    r'find each distinct .+?, using its first-seen frame|list the distinct .+? instances by first appearance)\s*:\s*(.*)')
GEN_PAT = re.compile(r'(count (each|it) once across the frames|and count it once|count each once)', re.I)
def entries(s):
    s = s.strip().rstrip('.').strip()
    return [e.strip() for e in s.split(';') if e.strip()] if s else []
FR = re.compile(r'frame\s+(\d+(?:\.\d+)?)')
def ent_frame(e):
    m = FR.search(e)
    if m: return float(m.group(1))
    m = re.match(r'^(\d+(?:\.\d+)?)\s*(s\b|\(|$)', e)
    if m: return float(m.group(1))
    return None
def parse(r):
    """returns dict(form, lists=[entries per category], stated=int|None, vis=n frames listed (544), inst=N (544), fs544=[...])"""
    th = think(r['text']).strip(); out = dict(form='OTHER', lists=[], stated=None, vis=None, inst=None, fs544=None, nlines=th.count('\n') + 1)
    if 'find the frames that show' in th or 'match the' in th and 'detections' in th:
        out['form'] = 'F544'
        m = re.search(r'find the frames that show [^:]*:\s*(.*)', th)
        if m: out['vis'] = len([x for x in m.group(1).split('\n')[0].split(',') if 'frame' in x])
        ms = re.findall(r'into distinct instances:\s*(\d+)(?:,\s*first seen in\s*([^\n]*))?', th)
        if ms:
            out['inst'] = sum(int(a) for a, b in ms)
            out['fs544'] = [entries(b.replace(',', ';')) for a, b in ms]
    else:
        for line in th.split('\n'):
            m = FS_PAT.search(line)
            if m:
                out['form'] = 'FS'; out['lists'].append(entries(m.group(2)))
        if out['form'] != 'FS' and GEN_PAT.search(th): out['form'] = 'GEN'
    m = re.findall(r'add them:\s*([\d\s\+=;]+)', th)
    if m:
        nums = re.findall(r'=\s*(\d+)', m[-1]); out['stated'] = int(nums[-1]) if nums else None
    else:
        m = re.findall(r'(?:count (?:is|equals)|there (?:are|is)|So there are)\s*(\d+)', th)
        if m: out['stated'] = int(m[-1])
    return out
def load(run, step, s, types=('object_counting',)):
    rows = K.direct(run, step, s, types=list(types))
    for r in rows: r['P'] = parse(r)
    return rows
def pat(lst):
    """pattern of one category list at R1: identical (all entries same string), samefr (a frame repeats, entries differ),
    adj (no repeat, two cited frames differ by 1), distinct (all frames distinct and non-adjacent), noframe (no frame number)"""
    if len(lst) <= 1: return 'single'
    if len(set(lst)) == 1: return 'identical'
    fr = [ent_frame(e) for e in lst]
    if any(f is None for f in fr): return 'noframe' if all(f is None for f in fr) else 'mixed'
    if len(set(fr)) < len(fr): return 'samefr'
    sf = sorted(fr)
    if any(abs(b - a) <= 1 for a, b in zip(sf, sf[1:])): return 'adj'
    return 'distinct'
