"""Authenticate the prior lane's filtered extract against both original row sources."""
import sys,hashlib,json,csv,gzip,sqlite3,resource
from pathlib import Path
from collections import Counter
W=Path(__file__).resolve().parents[1];RO=Path('/scratch/jjyeung/orch_n30/fb_pack/ro');P=RO/'orch_n30/fb_pack/prior/out'
sys.path.insert(0,str(W/'work/new'))
from student_pilot.p3_provenance import digest,encoded
from student_pilot.r1_direction_twins import direction_details
from student_pilot.r1_population import family
from student_pilot.r1_direction_prior import WEIGHTS
resource.setrlimit(resource.RLIMIT_AS,(36*1024**3,36*1024**3))
inputs=[]
def track(path,expected=None):
 path=Path(path);h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 h=h.hexdigest()
 if expected is not None:assert h==expected,(path,h,expected)
 pin={'path':str(path),'sha256':h};inputs.append(pin);return pin
census=json.loads((P/'SOURCE_CENSUS.json').read_text());track(P/'SOURCE_CENSUS.json');track(P/'CENSUS.json')
extract=P/'DIRECTION_ROWS.tsv.gz';track(extract,census['direction_extract']['sha256'])
refs={}
with gzip.open(extract,'rt') as f:
 for r in csv.DictReader(f,delimiter='\t'):refs[(r['source'],int(r['source_i']))]=r
assert len(refs)==98315
source=RO/'n30_mirror/rows_r1/out/a2_vqa_v7/vqa/rows.sqlite';twins=RO/'orch_n30/sb_rowD7f/out/NEW_ROWS.jsonl'
track(source,'210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443')
track(twins,'7b3d696d580386f9e8af3240fa142e2ad50eebb277a8718c97e2db497dcc925e')
track(RO/'orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json');track(W/'work/recovered/card.json','c0167f682bd49fce84d1ca447a64131ae1605a345f534ce61ee98aabf7bee9c8')
track(__file__);track(W/'out/MISSING_INPUTS.json');track(W/'out/CAPSULE_RECOVERY.json')
for name in ('r1_direction_prior.py','r1_direction_twins.py','r1_population.py','p3_provenance.py'):track(W/'work/new/student_pilot'/name)
weights={k:dict(weights=WEIGHTS[k],rows=[]) for k in WEIGHTS};counts=Counter();seen=set();old_disagree=0
outdb=W/'work/direction_rows_release.sqlite';assert not outdb.exists();dest=sqlite3.connect(outdb)
dest.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT NOT NULL,cell TEXT NOT NULL,source TEXT NOT NULL,source_i INTEGER NOT NULL)')
def consume(row,source,i):
 global old_disagree
 ref=refs.get((source,i))
 if ref is None:return
 assert row['qid']==ref['qid'] and digest(row)==ref['row_sha256']
 kind=family(row,'vqa');assert kind==ref['family']
 details=direction_details(row);clause,difficulty,side,relation=details
 assert 'MISSING' not in details,(row['qid'],details)
 old_disagree+=json.loads(ref['native_dimensions_json'])[0]!=clause
 index=len(seen);assert row['qid'] not in seen;seen.add(row['qid'])
 dest.execute('INSERT INTO rows VALUES(?,?,?,?,?)',(index,encoded(row),kind,source,i))
 counts[(kind,clause,difficulty,side)]+=1
 if (clause,difficulty)==('toward','hard'):
  assert relation=={'front':'front','back':'behind'}[side]
  weights[kind]['rows'].append(dict(qid=row['qid'],row_sha256=digest(row),side=side))
conn=sqlite3.connect(source.as_uri()+'?mode=ro&immutable=1',uri=True)
for i,raw in conn.execute('SELECT i,row FROM rows ORDER BY i'):
 if ('store_v7',i) in refs:consume(json.loads(raw),'store_v7',i)
conn.close()
with twins.open() as f:
 for i,line in enumerate(f):consume(json.loads(line),'twins',i)
assert len(seen)==len(refs);dest.commit();dest.close()
missing=json.loads((W/'out/INPUT_LOCATIONS.json').read_text())['missing']
policy={'schema':'r1-direction-prior-v1','policy':'toward_hard_equal_mass_v1','cells':weights,'inputs':inputs,'selection_evidence':{'scope':'Prior lane authenticated filtered direction extract; row identities rechecked against original v7 and twin bytes. Full filtering cannot be independently repeated because inputs are missing.','extract':inputs[2],'inherited_source_inputs':census['inputs'],'missing_filter_inputs':[p for p in missing if p['path'].endswith(('naming_remove.json','s.json','u.json','u_union.json','BINDING.jsonl','TIERED_ALIAS_MAP.json','WORDINGS.json'))]},'command':'OMP_NUM_THREADS=16 MKL_NUM_THREADS=16 OPENBLAS_NUM_THREADS=16 PYTHONDONTWRITEBYTECODE=1 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python scripts/build_weights.py'}
(W/'out/TOWARD_HARD_WEIGHTS.json').write_text(json.dumps(policy,sort_keys=True,separators=(',',':'))+'\n')
record={'status':'AUTHENTICATED_EXTRACT_REPLAY_ONLY','rows':len(seen),'clause_disagreements_with_base':old_disagree,'counts':[dict(cell=k[0],clause=k[1],difficulty=k[2],side=k[3],rows=v) for k,v in sorted(counts.items())],'inputs':inputs,'database':track(outdb),'weights':track(W/'out/TOWARD_HARD_WEIGHTS.json'),'missing':missing}
(W/'out/WEIGHT_BUILD.json').write_text(json.dumps(record,indent=2)+'\n')
(W/'STATUS.md').write_text('The patch binds pinned toward-hard weights to native prepared offsets and preserves all other slots. The prior lane direction extract has been authenticated against the original v7 and twin row bytes, and the weight file is generated. Independent full production filtering remains MISSING because the mirror lacks required removal and room-authority inputs. CPU tests and the diagnostic draw replay are in progress.\n')
print('Authenticated rows',len(seen),'base clause disagreements',old_disagree,'target counts',{k:dict(Counter(r['side'] for r in v['rows'])) for k,v in weights.items()},flush=True)
