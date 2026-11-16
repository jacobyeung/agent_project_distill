import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
report_path=L/'work/build4/pool_clock_join/slices_final/a0_pool_abs_distance_reworded/proof/materialization.json'
report=json.loads(report_path.read_text())
ids={r['qid'] for r in report['intake'][0]['refusals'] if 'frame metadata' in r['reason']}
source=L/'work/rows_slices/slices_final/a0_pool_abs_distance_reworded.jsonl'
examples=[]
with source.open() as f:
    for n,line in enumerate(f):
        if n>=2000:break
        row=json.loads(line)
        if row['qid'] in ids:examples.append(row)
destination=L/'fixtures/rows/join_examples.jsonl'
destination.write_text(''.join(json.dumps(row)+'\n' for row in examples))
summary=dict(source=str(source.relative_to(L)),refusals=len(ids),examples=len(examples),
    rows=[dict(qid=r['qid'],canonical=r.get('canonical'),indices=len(r.get('frame_indices',[])),
               input_keys=sorted(r.get('student_input',{})),provenance=r.get('provenance',{})) for r in examples])
(L/'work/build5/JOIN_INPUTS.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(dict(source=summary['source'],refusals=len(ids),examples=len(examples),
    starts=[r['frame_indices'][0] for r in examples])))
