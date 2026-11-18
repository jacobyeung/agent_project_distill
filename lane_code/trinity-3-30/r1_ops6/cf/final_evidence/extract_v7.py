import json, sqlite3, sys
V = '/scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7'
R = json.load(open(f'{V}/FAMILY_INDEX_RANGES.json'))['families']
con = sqlite3.connect(f'file:{V}/vqa/rows.sqlite?immutable=1', uri=True)
out = open('v7_count_fs_rows.jsonl', 'w')
n = 0
for fam in ['object_counting', 'first_seen_frame']:
    for a, b in R[fam]:
        for i, row, target in con.execute('select i,row,target from rows where i between ? and ?', (a, b)):
            r = json.loads(row)
            out.write(json.dumps({'i': i, 'fam': fam, 'row': r, 'target': target}) + '\n'); n += 1
print(n)
