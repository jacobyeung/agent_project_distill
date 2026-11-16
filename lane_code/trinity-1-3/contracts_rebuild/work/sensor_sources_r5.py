import gzip,json
from pathlib import Path
L=Path(__file__).resolve().parents[1];checks=[];eligible=[]
def inspect(row,path,line):
    if not isinstance(row,dict):return
    heads=row.get('heads',{})
    if not isinstance(heads,dict):return
    queries=heads.get('ground_queries')
    if not isinstance(queries,list) or not queries:return
    if heads.get('trace_program_version','3.13')!='3.13':return
    if all(isinstance(q,dict) and q.get('geometry_mode','sensor')=='sensor' for q in queries):
        eligible.append(dict(source=str(path),line=line,queries=len(queries)))
for p in sorted((L/'work/real/x').glob('*.jsonl.gz')):
    count=0
    with gzip.open(p,'rt') as f:
        for count,line in enumerate(f,1):inspect(json.loads(line),p,count)
    checks.append(dict(source=str(p),records=count))
for p in [L/'out/real_replay_r4/completed_r4_base.jsonl',*sorted((L/'work/base/work/base/tree_b01ce449').rglob('*.json'))]:
    if p.suffix=='.jsonl':
        with p.open() as f:
            count=0
            for count,line in enumerate(f,1):inspect(json.loads(line),p,count)
    else:
        try:obj=json.loads(p.read_text())
        except (ValueError,UnicodeDecodeError):continue
        rows=obj if isinstance(obj,list) else [obj];count=len(rows)
        for n,row in enumerate(rows,1):inspect(row,p,n)
    checks.append(dict(source=str(p),records=count))
result=dict(eligible_live_sensor313_records=len(eligible),eligible=eligible,scanned=checks,
            eligibility='live_trace313.replay requires heads.ground_queries; trace_program_version must be 3.13 and every query must use sensor mode.',
            generated_source=str(L/'work/review2_inputs/base_sensor313_generated.json'))
(L/'work/test_artifacts_r5/SENSOR313_SOURCE_SEARCH_R5.json').write_text(json.dumps(result,indent=2))
assert not eligible,'Use the sealed eligible records instead of the generated fallback.'
