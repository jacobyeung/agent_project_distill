"""Q2: one read-only pass over store v7 (210b2534). Per family (question_type x pool x retrace rule): rows, rows kept after
n.json (02315a74) and after n.json + B1r z.json (caba6a56), template hits in the target, unit words in the question,
tool-call syntax in the target; 20 sample rows per family (lowest sha256(qid)); 5 examples per template x family."""
import sqlite3, json, re, hashlib, sys
from collections import defaultdict, Counter
DB = 'file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro'
N = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/n.json'
Z = '/scratch/jjyeung/orch_n30/r1_ops6/cp/out/records/z.json'
def keys(p):
    return set(json.loads(l)['row_key'] for l in open(p) if l.strip())
nkeys, zkeys = keys(N), keys(Z)
T = {
 'first_seen_frame': r'first seen in frame', 'first_seen_any': r'first (?:seen|appear)',
 'nearest_to_farthest': r'nearest[- ]to[- ]farthest', 'candidates_ordered': r'candidates ordered',
 'question_asks': r'[Tt]he question (?:asks|has me)', 'i_find_to_be': r'I find (?:it|that|them|the [a-z ]{1,30}?) to be',
 'find_x_and_y_then': r'find the [^.\n]{1,40} and the [^.\n]{1,40}, then', 'gap_between_closest': r'between their (?:closest|nearest) points',
 'the_gap_is': r'\b[Tt]he gap is\b', 'stand_at_facing': r'when I stand at', 'step_numbering': r'(?m)^Step \d+:',
 'locate_line': r'(?m)^Locate', 'relate_line': r'(?m)^Relate',
 'number_with_len_unit': r'\d(?:\.\d+)?\s*(?:m|meters?|metres?|cm|centimet(?:er|re)s?|feet|foot|ft|inch(?:es)?)\b',
 'number_with_nonmetre_unit': r'\d(?:\.\d+)?\s*(?:cm|centimet(?:er|re)s?|feet|foot|ft|inch(?:es)?)\b',
 'tool_call': r'<(?:ground|gap|move|turn|room|size)\b', 'convert': r'(?i)convert', 'x_factor': r'x\s*(?:3\.28|39\.37|100)\b',
 'apart': r'\bapart\b', 'distance_word': r'\bdistance\b',
}
T = {k: re.compile(v) for k, v in T.items()}
Q = {'q_metre': r'\b(?:meters?|metres?)\b', 'q_cm': r'\b(?:centimeters?|centimetres?|cm)\b', 'q_feet': r'\b(?:feet|foot|ft)\b',
     'q_inch': r'\b(?:inches|inch)\b', 'q_square': r'(?i)square', 'q_closest_points': r'(?i)(?:closest|nearest) points?',
     'q_distance_word': r'(?i)\b(?:distance|span|gap|spacing|separat\w+|apart|far)\b'}
Q = {k: re.compile(v) for k, v in Q.items()}
fam = defaultdict(lambda: dict(rows=0, kept_n=0, kept_nz=0, t=Counter(), t_kept_nz=Counter(), q=Counter(), q_kept_nz=Counter(), qt=Counter()))
samples = defaultdict(list); tex = defaultdict(list)
con = sqlite3.connect(DB, uri=True)
n = 0
for i, row, target in con.execute('select i, row, target from rows'):
    r = json.loads(row); n += 1
    qt = r.get('question_type') or r.get('category'); pool = r.get('pool'); rr = (r.get('retrace') or {}).get('rule')
    k = '%s|%s|%s' % (qt, pool, rr)
    tg = r.get('target') or ''
    si = r.get('student_input') or {}; qs = si.get('question') or r.get('question') or ''
    qid = r.get('qid'); f = fam[k]; f['rows'] += 1
    kn = qid not in nkeys; knz = kn and qid not in zkeys
    f['kept_n'] += kn; f['kept_nz'] += knz
    hits = [t for t, rx in T.items() if rx.search(tg)]
    qh = [t for t, rx in Q.items() if rx.search(qs)]
    for t in hits:
        f['t'][t] += 1
        if knz: f['t_kept_nz'][t] += 1
    for t in qh:
        f['q'][t] += 1
        if knz: f['q_kept_nz'][t] += 1
    for a in qh:
        for b in hits: f['qt'][a + '&' + b] += 1
    h = hashlib.sha256(qid.encode()).hexdigest()
    rec = dict(i=i, qid=qid, h=h, kept_nz=knz, question=qs, options=si.get('options'), target=tg, answer=r.get('answer'))
    s = samples[k]; s.append(rec); s.sort(key=lambda x: x['h']); del s[20:]
    for t in hits:
        e = tex[k + '#' + t]
        if len(e) < 5: e.append(dict(qid=qid, question=qs, target=tg[:600]))
out = dict(rows=n, n_json_keys=len(nkeys), z_json_keys=len(zkeys), families={k: dict(rows=v['rows'], kept_n=v['kept_n'], kept_nz=v['kept_nz'],
           templates=dict(v['t']), templates_kept_nz=dict(v['t_kept_nz']), question=dict(v['q']), question_kept_nz=dict(v['q_kept_nz']), q_and_t=dict(v['qt'])) for k, v in fam.items()})
json.dump(out, open('STORE_V7_TEMPLATE_COUNTS.json', 'w'), indent=1, sort_keys=True)
json.dump(samples, open('STORE_V7_SAMPLES20.json', 'w'))
json.dump(tex, open('STORE_V7_TEMPLATE_EXAMPLES.json', 'w'))
print('rows', n, 'families', len(fam))
