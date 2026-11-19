"""Labelling pilot, part 2 (row audit): turn the store-v7 rows that sit on the 24 K1 training captures of the calibration set into closed
questions for the labeller. Input /tmp/v7_k1train_full.jsonl (one line per row: i, alias, capture, category, pool, q, options, answer, target,
shas), written by the scan in work/pilot/v7_scan.py. No truth and no row text reaches the labeller: only object names and frame numbers.
Per capture, two kinds of question:
  v: is the object kind visible in frame k?            (one per distinct (object, frame) pair that a trace cites as "seen" or "first seen")
  f: in which frame is the object kind first visible, 0 if never?   (one per distinct object named by any row)
Writes work/pilot/jobs_audit.json (chunks of at most CH questions per dispatch), work/pilot_key/key_audit.json (question -> object, frame, rows)
and work/pilot_key/audit_rows.json (row -> its cited pairs and named objects). usage: /usr/bin/python3 audit_build.py [CH=50]"""
import json, re, sys, collections
P = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot/'; KD = '/scratch/jjyeung/orch_n30/swarm_an/work/pilot_key/'
CH = int(sys.argv[1]) if len(sys.argv) > 1 else 50
R = [json.loads(l) for l in open('/tmp/v7_k1train_full.jsonl')]
jobs_k1 = json.load(open(P + 'jobs_k1.json'))
def clean(o):
    o = o.replace('(s)', '').strip().strip('.').strip(); o = re.sub(r'^(the|a|an) ', '', o); return o
def split_objs(s):
    return [clean(x) for x in re.split(r',\s*then\s+|,\s*and\s+|\s+and\s+|,\s*|\s+then\s+', s) if clean(x)]
def parse(r):
    t = r['target']; think = t.split('</think>')[0]; pairs = []; objs = []
    for m in re.finditer(r'(?:find|locate) the ([^,.;:\n]+?), first seen in frame (\d+)', think): pairs.append((clean(m.group(1)), int(m.group(2))))
    for line in think.split('\n'):
        if line.startswith('Seen:'):
            for part in line[5:].split(';'):
                m = re.match(r'\s*(.+?) in frame (\d+)', part)
                if m: pairs.append((clean(m.group(1)), int(m.group(2))))
        m = re.search(r'first frame showing each object:(.*)', line)
        if m:
            for part in m.group(1).split(';'):
                m2 = re.match(r'\s*(.+?) frame (\d+)', part)
                if m2: pairs.append((clean(m2.group(1)), int(m2.group(2))))
        if 'distinct' in line and 'frame' in line:
            m = re.search(r'distinct instances of ([^;:]+?)[;:]', line) or re.search(r'distinct ([^:;]+?)(?: instances| at its| once)', line)
            if m:
                for f in re.findall(r'frame (\d+)', line.split(':', 2)[-1]): pairs.append((clean(m.group(1)), int(f)))
    objs += [o for o, _ in pairs]
    cat = r['category']; q = r['q']
    if not pairs and cat != 'object_counting' and cat != 'route_planning':
        m = re.search(r'Step 1: (?:find|locate) (.*?)\.\n', think + '\n')
        if m: objs += split_objs(m.group(1))
    if cat == 'object_rel_distance':
        objs += [clean(re.sub(r'^[A-D]\.\s*', '', o)) for o in (r.get('options') or [])]
        m = re.search(r'(?:to|from) the ([a-z][a-z0-9 \-/\']+?)\?', q)
        if m: objs.append(clean(m.group(1)))
    if cat == 'object_counting':
        for m in re.finditer(r'([a-z][a-z0-9 \-/\']+?)\(s\)', q): objs.append(clean(re.sub(r'^.*\b(?:many|the|and|of|count)\s+', '', m.group(1))))
    if cat == 'route_planning':
        for m in re.finditer(r'stand at the (.+?) (?:and )?facing the (.+?)\.', think): objs += [clean(m.group(1)), clean(m.group(2))]
        for m in re.finditer(r'I find the (.+?) (?:to my|behind|in front|ahead|out to|at my)', think): objs.append(clean(m.group(1)))
        m = re.search(r'navigate to the (.+?)\.', q)
        if m: objs.append(clean(m.group(1)))
    seen = []
    for o in objs:
        if o and o not in seen and len(o) < 40: seen.append(o)
    return sorted(set(pairs)), seen
rows = {}; per = collections.defaultdict(lambda: dict(pairs=collections.defaultdict(list), objs=collections.defaultdict(list)))
noobj = collections.Counter(); fam = collections.Counter(); cited = collections.Counter()
for r in R:
    pairs, objs = parse(r); f = r['category']; fam[f] += 1
    if not objs: noobj[f] += 1
    if pairs: cited[f] += 1
    rows[str(r['i'])] = dict(alias=r['alias'], category=f, pool=r['pool'], pairs=pairs, objs=objs, q=r['q'][:200], cites_first=bool(re.search(r'first seen in frame|first frame showing|first appear', r['target'])))
    for o, k in pairs: per[r['alias']]['pairs'][(o, k)].append(r['i'])
    for o in objs: per[r['alias']]['objs'][o].append(r['i'])
jobs = collections.OrderedDict(); key = collections.OrderedDict(); nq = collections.Counter()
for alias in sorted(per):
    Q = []
    for (o, k), ii in sorted(per[alias]['pairs'].items()):
        Q.append(('v', 'Is the object kind "%s" visible, fully or partly, in frame %d?' % (o, k), 'yes or no', dict(kind='visible', obj=o, frame=k, rows=ii)))
    for o, ii in sorted(per[alias]['objs'].items()):
        Q.append(('f', 'In which frame, 1 to 32, is the object kind "%s" visible for the first time? Answer 0 if no frame shows it.' % o, 'integer from 0 to 32', dict(kind='first', obj=o, rows=ii)))
    nchunk = max(1, -(-len(Q) // CH)); size = -(-len(Q) // nchunk)
    for c in range(nchunk):
        part = Q[c * size:(c + 1) * size]; name = '%s_%d' % (alias, c + 1); qs = []
        for j, (kind, text, fmt, meta) in enumerate(part):
            qid = '%s%03d' % (kind, j + 1); qs.append(dict(qid=qid, text=text, format=fmt)); key[name + '/' + qid] = dict(meta, alias=alias); nq[kind] += 1
        jobs[name] = dict(sheets=jobs_k1[alias]['sheets'], questions=qs)
json.dump(jobs, open(P + 'jobs_audit.json', 'w'), indent=0); json.dump(key, open(KD + 'key_audit.json', 'w'), indent=0); json.dump(rows, open(KD + 'audit_rows.json', 'w'), indent=0)
print('rows', len(R), 'by family', dict(fam)); print('rows with a cited frame', dict(cited)); print('rows with no object parsed', dict(noobj))
print('captures', len(per), 'dispatches', len(jobs), 'questions', dict(nq), 'largest dispatch', max(len(v['questions']) for v in jobs.values()))
ex = collections.defaultdict(list)
for i, r in rows.items():
    if len(ex[r['category']]) < 1: ex[r['category']].append((r['pairs'][:4], r['objs'][:6]))
for k, v in ex.items(): print('  ', k, v[0])
# the (alias, object, frame) list for the raster cross-check on trinity-1-18
json.dump(dict((a, dict(pairs=sorted(set(v['pairs'])), objs=sorted(v['objs']))) for a, v in per.items()), open(P + 'k1/audit_facts.json', 'w'))
