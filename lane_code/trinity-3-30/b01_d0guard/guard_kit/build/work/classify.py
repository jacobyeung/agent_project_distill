import ast,json,pathlib,re
B=pathlib.Path(__file__).resolve().parents[1];O=B/'out';K=O/'guard_kit';C=json.loads((O/'BASELINE_CONFIG.json').read_text());F=json.loads((O/'BASELINE_FAMILY.json').read_text())
root=K/'sj/orch_cd/evalx/work/milestone'
def loc(file,name):
 p=root/file
 for n in ast.walk(ast.parse(p.read_text())):
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name:return str(p.relative_to(O))+':'+str(n.lineno)
 return str(p.relative_to(O))+':1'
def show(v):
 if isinstance(v,(dict,list)):
  import hashlib
  encoded=json.dumps(v,sort_keys=True,separators=(',',':')).encode()
  if len(encoded)>230:return 'canonical SHA256 `'+hashlib.sha256(encoded).hexdigest()+'`; exact leaves in `BASELINE_PIN_VALUES.json`'
 return '`'+json.dumps(v,separators=(',',':'))+'`'
A=C['assets'];W=C['worker'];T=C['transport'];P=json.loads((O/'BASELINE_prepare_config.json').read_text())
# Number, class, baseline value, enforcement, candidate treatment.
entries={
1:('I',C['plan_sha256'],'orchard_launcher.py','render_batch','New payload seal is build-dependent; cannot equal the accepted payload hash.'),
2:('I','g1 has no executable packet','orchard_launcher.py','validate_batch','Invocation admission retained as a requirement; production integration incomplete.'),
3:('I',32*1024**2,'orchard_launcher.py','validate_batch','Packet-size/safe-member guard is independent; added proof must be a separate pinned input.'),
4:('D',dict(schema=C['schema'],mode=C['mode'],partition=C['partition'],step=C['step'],token=C['token'],gpus=C['gpus']),'orchard_native/native_common.py','validate_config','Candidate step changes; token must be fresh, never equal the accepted invocation token.'),
5:('I',dict(partition=C['partition'],user='jjyeung',job='170056'),'orchard_native/native_job.py','context','User/partition semantics fixed; allocation identity must be fresh.'),
6:('I',dict(family=C['family'],review=C['review'],order=C['authorization']['orch_order']),'orchard_native/native_job.py','early_admission','New code/family/order require new seals and review. Build-dependent, not a checkpoint property.'),
7:('D',dict(assets=C['assets'],limits=C['limits'],contract=F['worker_contract']),'orchard_native/native_common.py','admit','Split backend invariants from candidate restoration pins; new-family integration remains blocked.'),
8:('D',C['authorization'],'orchard_native/native_common.py','admit','Rebind candidate whole-tar identity, step and fresh token; no authority is fabricated.'),
9:('I',F['bootstrap_pins'],'orchard_native/native_job.py','early_admission','Original bootstrap source bytes are unchanged; wrapper bootstrap admission is incomplete.'),
10:('I','job-private local mount and available disk','orchard_job.py','storage_proof','Live allocation property; retain original check.'),
11:('I','one empty NVIDIA H100 80GB HBM3','orchard_native/native_job.py','card','Live allocation property; retain original check.'),
12:('D',dict(objects=len(A['small_objects']),bytes=sum(x['bytes'] for x in A['small_objects'])),'orchard_native/native_stage.py','stage','Candidate closure and reference expand the transport contract; no silent widening.'),
13:('D',A['small_objects'],'orchard_native/native_stage.py','cloud_uri','New code/input objects need generation after upload; unchanged objects retain accepted digests.'),
14:('D',T,'orchard_native/native_stage.py','stage','Candidate whole-tar size and hash come from strict plain-text receipt; proof transport stays exact.'),
15:('D',{x['role']:x['members'] for x in A['small_objects']},'orchard_native/native_stage.py','verify_inventory','Every new archive needs a new regular-member inventory. Existing input member digests stay fixed.'),
16:('I',{k:A[k] for k in ('runtime','numpy','closure','trainer')},'orchard_native/native_stage.py','stage','Same backend archives. Candidate metadata cannot authorize different runtime/trainer bytes.'),
17:('I','unique authenticated interpreter; registered absolute symlinks','orchard_native/native_stage.py','runtime_links','Retain interpreter uniqueness and original symlink allowlist; input hard links remain forbidden.'),
18:('I',dict(tree_sources=A['tree_sources'],tree_sha256='b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'),'orchard_native/native_stage.py','verify_inventory','Fixed inference source tree. Any candidate seal mismatch refuses.'),
19:('I',A['bwrap'],'orchard_native/native_stage.py','copied','Byte-identical executable; sandbox probe is not this production pin check.'),
20:('I',A['fla'],'orchard_native/native_stage.py','extract_named','Retain manifest and per-member bytes; neutral source path is a name-only copy.'),
21:('I',dict(entry=A['worker_entrypoint'],site=A['sitecustomize']),'orchard_native/native_stage.py','runtime_spec','Original files unchanged. A new wrapper entrypoint needs its own extra pin and bootstrap integration.'),
22:('I',A['model_manifest'],'orchard_native/native_stage.py','stage','Base-model manifest is independent; name migration must preserve the model-file contents.'),
23:('I',A['base'],'orchard_native/native_stage.py','stage','Same base bytes and model file inventory. Neutral member naming is not yet integrated.'),
24:('I',A['depth'],'orchard_native/native_stage.py','copied','Frozen auxiliary source weights independent of candidate own-head outputs.'),
25:('D',T,'orchard_native/native_stage.py','validate_export_headers','Proof uses accepted transport; candidate uses unchanged reviewed stage_export via guard_export.stage.'),
26:('I',A['frame_puller'],'orchard_native/native_stage.py','frames','Frame-puller source unchanged.'),
27:('I',A['frames_inventory'],'orchard_native/native_stage.py','frames','All frame bytes unchanged; no new frame cohort is admitted.'),
28:('D',dict(code=F['code_pins'],step=C['step']),'orchard_native/native_common.py','validate_config','Original code pins stay fixed; candidate checkpoint step is derived and checked.'),
29:('I',C['logical_run'],'orchard_native/native_job.py','run','Fresh exclusive output required. Literal equality to prior run would be wrong.'),
30:('I',A['vnice'],'orchard_native/native_job.py','run','Original executable and mode retained.'),
31:('I',dict(archive=A['runtime']['sha256'],source='b01ce449beffe35be3bf0b48ad3d69f331f1523f96a69cbd3d10aab3dbb42a99'),'native_bootstrap.py','main','Original isolated bootstrap retained; new entrypoint launch is not integrated.'),
32:('I',dict(runtime=A['runtime'],numpy=A['numpy']),'native_bootstrap.py','main','Production interpreter and overlay hashes retained; local CPU environment is a stand-in.'),
33:('I',A['sitecustomize'],'native_bootstrap.py','main','Exact alias source bytes retained.'),
34:('I','torch=2.11.0; transformers=5.12.1; numpy=2.2.6; complete import origins in NATIVE_RUNTIME.json','native_bootstrap.py','main','Live bootstrap must verify every import; not established by local tests.'),
35:('I',A['worker_entrypoint'],'native_bootstrap.py','main','Original worker entrypoint preserved as source; new guard entrypoint needs added admission.'),
36:('D',C['worker'],'orchard_native/native_worker.py','run','Candidate metadata/config and dual-export workflow need complete job-layer admission.'),
37:('I',W['adapter_pins'],'orchard_native/native_worker.py','modules','Every original adapter byte is unchanged and checked before import.'),
38:('I',dict(inputs=W['inputs'],keys=W['expected_keys'],captures=W['geometry_captures'],selection=W['pilot_selection']),'orchard_native/native_worker.py','cohort','Exact accepted order and frozen distance membership verified; expanded list refused.'),
39:('I',W['kernel_source_pins'],'orchard_native/kernels.py','load_parts','Exact sealed kernels; native_arm selects only the unchanged native serving prefix.'),
40:('I',dict(tree=A['tree_sources'],runtime_tree='native/out2/RUNTIME_TREE.json'),'native/out2/runtime_tree.py','tree_identity','Original runtime source authentication remains mandatory.'),
41:('D',dict(config=W['config'],artifact=W['artifact'],data=W['data_receipt'],preparation=P['preparation'],code=P['code']),'native/out2/read_runtime.py','prepared','Candidate metadata is absent. Unchanged prepared/load_model/check_init_spec must authenticate it; never reuse step-544 receipts.'),
42:('I',dict(mask=W['mask_cache'],producer=W['kernel_source_pins']['nomdg']),'native/out2/nomdg.py','cache_bind','Preserve mask receipt and sealed producer bytes exactly.'),
43:('I',W['mask_cache'],'native/out2/perception.py','Masks','Frozen masks/operands/cache pins stay fixed; candidate geometry is a distinct dependent input.'),
44:('I',W['raw_tower'],'native/out2/geometry.py','prepare','Raw tower cache is independent. Prepared scale, gravity and output NPZ are dependent and must be recomputed.'),
45:('D',dict(geometry_captures=W['geometry_captures'],baseline_manifest=json.loads((B.parents[1]/'work/ret544/native/paired/request.json').read_text())['grounding']['geometry_manifest']),'native/out2/geometry_refusals.py','validate','Recompute every capture disposition, own-head scale/gravity and manifest for candidate; preserve refused items in denominator.'),
46:('I',dict(token=C['token'],pool_bytes=C['limits']['pool_bytes'],return_bytes=C['limits']['return_bytes']),'orchard_results.py','publish','Fresh pool/token and return integrity required. Proof and canary early durable publication integration is incomplete.')}
rows=[]
for line in (B/'in_c8r_kit/PIN_TABLE_C8R.md').read_text().splitlines():
 m=re.match(r'\| (\d+) \| ([^|]+) \|',line)
 if m:
  number=int(m[1]);kind,value,file,func,note=entries[number]
  rows.append(dict(number=number,check=m[2].strip(),classification='export-dependent' if kind=='D' else 'export-independent',baseline=value,inherited_enforcement=loc(file,func),candidate=note))
assert len(rows)==46
(O/'PIN_CLASSIFICATION.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
text=['# Pin classification','', 'This is a complete census of the accepted table, not a claim that the new job enforces every row. Production integration remains incomplete. Original source checks are cited below; new logic checks appear in `guard_core.py`, `guard_export.py`, `guard_backend.py` and `native_arm.py`.', '', 'Export-independent means that backend bytes and check semantics stay fixed. Fresh tokens, job IDs, payload seals and new code-object hashes cannot literally equal the accepted invocation. Those build/invocation exceptions are explicit below; treating them as unchanged pins would be false. `BASELINE_PIN_VALUES.json` records every scalar CONFIG/FAMILY value, and `PIN_CLASSIFICATION.json` carries each complete baseline object.', '', '| Row | Check | Classification | Accepted value | Enforcement in original code | Candidate treatment |','|---|---|---|---|---|---|']
for r in rows:text.append('| '+str(r['number'])+' | '+r['check']+' | '+r['classification']+' | '+show(r['baseline'])+' | `'+r['inherited_enforcement']+'` | '+r['candidate']+' |')
text+=['','## Added or changed control fields','', '| Field | Class | Accepted value | New treatment |','|---|---|---|---|',
'| candidate done object/bytes/hash | export-dependent | `BASELINE_CONFIG.json` transport | `guard_core.parse_done`, `guard_export.stage` |',
'| candidate config/data/preparation/source seal | export-dependent | `BASELINE_prepare_config.json`, `BASELINE_preparation.json`, `BASELINE_data_receipt.json`, `BASELINE_source_seal.json` | `guard_backend.authenticate_candidate`; absent candidate closure refuses |',
'| independent contract | export-independent | `INDEPENDENT_CONTRACT.json` exact accepted values | Equality helper is tested; complete job enforcement is not integrated |',
'| reference record and item list | export-independent | `REFERENCE_EXTRACTION.json`, `ITEM_SELECTION.json` | File digests in new FAMILY; source records project identically on every proof field |',
'| code tar and added modules | export-independent / explicit build change | `SOURCE_IDENTITY.json` lists every original code value | Original bytes fixed; added files and new tar have separate pins |',
'| time limit | export-independent / explicit resource change | Accepted limits in `BASELINE_CONFIG.json` | New estimate in `SIZING.json`; command-line resources in `packet.submit_argv` |',
'| neutral operational paths | export-independent / name-only change | `OPERATIONAL_NAME_MAP.json` | `names.prove` checks reversible scalar substitution; complete naming remains blocked |',
'| cloud generations | export-independent / new object publication | Original generations in `BASELINE_PIN_VALUES.json` | New objects `PENDING_UPLOAD`; never accepted as a live generation |','']
(O/'PIN_CLASSIFICATION.md').write_text('\n'.join(text))
