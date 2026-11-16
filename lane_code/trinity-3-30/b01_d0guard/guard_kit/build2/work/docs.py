from pathlib import Path
import difflib,json,re,secrets,shlex,sys,tarfile,hashlib
B=Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit';W=B.parents[1]/'work';OLD=B.parent/'build/out'
sys.path.insert(0,str(K));from guard_core import read,write,sha,digest

def line(file,needle):
 for n,s in enumerate((O/file).read_text().splitlines(),1):
  if needle in s:return f'out/{file}:{n}'
 raise ValueError((file,needle))
core='guard_kit/sj/orch_cd/evalx/work/milestone/'
checks={
1:('guard_kit/worker.py','Assigned Orchard'),2:('guard_kit/packet.py',"hashlib.sha256(raw).hexdigest()!=EXPECTED"),
3:('guard_kit/transport.py','def regular_tar'),4:('guard_kit/packet.py','def admit'),5:('guard_kit/worker.py','Assigned Orchard'),
6:('guard_kit/packet.py','def validate_packet'),7:('guard_kit/packet.py','for field in'),8:('guard_kit/packet.py','Exact ORCH GO'),
9:('guard_kit/packet.py',"for name,expected in family['code_pins'].items():"),10:('guard_kit/worker.py','O.storage_proof'),
11:(core+'orchard_native/native_job.py','def card'),12:(core+'orchard_native/native_stage.py','five-object/under-1-GB'),
13:(core+'orchard_native/native_stage.py','def cloud_uri'),14:(core+'orchard_stage.py','def copy_parts'),
15:(core+'orchard_native/native_stage.py','def verify_inventory'),16:(core+'orchard_native/native_stage.py','for name in ("runtime", "numpy", "closure", "trainer")'),
17:(core+'orchard_native/native_stage.py','def runtime_links'),18:(core+'native/out2/runtime_tree.py','def verified_sources'),
19:(core+'orchard_native/native_stage.py','phase("bwrap"'),20:(core+'orchard_native/native_stage.py','FLA manifest differs'),
21:(core+'orchard_native/native_stage.py','def runtime_spec'),22:(core+'orchard_native/native_stage.py','Production model manifest differs'),
23:(core+'orchard_native/native_stage.py','phase("base"'),24:(core+'orchard_native/native_stage.py','for index, item in enumerate(assets["depth"])'),
25:('guard_kit/staging.py','verify_archive(export'),26:(core+'orchard_native/native_stage.py','def frames'),
27:(core+'orchard_native/native_stage.py','def frames'),28:('guard_kit/packet.py','def validate_packet'),
29:('guard_kit/worker.py',"output=root/'result';output.mkdir()"),30:('guard_kit/worker.py','Priority wrapper pin differs'),
31:(core+'native_bootstrap.py','def configure'),32:(core+'native_bootstrap.py',"checked(spec['python'])"),
33:(core+'native_bootstrap.py',"checked(spec['sitecustomize'])"),34:(core+'native_bootstrap.py','for name in IMPORTS:'),
35:(core+'native_bootstrap.py',"target.name not in spec['entrypoints']"),36:('guard_kit/checkpoint.py','def run'),
37:(core+'orchard_native/native_worker.py','def modules'),38:(core+'orchard_native/native_worker.py','def cohort'),
39:('guard_kit/guard_backend.py',"parts=K.load_parts"),40:(core+'native/out2/runtime_tree.py','def verified_sources'),
41:('guard_kit/checkpoint.py','receipt=authenticate'),42:(core+'native/out2/nomdg.py','def cache_bind'),
43:(core+'native/out2/nomdg.py','def validate_request'),44:(core+'native/out2/geometry.py','def validate_raw'),
45:('guard_kit/admission.py','native_metrics.validate_gravity_guard'),46:('guard_kit/pool.py','def reserve')}
# Find the exact existing raw geometry validation definition if it is named differently.
if 'def validate_raw' not in (O/(core+'native/out2/geometry.py')).read_text():checks[44]=(core+'native/out2/geometry.py','def tower')
rows=read(OLD/'PIN_CLASSIFICATION.json')
changes={
1:'Require assigned Orchard host/partition/user and fresh job-private root.',2:'Literal SHA256 authenticates the external neutral payload before extraction.',
3:'Bound unique relative regular payload members; hard links rejected.',4:'Admit only the registered candidate run/milestones and allocation shape.',
6:'Authenticate the packaged family and exact review; ORCH GO binds the prepared plan.',7:'Seal all code and shared inputs; compare operational limits and publication contract.',
8:'Require one exact ORCH GO line naming job, step and plan.',9:'Check every packaged code source against the reviewed family map.',
12:'Retain the unchanged shared-object bound; candidate metadata is a separate bounded object.',
18:'Authenticate the unchanged source inventory and trainer archive; candidate source seal must match.',
25:'Stage the accepted export through C8r, candidate through unchanged reviewed stager; full tensor checker plus closure-artifact byte equality.',
28:'Validate packaged controls and code before staging; candidate step checked against artifact and closure.',
29:'Create private output exclusively.',30:'Authenticate and invoke the inherited priority wrapper.',
35:'Add the new checkpoint entrypoint to the authenticated runtime map after checking the family code map.',
36:'Parent authenticates launch/allocation; fresh child runs the same pinned restore, request, geometry and parity paths.',
38:'Preserve accepted order and inputs; the full candidate must retain the full denominator.',
39:'Preserve both kernel files; select only the native AST prefix at the existing worker boundary.',
41:'Recompute candidate config identity; bind preparation, source seals, baseline group chain and init-spec; unchanged C8r restoration is called.',
45:'Recompute candidate geometry; preserve refused items and verify guard dispositions. The fixed canary replaces paired pilot scheduling.',
46:'Reserve a fresh token in a bounded result pool; verify pool/cloud receipt copies before continuing.'}
for row in rows:
 n=row['number'];row['enforcement']=line(*checks[n]);row['candidate']=changes.get(n,'Retain and call the unchanged C8r check through production staging or the checkpoint session.')
 row['status']='IMPLEMENTED_NOT_EXECUTED_IN_PRODUCTION'
 if n==41:row['status']='METADATA_CHECKS_EXECUTED; MODEL_RESTORE_UNCHECKED'
 if n in (2,3,4,6,7,8,9,28):row['status']='PACKET_FIXTURE_TESTED'
 if n==46:row['status']='LOCAL_POOL_FIXTURE_TESTED; LIVE_CHANNELS_UNCHECKED'
 if n==45:row['classification']='export-dependent';row['status']='ADAPTER_IMPLEMENTED; WHOLE_WORKER_UNEXECUTED'
 if n==2:row['baseline']=dict(accepted_packet=str(W/'from113/sub/b07a20b364/PACKET.json'),sha256=sha(W/'from113/sub/b07a20b364/PACKET.json'))
write(O/'PIN_CLASSIFICATION.json',rows)
md=['# Pin classification','',
 'The table covers the inherited checks. An implementation reference is not an execution claim. Exact accepted values remain in `PIN_CLASSIFICATION.json`; the accepted configuration is pinned at `inputs/BASELINE_CONFIG.json`.',
 '', '| Row | Class | Accepted value | Candidate treatment and check | Evidence |','|---|---|---|---|---|']
for r in rows:
 base=r['baseline'];preview=json.dumps(base,sort_keys=True)
 if len(preview)>105:preview='canonical SHA256 '+digest(base)+' (exact value in JSON row)'
 md.append(f"| {r['number']} | {r['classification']} | `{preview}` | {r['candidate']} `{r['enforcement']}` | {r['status']} |")
md+=['','Additional touched pins:','',
 '| Pin | Class | Enforcement |','|---|---|---|',
 f"| Closure source/archive/member digests | export-dependent | `{line('guard_kit/closure.py','def authenticate')}`, `{line('guard_kit/packet.py','def authenticate_meta')}` |",
 f"| Artifact byte equality and baseline trained-group chain | export-dependent | `{line('guard_kit/closure.py','Export artifact is not byte-equal')}`, `{line('guard_kit/closure.py','Trained-group chain differs')}` |",
 f"| Candidate config identity and input configuration | run-dependent; fixed for this candidate run | `{line('guard_kit/closure.py','Candidate training config identity differs')}` |",
 f"| Code, reference and item order | export-independent; exact family pins | `{line('guard_kit/packet.py','def validate_packet')}` |",
 f"| Native-only journal, artifact, request and parity | export-dependent bindings, unchanged scoring rules | `{line('guard_kit/admission.py','def merge')}` |",
 f"| Return plan, admission and bundle digest | plan/export-dependent | `{line('guard_kit/transport.py','def verify_return')}` |",
 '', 'The exact G2 family and code hashes are in `FAMILY.json` and `CODE_MANIFEST.json`. No live upload generation, allocation, GPU parity, or candidate tensor-load result is inferred from local tests.']
(O/'PIN_CLASSIFICATION.md').write_text('\n'.join(md)+'\n')
# Every changed opcode becomes a line-range entry; unified patches contain exact source lines.
records=[];patch=[]
for p in sorted(K.rglob('*')):
 if not p.is_file():continue
 rel=p.relative_to(K);old=OLD/'guard_kit'/rel
 if old.is_file() and p.read_bytes()==old.read_bytes():continue
 if p.suffix not in ('.py','.sh','.json'):continue
 left=old.read_text().splitlines(True) if old.is_file() else [];right=p.read_text().splitlines(True)
 patch.extend(difflib.unified_diff(left,right,fromfile='G1/'+str(rel),tofile='G2/'+str(rel)))
 for kind,a,b,c,d in difflib.SequenceMatcher(a=left,b=right).get_opcodes():
  if kind!='equal':records.append(dict(file='out/guard_kit/'+str(rel),old_lines=[a+1,b],new_lines=[c+1,d],operation=kind))
write(O/'DIFF_LINES.json',records);(O/'DIFF.patch').write_text(''.join(patch))
reasons={'closure.py':('Candidate closure identity, source seals and hash chain','1'),
'guard_backend.py':('Select the staged logical source root in checkpoint children','2'),
'checkpoint.py':('Fresh checkpoint process, proof, published canary and native read','2,4'),
'admission.py':('Native-only journal merge, request/score/geometry admission','2'),
'packet.py':('Exact authority gates, bounded payload and command-line resources','2'),
'staging.py':('Dual export staging, closure mounting, hard-link rejection','1,2'),
'stage_candidate.py':('Call unchanged reviewed staging with the C8r checker namespace','1,2'),
'worker.py':('Coordinate fresh processes, durable early receipts and final publication','2'),
'pool.py':('Exclusive token and inherited result-pool bound','2'),
'fetch.py':('Verify and safely unpack a plan-bound return','2'),
 'transport.py':('Bound archives, verify local/cloud copies and returned admission','2,4')}
lines=['# Source changes','', 'The exact source patch is `DIFF.patch`. Each changed block appears below. All inherited C8r files and reviewed stager files remain byte-identical (`SOURCE_IDENTITY.json`). Naming projections are not integrated into the runtime.', '', '| File | G2 lines | Change | Reason / brief item |','|---|---|---|---|']
for r in records:
 reason,item=reasons.get(Path(r['file']).name,('Support the guarded native read','2'))
 lines.append(f"| `{r['file']}` | {r['new_lines'][0]}–{r['new_lines'][1]} | {r['operation']} | {reason}; item {item} |")
(O/'DIFF.md').write_text('\n'.join(lines)+'\n')
# Full difference from the sealed C8r tree, without Git.
patch=[]
for p in sorted(K.rglob('*.py')):
 rel=p.relative_to(K);old=W/'c8r_code'/rel
 left=old.read_text().splitlines(True) if old.is_file() else []
 patch.extend(difflib.unified_diff(left,p.read_text().splitlines(True),fromfile='C8r/'+str(rel),tofile='G2/'+str(rel)))
(O/'DIFF_C8R.patch').write_text(''.join(patch))
print('Documentation line references generated')
