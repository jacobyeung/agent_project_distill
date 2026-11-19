"""Sample 2,000 direction rows of store v7 by primary key (seed 7); question object order, names, sources, fps.  Prints a summary; writes rows_names.json (name counts)."""
import json, sqlite3, random, re, collections
F = json.load(open('/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/FAMILY_INDEX_RANGES.json'))['families']
ids = []
for t in ('object_rel_direction_easy', 'object_rel_direction_medium', 'object_rel_direction_hard'):
    for a, b in F[t]: ids.extend(range(a, b + 1))
print('direction rows in store v7:', len(ids))
random.seed(7); S = sorted(random.sample(ids, 2000))
con = sqlite3.connect('file:/scratch/jjyeung/orch_n30/r1_ops6/store/a2_vqa_v7/vqa/rows.sqlite?mode=ro', uri=True)
rows = []
for k in range(0, len(S), 200):
    q = 'select i,row from rows where i in (%s)' % ','.join(map(str, S[k:k + 200]))
    for i, r in con.execute(q):
        j = json.loads(r); si = j.get('student_input') or {}
        rows.append(dict(i=i, qt=j['question_type'], pool=j.get('pool'), rule=(j.get('retrace') or {}).get('rule'), q=si.get('question', ''),
                         target=j.get('target', ''), scene=j.get('scene'), lic=tuple(j.get('license') or []), ds=j.get('dataset'),
                         fps=si.get('fps'), nf=si.get('total_num_frames'), src=(j.get('provenance') or {}).get('source', '')[-60:]))
print('fetched', len(rows))
QA = re.compile(r"standing by the (.+?) and facing (away from |toward |towards )?the (.+?), is the (.+?) to (?:the |my )", re.I)
tmpl = collections.Counter(); order = collections.Counter(); fam = collections.Counter(); names = collections.Counter(); lic = collections.Counter()
toward = []
for r in rows:
    m = QA.search(r['q'])
    fam[(r['qt'][22:], r['pool'], r['rule'])] += 1
    lic[(r['lic'], r['ds'], r['fps'])] += 1
    if not m:
        tmpl[re.sub(r'the [a-z0-9 \-]+', 'the X', r['q'].split('\n')[0])[:90]] += 1; continue
    away = bool(m.group(2) and 'away' in m.group(2))
    for n in (m.group(1), m.group(3), m.group(4)): names[n.lower()] += 1
    if not away: toward.append((r, m))
print('families in sample:', sorted(fam.items(), key=lambda x: -x[1])[:14])
print('questions not matching the observer/faced/target pattern:', sum(tmpl.values()), tmpl.most_common(5))
random.seed(11); T6 = random.sample(toward, min(600, len(toward)))
qform = collections.Counter(re.sub(r'the [a-z0-9 \-]+?(?=[ ,?])', 'the X', m.string.split('\n')[0])[:120] for r, m in T6)
print('toward rows sampled:', len(T6), 'question templates:', len(qform))
for k, v in qform.most_common(8): print('  ', v, k)
# order in the trace's Step 1 line relative to the question's roles
so = collections.Counter()
for r, m in T6:
    o, f, t = m.group(1).lower(), m.group(3).lower(), m.group(4).lower()
    s1 = (r['target'].split('\n')[1] if '\n' in r['target'] else '').lower()
    pos = sorted([(s1.find('the ' + o), 'O'), (s1.find('the ' + f), 'F'), (s1.find('the ' + t), 'T')])
    so[(s1[:12], ''.join(p for x, p in pos if x >= 0))] += 1
print('trace line-1 opening and role order (O observer, F faced, T target):', so.most_common(8))
print('sources (license, dataset, fps):', lic.most_common(8))
print('scene id formats:', collections.Counter(re.sub(r'[0-9a-f]', 'h', r['scene'] or 'None') for r in rows).most_common(4))
print('total_num_frames quartiles:', sorted(r['nf'] or 0 for r in rows)[::500])
json.dump(dict(names=names, n_rows=len(rows)), open('rows_names.json', 'w'))
