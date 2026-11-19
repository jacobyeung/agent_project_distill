"""D0 v5 category sets per scene for duplicate removal: totals (provenance total_categories) and appearance
(categories from option A, independent of question phrasing). Writes work/d0_sets.json."""
import sqlite3, json, re, collections
S = '/scratch/jjyeung/orch_n30/rows_rebuild3/out/rows/d0_v5/vqa/rows.sqlite'
con = sqlite3.connect(f'file:{S}?mode=ro&immutable=1', uri=True)
def norm(s): return re.sub(r'\s+', ' ', s.strip().lower())
tot = collections.defaultdict(set); app = collections.defaultdict(set); c = collections.Counter()
for i, row, t in con.execute('select i,row,target from rows'):
    d = json.loads(row); a = d['dataset'] + '/' + d['scene']
    if d['question_type'] == 'object_counting' and d.get('count_kind') == 'total':
        tot[a].add(tuple(sorted(norm(x['name']) for x in d['provenance']['total_categories']))); c['total'] += 1
    if d['question_type'] == 'obj_appearance_order':
        o = d['student_input']['options'][0]; o = re.sub(r'^[A-D]\.\s*', '', o)
        app[a].add(tuple(sorted(norm(x) for x in o.split(',')))); c['app'] += 1
json.dump({'total': {a: sorted(map(list, v)) for a, v in tot.items()}, 'app': {a: sorted(map(list, v)) for a, v in app.items()}},
          open('/scratch/jjyeung/orch_n30/b12_cntapp/work/d0_sets.json', 'w'), sort_keys=True)
print(dict(c), sum(map(len, tot.values())), sum(map(len, app.values())))
