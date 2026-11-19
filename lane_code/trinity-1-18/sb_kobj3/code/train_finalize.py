"""Report unavailable train contrasts and package the exact feasibility evidence."""
from common import *
import ast,tarfile

BOX=Path('/scratch/jjyeung/orch_n30/sb_kbox4')

def main():
 pins()
 census=js(ROOT/'out/TRAIN_CENSUS.json');probe=js(ROOT/'out/CPU_TRACK_FEASIBILITY.json')
 plan=js(ROOT/'out/CPU_TRACK_PLAN.json')
 inherited_gpu=js(Path('/scratch/jjyeung/orch_n30/sb_kobj2/out/GPU_NEED.json'))
 assert inherited_gpu['memory_gib']==48
 for p in [ROOT/'out/COPY_RECEIPT.json',ROOT/'out/TRACK_SELECTION.json',ROOT/'inputs/local/K1_MANIFEST.json']:
  data=js(p)
  PINS.update(data.get('input_sha256',{}))
 old=js(ROOT/'config/KBOX_RULES_HOOK.json')
 module_path=BOX/'box_math.py';blob=read(module_path)
 exports={n.name for n in ast.parse(blob).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
 required=old['required_interface'];missing_exports=sorted(set(required)-exports)
 receipt_path=BOX/'out/box_ladder/DECISION.json'
 replay_path=BOX/'out/box_ladder/REPLAY_CHECK.json'
 missing_paths=[str(p) for p in [receipt_path,replay_path] if not p.is_file()]
 # Do not normalize an unfinished sibling decision or infer a fusion winner.
 receipt=js(receipt_path) if receipt_path.is_file() else None
 sibling_status=read(BOX/'STATUS.md').decode().strip()
 ready=bool(receipt and receipt.get('selection_split')=='K1-train' and receipt.get('choices_frozen') is True and not missing_exports)
 if ready:raise RuntimeError('Sibling is now ready; consume its real interface and run pricing before finalizing')
 hook=dict(status='MISSING',module_path=str(module_path),module_sha256=sha(module_path),receipt_path=str(receipt_path),receipt_sha256=sha(receipt_path) if receipt else None,replay_path=str(replay_path),expected_normalized_decision=str(ROOT/'inputs/KBOX_DECISION.json'),required_interface=required,reason='sb_kbox4 has no complete frozen train receipt or required object-source/track-pricing interface; A0 must use R1 serving geometry')
 write(ROOT/'config/KBOX_RULES_HOOK.json',hook)
 from box_hook import load
 try:load(True)
 except Missing as exc:gate_error=str(exc)
 else:raise AssertionError('Unready hook did not refuse')
 write(ROOT/'out/OBJECT_GATHER_READINESS.json',dict(status='MISSING',module_exports=sorted(exports),missing_exports=missing_exports,missing_paths=missing_paths,sibling_status=sibling_status,hook_failure=gate_error,geometry='Required: sb_kbox4 R1 serving geometry; no GT-geometry substitute',frozen_rule=None,independent_arm_reason='The object_source and count_objects interfaces are absent, independent of frozen fusion choice. Legacy gather alone does not implement the specified merged object set.'))
 counts=census['counts'];allc=counts['all']
 arms=['object_today','object_frozen','track_today','track_frozen']
 comparisons=[]
 for rowset in ['K1_TRAIN_1037.txt','K1_TRAIN_TABLES_883.txt']:
  ids=set(read(ROOT/'inputs/rowsets'/rowset).decode().splitlines())
  for ds,c in counts.items():
   n=c['rows'] if rowset=='K1_TRAIN_1037.txt' else c['table_rows']
   for arm in arms:
    comparisons.append(dict(arm=arm,reference='present source: A0 on R1 serving geometry',rowset=rowset,dataset=ds,registered_rows=n,evaluated_paired_rows=0,status='MISSING',arm_score=None,present_score=None,difference=None,paired_room_bootstrap_ci95=None,refusals=None,reason='CPU predictor unavailable' if arm.startswith('track') else 'Sibling object-source and frozen decision interface unavailable'))
 stats=dict(method='item-weighted paired physical-room percentile bootstrap',draws=10000,seed=20261119,interval=[2.5,97.5],refusal_score=0,missing_policy='An unexecuted arm is MISSING, not a zero-scored refusal. No bootstrap is computed without paired predictions.')
 write(ROOT/'out/K1_TRAIN_RESULTS.json',dict(status='MISSING',selection_split='K1-train',comparisons=comparisons,statistics=stats))
 write(ROOT/'out/K1_TRAIN_DIAGNOSTICS.json',dict(status='MISSING',selection_split='K1-train',by_dataset={d:dict(registered_capture_names=c['capture_name_jobs'],object_n_all=None,object_n_conf=None,n_track=None,n_track_conf=None,first_seen_pair_rate_object=None,first_seen_pair_rate_linker=None,first_seen_pair_rate_track=None) for d,c in counts.items()},reason='No object-source output or tracker output; no registered first-seen pair outcomes supplied by sibling hook.'))
 write(ROOT/'out/GPU_NEED.json',dict(status='NEEDED_NOT_AUTHORIZED',selection_split='K1-train',remaining_captures=allc['captures'],remaining_capture_name_jobs=allc['capture_name_jobs'],remaining_rows=allc['rows'],completed_captures=0,GPU_hours_used=0,cards=1,memory_gib=48,estimated_gpu_hours=1.3,hard_stop_hours=1.75,estimate_basis='Unmeasured estimate from named KIT_SPEC_object_route_r0dev_v2.md sections 3b/3e; no extrapolation from failed CPU imports.',measured_gpu_memory=None,measured_cpu_tracking_seconds=None,full_train_cpu_hours=None,requirements=['Orchestrator GPU authorization and exclusive ledger lease','SAM 3 runtime with iopath, timm, einops and its other staged dependencies','Staged pinned checkpoint and 32 anchor frames per registered capture','sb_kbox4 object-source and track-pricing interface for scored contrasts'],command_reference='bash scripts/gpu_k1_track.sh in the originating sb_kobj2 kit after its GPU authorization requirements are satisfied; not executed by this CPU-only task',scope='Only K1-train tracking; no R0-dev, held-out, dev-S1, added views or GT-geometry arms'))
 table=['# K1 training contrasts','', 'Status: MISSING. No arm produced paired predictions. Unexecuted arms are not counted as refusals.','', '| Dataset | Registered rows | Table rows | Captures | Rooms | Capture/name jobs |','|---|---:|---:|---:|---:|---:|']
 for d,c in counts.items():table.append(f"| {d} | {c['rows']} | {c['table_rows']} | {c['captures']} | {c['rooms']} | {c['capture_name_jobs']} |")
 table+=['','| Arm vs present A0 | Rowset | Paired rows evaluated | Arm score | Present score | Difference [95% CI] | Refusals |','|---|---|---:|---|---|---|---|']
 for rowset in ['K1_TRAIN_1037.txt','K1_TRAIN_TABLES_883.txt']:
  for arm in arms:table.append(f'| {arm} | {rowset} | 0 | MISSING | MISSING | MISSING | MISSING |')
 table+=['','The JSON companion gives each contrast for all three datasets and the pooled set. Both arms must use exactly the named rowset; a future run must not drop rows refused by either arm.','', 'Paired intervals require 10,000 physical-room bootstrap draws, seed 20261119, item-weighted means, and 2.5/97.5 percentiles. Executed refusals score zero. No interval is available without paired predictions.','', 'First-seen pair rates and object/track counts are MISSING for every dataset. Census counts above count jobs, not detected objects.','', 'The CPU predictor imports fail at `iopath`; the staged factory also requires a nonempty CUDA GPU list and the predictor calls `.cuda()`. No frame was tracked.','', f'The sibling must supply `{receipt_path}` and the exports `{", ".join(missing_exports)}` in `{module_path}`. The existing hook points to sb_kbox4 and refuses pricing until those inputs are ready.','', 'Commands: `bash scripts/train_cpu.sh code/train_prepare.py`; `bash scripts/train_cpu.sh code/train_cpu_probe.py`; `bash scripts/train_cpu.sh code/train_finalize.py`.']
 (ROOT/'out/K1_TRAIN_TABLES.md').write_text('\n'.join(table)+'\n')
 attempts=probe['attempts']
 report=[
 'Both requested arms remain MISSING; no training accuracy or first-seen/count result was produced.',
 f"The registered workload is {allc['rows']} rows, {allc['captures']} captures, {allc['rooms']} rooms and {allc['capture_name_jobs']} capture/name jobs across all three datasets.",
 'The table-covered rowset contains 883 rows. Each unavailable arm/reference contrast is recorded on both fixed rowsets in K1_TRAIN_TABLES.md and K1_TRAIN_RESULTS.json.',
 'Census command: `bash scripts/train_cpu.sh code/train_prepare.py`.',
 '',
 'CPU feasibility: the two specified train captures were attempted with all registered operand names and 32 anchors planned per capture.',
 'Both attempts failed while importing SAM 3: `ModuleNotFoundError: No module named iopath`.',
 'The source independently requires a nonempty CUDA GPU list and calls `.cuda()`; the staged predictor has no CPU configuration.',
 'These are failed construction attempts, not completed two-capture tracking benchmarks.',
 'No checkpoint was loaded and no frame was decoded or tracked. Full-set CPU hours and the six-hour subset size are MISSING.',
 'The conditional subset rule was fixed before attempts: SHA256-sorted captures within dataset, round-robin all three datasets, complete captures/all names, at most six process CPU-hours.',
 'No subset ran because no successful pilot timing exists.',
 'Probe command: `bash scripts/train_cpu.sh code/train_cpu_probe.py`.',
 f"Attempt overhead: {sum(a['attempt_wall_seconds'] for a in attempts):.6f} wall seconds; {sum(a['attempt_cpu_seconds'] for a in attempts):.6f} process CPU seconds; peak RSS {probe['peak_rss_kib']} KiB. These are not inference costs.",
 '',
 'The object-gathering hook points to read-only sb_kbox4 and remains MISSING.',
 f'Missing expected receipt: `{receipt_path}`.',
 f'Missing expected replay receipt: `{replay_path}`.' if not replay_path.is_file() else f'Replay receipt exists: `{replay_path}`.',
 f'Missing exports in `{module_path}`: {", ".join(missing_exports)}.',
 'The missing object-source/count interface blocks gathering independently of the frozen fusion choice. Legacy gather is not a substitute for the specified merged object set.',
 'No A0 geometry was substituted, no GT-geometry arm ran, and no fusion winner was invented.',
 'Readiness, diagnostics and contrast-report command: `bash scripts/train_cpu.sh code/train_finalize.py`.',
 '',
 'Paired intervals, refusals and first-seen/object counts remain MISSING. A missing execution is not a zero-scored refusal.',
 'Future paired scores use identical registered rows, refusals scored zero, 10,000 room-bootstrap draws and seed 20261119.',
 'GPU_NEED.json records the specification estimate for all remaining tracking: one 48 GiB card, 1.3 GPU-hours estimated, 1.75-hour hard stop; no GPU timing was measured.',
 'No GPU is authorized or used by this task.',
 '',
 'Isolation: CPU-only PyTorch, nice 10, eight threads, 38,000,000 KiB virtual-memory cap; all writes stay in this workspace.',
 'Only the named specification was copied from NFS. Kit code/configuration/scripts and train rowsets were copied locally; evaluation data and inherited result tables were excluded.',
 'The mixed local manifest container was hashed; only explicit training blocks were decoded. No held-out caches, labels, frames or outcomes and no R0-dev data were opened.',
 'No SSH, network, Git, process termination, tmux operations, model downloads or GT-geometry evaluation ran.',
 'JSON evidence records input SHA256 values. The copied train manifest preserves existing registration; no membership, frame map or proof was invented.',
 'Archive command: `bash scripts/train_cpu.sh code/train_finalize.py`; verification: `sha256sum -c out/sb_kobj3.tar.sha256`.',
 'The archive includes code, train inputs, configuration and evidence; ARCHIVE_MANIFEST.json records each member hash. PACKAGE.json records archive verification.',
 'No borderline revision-history prose is retained.',
 ]
 assert len(report)<=60
 (ROOT/'out/REPORT.md').write_text('\n'.join(report)+'\n')
 status('The train-only feasibility work is complete, but both requested evaluation arms are MISSING. SAM 3 failed to import iopath on both capture attempts and its staged predictor requires CUDA. sb_kbox4 has no frozen train receipt or object-source/count/track-pricing interface. The tables preserve all registered denominators with missing metrics; GPU_NEED.json records the specification estimate for the remaining workload. The report and SHA256-verified archive are delivered; no R0-dev or held-out outcome was opened.')
 # Keep each JSON's provenance field even for copied configuration files.
 for p in sorted((ROOT/'config').glob('*.json')):
  d=json.loads(p.read_text());assert 'input_sha256' in d
 exclude={'ARCHIVE_MANIFEST.json','PACKAGE.json','sb_kobj3.tar','sb_kobj3.tar.sha256','train_finalize.log'}
 members=[p for base in ['code','config','inputs','out'] for p in (ROOT/base).rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name not in exclude]
 members += [ROOT/'scripts/train_cpu.sh',ROOT/'STATUS.md']
 member_hashes={str(p.relative_to(ROOT)):sha(p) for p in sorted(members)}
 write(ROOT/'out/ARCHIVE_MANIFEST.json',dict(status='COMPLETE',members=member_hashes))
 members.append(ROOT/'out/ARCHIVE_MANIFEST.json')
 archive=ROOT/'out/sb_kobj3.tar'
 with tarfile.open(archive,'w') as tf:
  for p in sorted(members):tf.add(p,arcname=str(p.relative_to(ROOT)),recursive=False)
 with tarfile.open(archive,'r') as tf:
  expected=dict(member_hashes,**{'out/ARCHIVE_MANIFEST.json':sha(ROOT/'out/ARCHIVE_MANIFEST.json')})
  assert set(tf.getnames())==set(expected)
  for n,h in expected.items():assert hashlib.sha256(tf.extractfile(n).read()).hexdigest()==h,n
 h=sha(archive)
 (ROOT/'out/sb_kobj3.tar.sha256').write_text(h+'  out/sb_kobj3.tar\n')
 write(ROOT/'out/PACKAGE.json',dict(status='COMPLETE',evaluation_status='MISSING',archive='out/sb_kobj3.tar',sha256=h,members=len(members),verified=True))
 print(json.dumps(dict(status='MISSING',archive=str(archive),sha256=h,members=len(members))))

if __name__=='__main__':main()
