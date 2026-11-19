import json,hashlib,collections,re
from pathlib import Path
import route as R
from route import ROOT,BASE,TREE,NAMES,INV,load,pin,write,rows,status
R.COMMAND=R.PREFIX+'work/finalize.py'
pin(__file__);pin(ROOT/'work/route.py');pin(ROOT/'prompts/fbp_route.md')
acc=load(ROOT/'out/EXCLUSION_ACCOUNTING.json');native=load(ROOT/'out/INTAKE_RESULTS.json');idx=load(ROOT/'out/ENVELOPE_INDEX.json');local=load(ROOT/'out/LOCALIZED_INDEX.json');audits=load(ROOT/'out/AUDIT_RESULTS.json');phrase=load(ROOT/'out/PHRASE_DECISION.json');camera=load(ROOT/'out/CAMERA_SELECTION.json');diff=load(ROOT/'out/CAMERA_KR9C_DIFF.json');compose=load(ROOT/'out/COMPOSE_RESULT.json');diag=load(ROOT/'out/BLOCKER_DIAGNOSTICS.json')
sealpath=BASE/'tree_rebuild10_w/w24/out/TREE_SEAL.json';seal=load(sealpath)
coverage=load(BASE/'fb_pack/FRAME_COVERAGE.json')
for p in ['tree_rebuild10_w/w24/out/BUILD24E_REPORT.md','tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json','tree_rebuild10_w/w24/work/build24e/upload/q/k/c.json','tree_rebuild10_w/w24/work/build24e/upload/q/k/n.json']:
 pin(BASE/p)
# Check every recorded tree dependency against the live, read-only tree.
tree_inputs={}
for f in sorted((ROOT/'out').rglob('*.json')):
 if f.name in ['ROUTE_MANIFEST.json','PACKAGE.json','TREE_IMPORTS.json','CONFIG_HANDOFF.json']:continue
 try:d=json.loads(f.read_text())
 except (ValueError,UnicodeError):continue
 for path,v in d.get('inputs',{}).items():
  if path.startswith(str(TREE)+'/'):
   h=v['sha256'] if isinstance(v,dict) else v
   if path in tree_inputs:assert tree_inputs[path]==h,(path,'tree changed across stages')
   tree_inputs[path]=h
for path,h in tree_inputs.items():pin(path,h)
versions={}
for p in sorted((ROOT/'work').glob('*.py'))+sorted((ROOT/'work/code').glob('*.py')):
 q=pin(p);versions[q['sha256']]=q
codepin=write('out/TREE_IMPORTS.json',dict(tree=str(TREE),tree_seal=pin(sealpath),tree_seal_value=seal,files={p:dict(sha256=h,bytes=Path(p).stat().st_size) for p,h in sorted(tree_inputs.items())},code_versions=versions,scope='All tree Python modules and adjacent tree data recorded by the executed stages and checker; each hash was rechecked against the read-only tree. Code snapshots preserve scripts whose source path had been updated between stages.'))
# Concrete config/request fields, with source catalog derived from the authenticated row bindings.
old=load(BASE/'tree_rebuild10_w/w21/work/build21/inputs/row_sources.json');specs={};catalog={};route_pins={};row_pins={}
for n in NAMES:
 s=acc['slices'][n];e=load(local['slices'][n]['envelope']['path']);pin(s['rows']['path'],s['rows']['sha256'])
 row_pins[n]=e['rows'];route_pins[n]=local['slices'][n]['envelope'];specs[n]=dict(old.get(n,{}),source=e['rows'])
 catalog[n]=dict(source=e['rows'],qids=list(e['row_bindings']))
sp=write('out/config/LOCALIZED_ROW_SOURCES.json',specs)
mp=write('out/config/LOCALIZED_SOURCE_MEMBERSHIP.json',dict(schema='r1-source-catalog-v1',sources=catalog,scope='Exact inherited raw QID membership of the final source files; admission is separately recorded by native intake.'))
inv=load(INV/'out/FULL_INVENTORY.json');extent=load(local['slices']['recovery']['envelope']['path'])['extent_receipt']
fields={'cfg.r1_training.routing_inputs':route_pins,'request.routing_inputs':route_pins,'cfg.r1_training.row_slice_inputs':row_pins,'request.row_slice_inputs':row_pins,'cfg.r1_training.row_sources':sp,'cfg.r1_training.source_membership':mp,'cfg.extent_receipt':extent,'cfg.streams.routing':inv['routing_base']['original_pin'],'request.routing_base':inv['routing_base']['original_pin']}
configpin=write('out/CONFIG_HANDOFF.json',dict(fields=fields,remove_field_at_first_boundary='cfg.r1_training.routing_slices (currently deferred_first_boundary); omit the field for FULL composition',Q_E4={'/data2/k6tk':'MISSING','/data2/kr9c':'MISSING'},Q_E4_requirement='JSON mapping to independently verified absolute node-local raster roots; actual production roots and byte/staging receipts were not supplied.',Q_E7='1 only after tree_rebuild/sb_fhalias adds the alias and reseals; current w24 job_env.py lacks it',Q_E8='Do not set a local-node bypass; retain native local-node and non-Trinity vetoes.',pin_localization=dict(transport='u/<sha256> in out/envelopes; transport intake used the native r1_persisted.scope hash-to-absolute-path map.',dry_native='out/localized envelopes carry absolute active pins and pass the same prefix checks without a relocation scope.',production_command=R.PREFIX+'work/localize.py --tree <production-tree>',production_steps='Stage the required input bytes under the unpacked root/u/<sha256>, run the localizer there, and bind its newly hashed absolute envelopes plus exactly equal rows and extent pins. Regenerate row_sources/source_membership/config/request pins for that root. The kit localizes inline config/request strings but does not recursively rewrite already pinned envelope files.'),blocked_by=diag['tree_actions'],no_tree_edits=True))
def artifact(p,count):
 return dict(p,row_count=count)
slices={}
for n in NAMES+['camera_B']:
 s=acc['slices'][n];test=native['slices'][n];l=local['slices'][n];a=audits['files'][s['rows']['path']]
 passed=test['every_row_seen'] and test['status']!='TREE_FIX_REQUIRED'
 slices[n]=dict(status='PASSED_NATIVE_INTAKE_WITH_EXCLUSIONS' if passed else 'BLOCKED_TREE_CONTRACT',rows=artifact(s['rows'],s['row_count']),coverage=artifact(l['coverage'],s['row_count']),upstream_receipt=artifact(l['upstream_receipt'],s['row_count']),envelope=artifact(l['envelope'],s['row_count']),transport_envelope=artifact(idx['slices'][n]['envelope'],s['row_count']),remove=artifact(s['remove'],s['removed']),camera_remove=s.get('camera_remove'),prefiltered=s['prefiltered'],native_counts=test['aggregate'],native_refusal_reasons=test['reasons'],first2000=test['first2000'],localized_first2000=artifact(l['intake'],min(s['row_count'],2000)),shards=test['shards'],audit=artifact(a['audit'],s['row_count']),audit_hits=a['hits'],every_row_seen=test['every_row_seen'],upstream_accounting_scope='Exclusion predicates on every final source row, before grammar/extent checks; counts can differ from first-failure native counts.')
manifest=dict(schema='fbp-route-manifest-v1',status='DELIVERED_WITH_TREE_AND_FRAME_HOST_BLOCKERS',production_ready=False,tree_seal=pin(sealpath),tree_seal_value=seal,tree_imports=codepin,slices=slices,passed_slices=[n for n in NAMES if slices[n]['status'].startswith('PASSED')],phrase=dict(decision='Original call text retained in production; radiator variant R invalidates c072905b extent content and raw row_bindings.',report=pin(ROOT/'out/PHRASE_DECISION.json'),variants={n:dict(file=artifact(s['variant_R'],s['rows']),changed_rows=s['changed']) for n,s in phrase['slices'].items()},registered_document=dict(path='/data2/jjyeung/agent_project_data/distill_design/PHRASE_KIT_K1_TRAIN_20261119.md',sha256='MISSING',note='Read once as instructed; the initial bounded read did not capture a file-byte digest. No second NFS read was made. The same rewrite rule is explicit in the supplied task prompt.')),camera=dict(selection=pin(ROOT/'out/CAMERA_SELECTION.json'),diff=pin(ROOT/'out/CAMERA_KR9C_DIFF.json'),frame_reference_occurrences=sum(len(r['qids']) for r in diff['references']),unique_frame_keys=diff['unique_references'],unique_kr9c_hashes=len(diff['unique_kr9c_sha256']),unique_k6tk_hashes=len(diff['unique_k6tk_sha256']),citing_rows=diff['citing_rows'],variant_A_count=camera['variants']['camera_wording']['row_count'],variant_B_count=camera['variants']['camera_B']['row_count']),config_handoff=configpin,compose=pin(ROOT/'out/COMPOSE_RESULT.json'),blocker_diagnostics=pin(ROOT/'out/BLOCKER_DIAGNOSTICS.json'),audit_results=pin(ROOT/'out/AUDIT_RESULTS.json'),staging=pin(ROOT/'out/STAGED_INPUTS_FINAL.json'),frame_coverage=pin(BASE/'fb_pack/FRAME_COVERAGE.json'),frame_byte_verification='MISSING: expected N frame-host staging and retained-frame audit receipts; no producer path or verified Q_E4 destinations supplied.',packaging=dict(archive='out/fbp_route.tar',sha256_file='out/fbp_route.tar.sha256',receipt='out/PACKAGE.json',rows_included=False,reason='New row files exceed the 300 MB inclusion limit; preserve source paths/pins and stage row bytes separately. No store was copied.'),commands=dict(phrase=R.PREFIX+'work/route.py 1',camera=R.PREFIX+'work/route.py 2',accounting=R.PREFIX+'work/route.py 3',envelopes=R.PREFIX+'work/route.py 4',intake=R.PREFIX+'work/intake.py',localization=R.PREFIX+'work/localize.py',audits=R.PREFIX+'work/audit.py',diagnostics=R.PREFIX+'work/diagnose.py',manifest=R.COMMAND,archive=R.PREFIX+'work/package.py'))
write('out/ROUTE_MANIFEST.json',manifest)
totals=collections.Counter()
for n in NAMES:totals.update(slices[n]['native_counts'])
report=[
'Host-side routing package delivered; production remains blocked. Four of six slices pass native intake with only sealed exclusion refusals. Recovery and camera require owner changes.',
'',
f'Tree seal: `{seal["tree_sha256"]}`. `TREE_IMPORTS.json` records and rechecks every tree dependency captured by the executed stages. No tree file was edited.',
'',
'| Slice | Final rows | Native admitted | Native refused | Result |',
'|---|---:|---:|---:|---|',
]
for n in NAMES+['camera_B']:
 s=slices[n];c=s['native_counts'];report.append(f'| {n} | {s["rows"]["row_count"]:,} | {c["admitted"]:,} | {c["refused"]:,} | {"PASS with exclusions" if s["status"].startswith("PASSED") else "BLOCKED"} |')
report.extend([
'',
f'The six primary slices contain {totals["seen"]:,} rows; all were covered by disjoint shards of at most 2,000 rows. Full envelopes were also called with `limit=2000`. Camera B is an alternative, not an extra training family.',
'Native refusal reasons: recovery—61 `excluded:eval_rooms`, 152 `R2 fallback calls again after a failed response`; absolute_distance—510 `excluded:eval_rooms`; units—510 `excluded:eval_rooms`; both coverage slices—none.',
'Camera A refuses 280 `excluded:eval_rooms`, 1,993 `Shared grammar: unit_quantity`, and 1,984 `Shared grammar: number_not_allowed,unit_quantity`. Camera B refuses 248, 1,936, and 1,938 respectively.',
'Upstream receipts run the actual seven-pin Exclusions.check, withheld-room check, merged-dev check, and native removal predicates over every final row. Their counts describe exclusion eligibility before grammar checks; native first-failure counts differ. No prefiltered flag skips a check.',
'',
'Radiator: the change affects 112/806/818/149/476 rows in recovery/absolute_distance/units/coverage_distance/coverage_units; camera changes zero. Every changed row fails the sealed extent-content comparison. Production keeps the original call text. Variant R changes only the obj phrase in ground-call strings; it is diagnostic and needs repacked spans and new independent extent/raw membership/source/coverage pins before use.',
'The independent extent-audit owner and tree_rebuild must regenerate the affected extent entries and config pin, plus V2H source constants/derivations and downstream bindings. No extent receipt was invented and no radiator REMOVE list is active.',
'Camera A removes the 21 unproven d2/vfc2c241f2978 rows. Camera B also removes 150 citing rows: 150 differing frame-reference occurrences across 7 unique keys and 7 kr9c/k6tk hash pairs. CAMERA_KR9C_DIFF.json lists every key, both pins, and citing QIDs. No PNG bytes were read or substituted.',
'K1: 21 recovery and 262 units rows were physically removed with existing native removal matches. The other final slices have zero K1 matches.',
'',
'All 37 checker runs pass, with zero R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4, and placeholder-object remove hits. The only K1 hits are 21/262 in diagnostic recovery/units variant R; every hit matches an existing removal list. Unselected intermediate row files were audited too.',
'',
'Recovery blocker: student_pilot/r2_contract.py:248 refuses the second distinct operand probe after the first reports failure in 152 sealed rows. The recovery contract owner must reconcile that guard with the authenticated event sequence; this lane did not weaken it.',
'Camera blocker: student_pilot/r2_grammar.py:183 invokes pinned trace_grammar.py, whose rules at :502/:509 reject unsupported signed arithmetic values and the +180-degree convention in canonical camera prose. The tree/camera owner must reconcile rendering/adaptation with a41ba191 or regenerate authenticated rows and bindings. BLOCKER_DIAGNOSTICS.json records exact examples.',
'Composition: the supplied deferred N config raises KeyError recovery at r1_routing.py:171. The concrete six-family first-boundary candidate refuses R1_CAMERA_SOURCE_PIN at r1_coverage.py:190. This w24 tree already includes camera_wording in source_names; its EXTRA_PINS still binds the old 6,000-row file and must be updated/resealed for the selected source.',
'Composition therefore stops before the host veto. A separate unmodified intake(limit=None) call refuses `Local slices must contain at most 2000 rows per family` at r2_intake.py:42 on trinity-1-18. No hostname, environment, or function was spoofed.',
'',
'Pin paths: portable envelopes carry u/<sha256>. Dry shard intake resolves them through the existing r1_persisted.scope map; withheld_rooms reads u/<sha256> relative to the workspace. out/localized envelopes instead carry absolute active pins and were checked without a scope. ENVELOPE_INDEX.json, STAGED_INPUTS_FINAL.json, and LOCALIZED_INDEX.json enumerate both forms.',
'Production must stage identical bytes under its root/u/<sha256> and run work/localize.py --tree <production-tree>; then bind the resulting envelope hashes and exact equal rows/extent pins. Its coverage and upstream exclusion paths are regenerated together. Inline kit localization alone does not rewrite nested envelope files.',
'CONFIG_HANDOFF.json supplies routing_inputs in config and request, row_slice_inputs, row_sources, source_membership, extent_receipt, and both routing-base fields. Exit deferred_first_boundary by omitting routing_slices at the first boundary. Preserve the fixed removal order.',
'Q_E4 must map /data2/k6tk and /data2/kr9c to verified absolute node-local roots. Those destinations and N raster/staging receipts are MISSING. Set Q_E7=1 only after the separate alias patch and reseal; preserve the local-node and non-Trinity vetoes. The named map/plan/FPS hashes were verified; raster/store readiness is not claimed.',
'The registered phrase document was read once; its file-byte SHA256 is MISSING because the initial bounded read did not capture it. The same rewrite policy is explicit in the task prompt. Its exact path is recorded in ROUTE_MANIFEST.json.',
'',
'Commands for all numbers (run from this workspace): prefix each Python command with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B`.',
'`work/route.py 1` produces radiator counts/pin checks; `2` produces camera counts/diffs; `3` produces final row/removal/accounting counts; `4` binds envelopes.',
'`work/intake.py` produces all native counts and composition refusals; `work/localize.py` checks absolute pins; `work/diagnose.py` attributes refusal types/examples; `work/audit.py` produces all checker and placeholder counts.',
'`work/finalize.py` computes the reference-occurrence total, verifies the recorded tree hashes, and writes this manifest/report. `work/package.py` computes package bytes and SHA256 and verifies archive members.',
'',
'Delivery: ROUTE_MANIFEST.json, fbp_route.tar, fbp_route.tar.sha256, and PACKAGE.json. The tar contains code, envelopes, coverage, receipts, audits, and reports. Row files exceed the 300 MB inclusion cap and are excluded; their exact paths/hashes remain in the manifest. The 1.7 GB store was not copied.',
])
assert len(report)<=100
(ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
status(7,'The final manifest and report identify four passing slices, recovery/camera contract blockers, exact config fields, staged-path rules, and all audits. Package creation and member verification are the remaining delivery step.')
print('primary totals',dict(totals),'report lines',len(report),'tree files',len(tree_inputs),flush=True)
