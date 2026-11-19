from pathlib import Path
import json,sqlite3,subprocess
L=Path(__file__).resolve().parents[2];B=L/'work/build20';O=B/'proofs/capacity';O.mkdir(parents=True,exist_ok=True)
counts={'pose':16000,'vqa':32000,'routing':16000,'pointing':8000}
workspace=sum(p.stat().st_size for p in L.rglob('*') if p.is_file() and not p.is_symlink())
rows={}
for name in ('vqa','routing','pointing'):
    path=L/'work/build19/proofs/native'/('routing19' if name=='routing' else name)/'rows.sqlite'
    with sqlite3.connect(path.as_uri()+'?mode=ro',uri=True) as c:
        length=c.execute('select length(cast(row as blob)) from rows limit 1').fetchone()[0]
    rows[name]=dict(source=str(path),row_bytes=length,required_rows=counts[name],row_payload_bytes=length*counts[name])
minimum=sum(v['row_payload_bytes'] for v in rows.values())
result=dict(status='REFUSE',error='BUILD20_WORKSPACE_CAPACITY',GO=False,
    workspace_bytes=workspace,workspace_limit_bytes=1_500_000_000,
    capacity_source=str(L/'work/build19/proofs/native/card.json'),counts=counts,measured_rows=rows,
    projected_row_payload_bytes=minimum,projection_scope='Existing fixture row payload only; excludes pose, SQLite overhead, source JSONL, composed stores and proofs.',
    free_scratch=subprocess.check_output(['df','-BG','--output=avail','/scratch'],text=True),
    required='A larger authorized workspace or a user-pruned inherited workspace is needed before capacity-sized native generation.',
    did_not_run=['capacity-sized producers','production audit','final handover','N initialization','all-rank first forward and loss'])
assert workspace+minimum>1_500_000_000
(O/'RESULT.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
