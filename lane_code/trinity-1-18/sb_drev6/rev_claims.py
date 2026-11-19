"""Recount the direction census exclusions and the scarce Seen/away hard cell."""
import collections as C, json, pickle, sqlite3, sys
from pathlib import Path
sys.path.insert(0, '/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/tree_r1')
from student_pilot import row_removals
import hashlib
CFG = json.load(open('/scratch/jjyeung/orch_n30/tree_rebuild10_w/w19/work/build19/inputs/config.json'))
U = '/scratch/jjyeung/orch_n30/sb_k1list/out/u_union.json'
files = list(CFG['remove_files']) + [dict(path=U, sha256=hashlib.sha256(open(U, 'rb').read()).hexdigest())]
rem = row_removals.Removals(files)
D = pickle.load(open('work/census.pkl', 'rb'))['dirrows']
con = sqlite3.connect('file:/scratch/jjyeung/n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite?mode=ro&immutable=1', uri=True)
hit = C.Counter(); per = C.Counter(); adm = C.Counter()
for i, m in D.items():
    r = json.loads(con.execute('select row from rows where i=?', (i,)).fetchone()[0])
    mt = rem.match(r)
    if mt:
        hit['any'] += 1
        for j in mt: per[Path(files[j]['path']).name] += 1
    elif m['fam'] != 'medium':
        adm[m['op'], m['cl'], m['fam'], m['label']] += 1
print(dict(hit), dict(per))
for k in sorted(adm):
    if k[2] == 'hard' or k[:2] == ('Seen', 'away'): print(k, adm[k])
