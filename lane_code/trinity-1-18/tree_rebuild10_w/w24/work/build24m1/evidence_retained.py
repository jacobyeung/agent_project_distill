from pathlib import Path
import sys,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24m1'
sys.path[:0]=[str(L/'out/kit_n_go/b'),str(L/'work/tree_r1'),str(L/'work/build24')]
import rv,joblib as J
from student_pilot.r1_persisted import scope
cfg=J.load('/tmp/q_22c714e1/v.json');out=D/'retained_evidence';out.mkdir(exist_ok=True)
aliases={p.name:str(p) for folder in ('build21','build22') for p in (L/'work'/folder/'upload/u').glob('*') if p.is_file()}
start=time.monotonic();code=None
try:
 with scope(aliases),scope(cfg['r1_training']['persisted_files']):rv.evidence(cfg,'/tmp/q_22c714e1/rooms.json',out)
except ValueError as e:code=str(e)
elapsed=time.monotonic()-start
counts={stream:{key:J.load(out/name)[key] for key in ('admitted_rows','answer_only','trace_forms','databases','protected_rooms')} for stream,name in rv.NAMES.items()}
assert code is None,code
total=sum(v['admitted_rows'] for v in counts.values());size=sum(p.stat().st_size for p in out.iterdir())
assert size<2_000_000
assert all(all(v['rows']==0 for v in c['protected_rooms'].values()) for c in counts.values())
assert counts['vqa']['answer_only']==counts['routing']['answer_only']==0
J.write(D/'RETAINED_EVIDENCE.json',dict(status='PASS',refusal=code,counts=counts,total_rows=total,elapsed_seconds=elapsed,rows_per_second=total/elapsed,evidence_bytes=size,source='read-only 24f rehearsal v.json/prepared stores',native_reader='carrier_c1_run.Rows.row; c1_pose_mix.PoseMix/RowSource; no model or RGB encoding'))
print(total,'rows',elapsed,'seconds',size,'bytes',code,flush=True)
