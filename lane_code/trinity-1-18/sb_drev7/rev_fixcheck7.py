"""Validate the two proposed fixes in memory: drop `facing`; copy the source's Step-1 line and final-line form."""
import collections as C, copy, json, re, sqlite3, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
import rev_verify7 as V
from student_pilot import r1_population

B = V.B; con = sqlite3.connect('file:' + V.DB + '?mode=ro&immutable=1', uri=True)
pack = V.pack_fn(); R = C.Counter(); fail = []
smap = {m['qid']: m for m in map(json.loads, open(B / 'SOURCE_MAP.jsonl'))}
for l in open(B / 'NEW_ROWS.jsonl'):
    r = json.loads(l); m = smap[r['qid']]
    s = json.loads(con.execute('select row from rows where i=?', (m['source_i'],)).fetchone()[0])
    sb, nb = V.body(s), V.body(r); X, Y, Z = m['objects']; lab = V.opts(r)[r['answer']]
    final = re.sub(r'(at|to) my [\w-]+\.$', lambda g: f'{g[1]} my {lab}.', sb[3])
    fixed = copy.deepcopy(r); fixed.pop('facing')
    fixed['target'] = '<think>\n' + '\n'.join([sb[0], sb[1], nb[2], final]) + '\n</think>\n\n' + r['answer']
    try:
        V.native(fixed, pack); R['native_PASS'] += 1
    except Exception as e:
        R['native_FAIL'] += 1; fail.append((r['qid'], repr(e)[:200])) if len(fail) < 5 else None
    R['cell:' + r1_population.family(fixed, 'vqa')] += 1
    R['final_line_label_ok'] += final.endswith(f' my {lab}.') and Z in final
print(dict(R), fail)
(HERE / 'work/FIXCHECK.json').write_text(json.dumps(dict(results=dict(R), failures=fail), indent=1))
