import sqlite3,json,collections,csv
db=sqlite3.connect('file:/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/rows.sqlite?mode=ro',uri=True)
rows=[json.loads(t) for (t,) in db.execute('select row from rows order by i')]
meta={r['video_id']:r for r in csv.DictReader(open('/scratch/jjyeung/orch_n30/b12_cntapp/work/auth/arkit_3dod_metadata.csv'))}
c=collections.Counter();caps=collections.defaultdict(set)
for r in rows:
    if r['dataset']!='d3':continue
    vid=r['provenance']['canonical'].split('/')[1]; m=meta.get(vid)
    c[(m['sky_direction'] if m else None, m['fold'] if m else None, r['question_type'])]+=1; caps[m['sky_direction'] if m else None].add(vid)
for k,v in sorted(c.items(),key=str):print(k,v)
print({k:len(v) for k,v in caps.items()})
sg=json.load(open('/scratch/jjyeung/orch_n30/rows_a2/vsti/out/vsti_rel_v3/SOURCE_GEOMETRY.json'))
cc=collections.Counter()
for k,v in sg.items():
    if v['canonical'].startswith('arkit'):
        m=meta.get(v['canonical'].split('/')[1]); cc[(m['sky_direction'] if m else None, v.get('reason'))]+=1
print(cc)
