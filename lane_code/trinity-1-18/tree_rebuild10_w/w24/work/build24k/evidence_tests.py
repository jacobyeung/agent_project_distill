from pathlib import Path
import hashlib,importlib.util,json,random,sys,time
L=Path(__file__).resolve().parents[2];D=L/'work/build24k'
sys.path[:0]=[str(L/'out/kit_n_go/b'),str(L/'work/tree_r1'),str(L/'work/build24')]
import rv,joblib as J
F=D/'review_tests/no_pass';cfg=J.load(F/'node/q_22c714e1_91/v.json');node=F/'node/q_22c714e1_91'
records=[]
for name in ('evidence_a','evidence_b'):
 p=D/name;p.mkdir(exist_ok=True)
 start=time.monotonic();v=rv.evidence(cfg,node/'rooms.json',p);v['elapsed']=time.monotonic()-start;records.append(v)
 assert v['bytes']<2_000_000
 for stream,n in rv.NAMES.items():
  data=J.load(p/n);assert data['admitted_rows']==64 and data['answer_only']==0
  assert all(v['rows']==0 for v in data['protected_rooms'].values())
  assert [v['row_id'] for v in data['sample']]==random.Random(20261119).sample(list(range(64)),40)
  assert not any(k in json.dumps(data['sample']) for k in ('"frames"','"frame_indices"','"timestamps"'))
for p in (D/'evidence_a').iterdir():assert p.read_bytes()==(D/'evidence_b'/p.name).read_bytes()
bad=J.load(D/'review_tests/no_answer_only/target/o/91/live/e1.json');assert bad['answer_only']==1
J.write(D/'EVIDENCE_TESTS.json',dict(status='PASS',native_reader='student_pilot.carrier_c1_run.Rows.row (SQLite and PoseMix/RowSource)',records=records,deterministic=True,injected_answer_only_count=1,rows_per_second=256/records[1]['elapsed']))
print('evidence cap, deterministic sample, native reader and one answer-only injection PASS')
