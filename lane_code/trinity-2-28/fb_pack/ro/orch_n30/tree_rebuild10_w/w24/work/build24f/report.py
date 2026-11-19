from pathlib import Path
import json,sys,gzip,re,subprocess
L=Path(__file__).resolve().parents[2];D=L/'work/build24f';sys.path.insert(0,str(L/'work/build24'));import joblib as J
kits=J.load(D/'KIT.json');go=J.seal(L/'out/kit_n_go');tree=J.load(L/'out/TREE_SEAL.json')['tree_sha256'];uploads=J.load(L/'out/UPLOADS_24F.json')
assert all(v['returncode']==0 for v in J.load(D/'SUITES.json'))
for name in ('KIT_TESTS','NAMING_TESTS','LAUNCH_TESTS','RESOLVER_TESTS','REFRESH_TESTS'):assert J.load(D/(name+'.json'))['successful']
for name in ('LIVE_TESTS','LIVE_REPEAT','RUNTIME_TESTS','PERSISTENCE_TESTS'):assert J.load(D/(name+'.json'))['passed']
assert J.load(D/'PIN_TESTS.json')['status']=='PASS'
assert J.load(D/'INVARIANTS.json')['status']=='PASS'
assert not J.load(D/'COVERAGE.json')['uncovered']
for name,k in [('q',L/'work/build24/kits/q'),('n',L/'work/build24/kits/n'),('n_go',L/'out/kit_n_go')]:
 v=json.loads(gzip.decompress((D/('SCAN_'+name+'.json.gz')).read_bytes()));assert v['status']=='PASS' and v['kit_seal']==J.seal(k)
validated=[dict(name=x,status='PASS') for x in ('guard:17 per kit','kit:5','naming:7','resolver:7 plus 600/23 suites','launch:7','selection refresh:5','isolated room pins:2','path refusals:12','persistence:4','live copier:5 plus 4 repeated','runtime:4','changed statements:8/8')]
J.write(D/'FINAL_VALIDATION.json',dict(status='PASS',checks=validated,distributed_execution='EXTERNAL_SCRIPT_REQUIRED',native_thread_limit='8 in canary; admission caps at 16'))
card=f"""Vehicle N uses MINIMAL. Normal kits have GO=false; only out/kit_n_go is armed and it is not uploaded.
Init is P's step-400 export 5083243c from run 6ed2c7aa through its authenticated export-only receipt.
No checkpoint or state after P's step 400 initializes N. No handover fill remains.
Tree: `{tree}`.
Kit n: `{kits['n']['kit_seal']}`; kit q: `{kits['q']['kit_seal']}`.
GO variant: `{go}`. Seals: work/build24f/KIT.json and out/UPLOADS_24F_GO.json.
N requests advanced, four GPUs/four ranks, one launcher, 48 CPUs, 800G and 24:00:00.
SBATCH signals the batch shell with TERM 600 seconds before the limit. The allocation runs its own mode-q canary.
TK_JOB_START records allocation-start epoch seconds and reaches bwrap, torch.distributed.run and train().
Shell CPU-stage OMP/MKL/OpenBLAS limits are 48. Native canary admission uses 8 Torch threads; training uses 8 per rank.
Checkpoint cadence is step 1, every 7,200 seconds, and at stop. Timed checkpoints remain node-local.
Exports occur at local steps 100, 200, 400, 600, 800, 1000, and at stop.
The batch shell copies log tails, metrics, attempt/run metadata, marker hashes and .steps every 600 seconds and at EXIT/TERM/USR1.
Each small copy is at most 50 MB, including at most 40 MB of log tails, under x_22c714e1/o/<jobid>/live/ on /project.
A separate worker checks export artifact markers every 10 seconds and sends immutable export tars through four GCS parts when sessions exist.
SESSION_NAMES_24F.json fixes milestone names plus three once-claimed stop generations. Without sessions, the tar and an explicit marker remain local.
At exit, the latest completed stop checkpoint goes to x_22c714e1/n_ck/<jobid>/ if its size plus 50 GiB is free; otherwise GCS is attempted or it remains local with a marker.
Small-file GCS mirroring awaits the orchestrator's credential ruling. The kit contains no credential or session URL.
Accepted loss: if the node dies between exports, the leg restarts from the last export with a fresh optimizer.
Declaration: r1_training.routing_slices=deferred_first_boundary; init_policy=step400_export_weights_fresh_v1.
N starts a fresh optimizer, counter and schedule at zero. Its first 200 steps are local steps 1–200 from P's step-400 weights.
N keeps P's regenerated S1 routing base (receipt ca0616db, database 4e8e6c04); all six deferred routing cells contain zero new rows.
Distance calls, unit conversions and camera wording receive no targeted new routing examples; routing-slice gates start when those slices enter.
VQA adds 7,971 direction half-turn twins and removes 109 named-route matches (107 newly removed), leaving 55,808 direction and 8,562 route-planning rows (work/build24/CENSUS.json).
Held-out wording exclusions, K1 removals and room rules remain active. P's opener rows stay routing_opener_init=keep; the step-544 lineage remains pinned.
The two absent head slots retain NOT_PRESENT; seven other slots stay DEFERRED and block official reads. The pose record remains bound.
Relative-count rows, answer-prior weights, frame-host alias and step-time patches wait for the first boundary.
N has no tower-scale freeze in the point-depth head; H3 can fire again at the first look for the same cause.
"""
assert len(card.splitlines())<40;(L/'out/N_CARD_KIT_ROWS.md').write_text(card)
prepared=(D/'rehearsal/PREPARED.json').exists()
canary='ADMIT; room audit, v.json producer and fixture gate checks pass' if prepared else 'preparation passed; full synthetic frame audit is not yet certified'
text=f"""BUILD24F PACKAGED FOR REVIEW; four-rank training awaits the external CPU script. Normal kits remain GO=false.
Tree: {tree}. The only tree change is launch_r2/persistence.py (out/PERSIST24F.patch).
Kit n: {kits['n']['kit_seal']}; kit q: {kits['q']['kit_seal']}; GO: {go}.
24e is delivered in out/DELIVERY_24E.json with its report, upload diff and immutable package.
N requests advanced, 4 GPUs, 48 CPUs, 800G and 24 hours; k/a.json and BUILD.json match job.sh.
CPU-stage OMP/MKL/OpenBLAS limits are 48 in job.sh and tk_env; the four training workers use 8 each.
LIMIT: native production_proof calls s1_admission with threads=8, and admission caps it at 16. Raising that native stage to 48 is outside the allowed tree/admission changes.
Kit q only receives the new sealed source and source pins; its 8-CPU/192G/12-hour proof request is unchanged.
TK_JOB_START is exported before staging and explicitly enters bwrap. The launcher preserves it; CPU view prints TK_JOB_START=1795111111 (RUNTIME_TESTS.json).
Two batch-shell workers independently publish small evidence every 600 s and inspect export markers every 10 s; EXIT/TERM/USR1 perform a final copy.
The supplied decoded runtime contains tk_step but no tk_persist_small; b/pc.sh and b/pc.py provide the requested batch-shell persistence.
SBATCH --signal=B:TERM@600 targets the batch shell. The copier reads the resolver's actual training output, Q_ROOT/r.
Small publications include t/q/h/rooms tails, metrics, attempt/run JSON, .steps and marker names/sizes/SHA-256; they never read weights for their listing.
A shared 50 MB copy cap includes a 40 MB total log-tail budget. TERM and concurrent-upload tests pass (LIVE_TESTS.json, LIVE_REPEAT.json, RUNTIME_TESTS.json).
Each immutable m export uses the unchanged gcsput.py split writer, four parts/four workers, and a verified object/bytes/SHA-256 done marker.
Global project claims reserve fixed milestone objects and mstop/mstopB/mstopC once. Failed sends retry on the next pass; native archives are reused without duplicate in-flight tars.
Missing sessions produce 'export not uploaded: no sessions' and retain the node-local tar. No session URL or Google credential was added.
The exit path copies only the latest completed stop checkpoint to n_ck/<jobid> after size+50 GiB admission; insufficient space uses ckstop GCS or records that it remains local.
Two-hourly checkpoints stay local. Small-evidence GCS mirroring remains pending the orchestrator's credential ruling.
Persistence permits the local path only for r1_training present and r2_persistence absent; explicit persistence bindings retain their upload behavior and every invalid binding still refuses.
Local receipts retain source/archive pins, parts=[], durable=false and project_required=false. Tests prove identical export bytes and receipt pins against a stub uploader (PERSISTENCE_TESTS.json).
All eight changed statements execute; local checkpoint/export, configured upload, invalid bindings, native-state and disk refusals pass (COVERAGE.json).
Decoded scans pass for q/n/GO; guard (17 per kit), kit, naming, resolver, launch, selection-refresh and room-pin suites pass (FINAL_VALIDATION.json).
The hidden-path q/n runs pass staging, guard, room authority/audit and publication; their canaries stop at missing production routing payload a67a3f6f489031d4.jsonl.gz (SEQUENCE.json).
Synthetic canary: {canary}. No distributed optimizer step is claimed in this sandbox.
Run work/build24f/go_rehearsal.sh outside the sandbox: nice 10, OMP 8, gloo, 4 CPU ranks, aggregate RSS guard 19 GB, output work/build24f/rehearsal.
REHEARSAL_OVERRIDES.json and FIXTURE_DIFF.json enumerate fixture differences. REHEARSAL_PATHS.md lists native calls, refusals, outputs and the one-line-per-path checker.
The script is designed to test step-1 persistence, a milestone export/copier done marker, timed checkpoint, allocation-age self-stop with checkpoint/export, and latest resume for one more step; these distributed paths remain unproved here.
Upload delta after 24e: {uploads['total_files']} files, {uploads['total_bytes']} bytes; stream root work/build24f/upload; names out/UPLOADS_24F.list. The GO-only three-file diff is not authorized for upload.
Config, admission, legality, trained groups, export contents, removals, opener rows, step-544 lineage, resolver identities and DEFERRED checks are unchanged (INVARIANTS.json).
The card records cadence and accepted loss: node death between exports restarts from the last export with a fresh optimizer.
Package SHA-256, byte count, verified member seal and workspace growth are in out/DELIVERY_24F.json. Existing packages remain unchanged; no upload or submission ran.
Evidence paths without a prefix are under work/build24f. Superseded files remain in attic; compressed fixture evidence is lossless and indexed by COMPRESSED_EVIDENCE.json.
"""
assert len(text.splitlines())<40;(L/'out/BUILD24F_REPORT.md').write_text(text)
p=L/'out/TREE_FILES.sha256';a=L/'attic/build24f/TREE_FILES.sha256'
if not a.exists():p.rename(a)
files=J.load(D/'TREE_FILES.json');p.write_text(''.join(f'{h}  {n}\n' for n,h in sorted(files.items())))
print('Report',len(text.splitlines()),'lines; card',len(card.splitlines()),'lines')
