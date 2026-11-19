"""Create the current review artifacts without running GPU work or pricing new rows."""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
import ast,difflib,tarfile
from camera_records import frame_binding
from budget import ORDER,HOURS
OUT=ROOT/'out';T=OUT/'tower_frames'

def ranges(values):
 values=sorted(set(values));groups=[]
 for v in values:
  if groups and v==groups[-1][-1]+1:groups[-1].append(v)
  else:groups.append([v])
 return ','.join(str(g[0]) if len(g)==1 else str(g[0])+'-'+str(g[-1]) for g in groups)

def edits():
 sources=read_json(ROOT/'inputs/CODE_SOURCES.json')['input_sha256'];blocks=[];patches=[]
 pack=Path('/scratch/jjyeung/n30_mirror/sb_headacc2/pack/r1_src/b')
 for origin,expected in sources.items():
  if '/tree_b01ce449/' in origin:rel=origin.split('/tree_b01ce449/',1)[1]
  elif '/b04_e2ehook/' in origin:rel=origin.split('/b04_e2ehook/',1)[1]
  else:continue
  target=ROOT/'code/vendor'/rel
  if not target.exists():continue
  original=pack/rel if rel.startswith('e2e_reader/') and (pack/rel).exists() else Path(origin)
  actual=sha(original)
  if original==Path(origin):assert actual==expected
  old=original.read_text().splitlines(True);new=target.read_text().splitlines(True)
  if old==new:continue
  patches.extend(difflib.unified_diff(old,new,fromfile=str(original),tofile=str(target.relative_to(ROOT))))
  for tag,a,b,c,d in difflib.SequenceMatcher(None,old,new).get_opcodes():
   if tag!='equal':blocks.append(dict(file=str(target.relative_to(ROOT)),source=str(original),source_sha256=actual,original_lines=list(range(a+1,b+1)),edited_lines=list(range(c+1,d+1)),old=old[a:b],new=new[c:d]))
 write_json(OUT/'EDITED_LINES.json',dict(edits=blocks));(OUT/'EDITED_LINES.patch').write_text(''.join(patches))
 by={}
 for b in blocks:by.setdefault(b['file'],[]).extend(b['edited_lines'])
 return by

def main():
 dry=read_json(OUT/'DRYRUN.json');tests=read_json(OUT/'TESTS.json');join=read_json(ROOT/'inputs/CAMERA_FRAME_JOINS.json')
 assert tests['status']=='PASS'
 assert dry['status']=='PASS','Section 8 must pass before delivery'
 pins=code_pins();assert dry['code_sha256']==digest(pins),'Dry run must match delivered code'
 sha(ROOT/'inputs/TASK_RULINGS.txt')
 for path in ('scripts/finalize_v3.py','scripts/bind_camera.py'):sha(ROOT/path)
 hook=read_json(ROOT/'configs/KBOX_WINNING_BOX_RULE.json')
 for path in ('a0_path','decision_path','freeze_path'):sha(hook[path])
 changed=edits()
 write_json(OUT/'CODE_SHA256.json',dict(files=pins,code_sha256=digest(pins)))
 import shutil
 for name in ('CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch'):shutil.copyfile(OUT/name,T/name)
 blockers=[dict(scope='CPU section 8b',**r) for r in dry['B']['captures'] if r['status']!='PASS']
 binding=dry['C']['frame_binding']
 if binding['status']!='PASS':blockers.append(dict(scope='GPU Part C',**binding))
 write_json(OUT/'BLOCKERS.json',dict(status='BLOCKER' if blockers else 'PASS',blockers=blockers,part_C_dense_skips=join['dense_missing']))
 for n in ('A_POSE.json','A_DEPTH.json','A_DISTANCE.txt','B_LADDER_TRAIN.txt','B_GAINS_ONCE.txt','HELDOUT_once.txt'):
  write_json(T/n,dict(status='MISSING',rows=[],reason='GPU pass not run; CPU self-comparisons are in out/DRYRUN.json',object_variant='NOT_APPLICABLE: no object variant frozen',heldout_role='Report only after DECISION.json'))
 write_json(T/'C_PARITY.json',dict(status='NOT_RUN',reason='CPU-only task; real G32 text parity requires a GPU pass',bound=binding['bound'],required_matches=440,total=450))
 write_json(T/'C_CAMERA.txt',dict(status='NOT_RUN',role='DIAGNOSTIC_ONLY',no_decision_bar=True,frame_binding=binding,reason='No GPU camera outputs produced in this workspace'))
 write_json(T/'PASS_TIMING.json',dict(gpu_passes=[],gpu_hours_used=0,cpu_seconds=dry['seconds'],cpu_peak_kib=dry['peak_cpu_kib'],peak_gpu_policy='Measure first capture of every pass; stop above 40,000,000,000 bytes'))
 write_json(T/'AVAILABILITY.json',dict(status='MISSING',reason='No GPU arm priced'))
 launch_blockers=list(blockers)
 for name,scope in [('GPU_GO.json','orchestrator GO'),('SHARED_GPU_RESERVATION.json','shared-ledger reservation'),('DA3_GO.txt','GPU Part C DA3 GO')]:
  p=ROOT/'inbox'/name
  if not p.is_file():launch_blockers.append(dict(status='MISSING',scope=scope,expected_path=str(p)))
 steps=[dict(part=p,expected_gpu_hours=e,hard_stop_hours=h,command=f'CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_{p}.sh') for p,e,h in [('A',.5,.75),('B',2.5,3.),('C',.6,.75)]]
 write_json(OUT/'GPU_NEED.json',dict(status='NOT_LAUNCHED',code_sha256=digest(pins),cpu_dryrun=dry['status'],cards=1,max_concurrent_cards_shared=2,card_memory_gb=24,max_allocated_bytes=40000000000,measured_peak_bytes=None,gpu_hours_used=0,expected_gpu_hours=3.6,hard_stop_gpu_hours=4.5,sharing=dict(ruling='0749Z',room_kit_expected_gpu_hours=.2,combined_expected_gpu_hours=3.8,allowed_on_same_card=True,schedule='Use the assigned card sequentially with the room kit; each pass retains its shared-ledger reservation'),environment='/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python',steps=steps,shared_cap_gpu_hours=16,shared_order=ORDER,shared_hard_hours=HOURS,cut_order=list(reversed(ORDER)),reservation_hook=str(ROOT/'inbox/SHARED_GPU_RESERVATION.json'),go_hook=str(ROOT/'inbox/GPU_GO.json'),ledger_owner='Swarm_build2 orchestrator',launch_blockers=launch_blockers,da3_go_hook=str(ROOT/'inbox/DA3_GO.txt'),part_C=dict(bound32=binding['bound'],bound64=binding['bound64'],dense_missing=join['dense_missing'],real_parity='NOT_RUN'),requirements=['Ampere or newer (bf16)','vnice','scratch-only assets and writes','hard stops','hash-validated DONE resume','explicit GPU GO bound to delivered code','Part C inbox/DA3_GO.txt containing a standalone GO line']))
 pyfiles=list((ROOT/'code').rglob('*.py'))+[ROOT/'scripts/finalize_v3.py',ROOT/'scripts/bind_camera.py']
 for p in pyfiles:ast.parse(p.read_text())
 write_json(OUT/'VALIDATION.json',dict(status='PASS',python_files=len(pyfiles),unit_tests=tests['tests'],shell_command='bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh',command='bash scripts/cpu.sh scripts/finalize_v3.py'))
 rows=sum(len(c.get('rows',[])) for c in dry['B']['captures'])
 missing_paths=sorted({p for x in join['dense_missing'] for p in x.get('expected_paths',[])})
 report=f'''The tower-frames section-8 CPU dry run is {dry['status']}. No GPU time was used.
The accepted specification has SHA256 133e8cfdbb149401767c76fc5908154b9dd106d2a4b580bcca81d207615169aa.

Run these commands from `{ROOT}`:
- `sha256sum inputs/KIT_SPEC_tower_frames_v2.md` verifies the accepted spec.
- `bash scripts/cpu.sh scripts/bind_camera.py > out/bind_camera.log 2>&1` produces the camera joins and byte-hash audit.
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v3.log 2>&1` produces every section-8 count and timing below.
- `bash scripts/cpu.sh code/test_kit.py > out/tests_v3.log 2>&1` produces the regression result.
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh scripts/run_H.sh` checks launcher syntax.
- `bash scripts/cpu.sh scripts/finalize_v3.py` produces the report, GPU request, code hashes, edited-line audit, and archive.

Section 8a: {dry['A']['status']}; five train captures have zero stored-C64 self-comparison differences for pose, depth and distance. All five median_ratio scales agree with stored convert scales within 1e-4 relative.
Section 8b: {dry['B']['status']}; {rows} A0 rows on five train captures match sb_kbox4 exactly in prediction, member frames and box values. The "response" match compares a re-formatted prediction; kbox4 rows store no response text.
The N=32 comparison rebuilds geometry through the same function used by Part B: own-depth median_ratio, float32 exp(log(scale)), checkpoint gravity and the serving guard.
Section 8c: {dry['C']['status']}; all 450 staged records and calls parse; synthetic formatting uses a staged scale and gravity. Real 440/450 text parity remains a GPU check.
Section 8d: {dry['numbering']['status']}; all {dry['numbering']['captures']} captures pass numbering and {dry['numbering']['frame_sha256_assertions']} anchor/model-row hash assertions.
N=32 lifting matches the original tree on all five train captures; the N=64 fixture visits all 64 slots.
At N=64 the unchanged selector still divides frame counts by 32/31, so features can exceed 1. Raw depth AbsRel uses unscaled G3T depth.
The dry run took {dry['seconds']:.3f} seconds and peaked at {dry['peak_cpu_kib']} KiB RSS. The launcher uses nice 10 and eight numerical threads.
Regression tests: {tests['tests']} PASS. The validation receipt records Python parsing and shell syntax checks.

Part C binds all {join['bound']} items by exact scene and ordered source-frame indices in existing local A_MANIFEST records, with every PNG byte hash verified.
The audit verified {join['unique_frames_verified']} unique PNGs ({join['frame_bytes_verified']} bytes); {join['bound64']} items also bind to 64-frame DENSE records whose anchors match those PNG hashes.
The request supplies the frame root and bundle identity; the local manifests supply the explicit scene/index/hash mapping. No filename-to-scene mapping was inferred.
The remaining {len(join['dense_missing'])} items have 32-frame parity inputs but MISSING dense inputs for scannet/scene0475_00 and scannet/scene0475_01. They are skipped only in dense camera arms.
Exact missing dense manifests:
{chr(10).join('- `'+p+'`.' for p in missing_paths)}
`inputs/CAMERA_FRAME_JOINS.json` records every item, source and hash; `out/CAMERA_BINDING.json` and `out/BLOCKERS.json` list the dense skips.

The box kit freezes no object variant: replace_box part 1 FAIL; fused_path PASS applies to GT masks only. This kit uses today arms and one added-frame-gain comparison.
Part B runs independently of Part A's bars. The 1,012 K1 train rows outside withheld rooms decide the bars; full 1,037-row figures are report-only; held-out scores remain report-only after DECISION.json. No held-out values were evaluated here.
The scripts retain vnice, scratch-only assets/writes, hash-validated DONE resume, shared-ledger admission and an explicit GPU GO bound to code hashes.
Prepared commands are `bash scripts/run_A.sh`, `bash scripts/run_B.sh`, and `bash scripts/run_C.sh`, each with one explicitly assigned CUDA_VISIBLE_DEVICES.
GPU_NEED.json requests one 24-GB Ampere-or-newer card: A 0.5 expected/0.75 hard-stop GPU-h; B 2.5/3.0; C 0.6/0.75. It stops allocations above 40 GB; actual GPU memory remains unmeasured.
Ruling 0749Z permits this kit's 3.6 expected GPU-h and the room kit's 0.2 to share one card. Schedule them sequentially under the shared 16 GPU-hour ledger.
CPU interpreter: `/scratch/jjyeung/envs/p1cpu/bin/python`; prepared GPU interpreter: `/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python`.
`out/EDITED_LINES.json` and its patch list every copied-source edit; `out/CODE_SHA256.json` pins the delivered code. All generated JSON receipts record input SHA256 values.
GPU performance and decision outputs are MISSING/NOT_RUN. No GPU, network, SSH, Git, tmux or process-control action ran; the archive was not mirrored.
Archive: `out/sb_ktfix3.tar`; verify with `sha256sum -c out/sb_ktfix3.tar.sha256`.
Writing skill: no-archaeology. No revision-history sentences were retained.
'''
 assert len(report.splitlines())<=50
 (OUT/'REPORT.md').write_text(report)
 (ROOT/'STATUS.md').write_text(f"The tower-frames section-8 CPU dry run is {dry['status']}, with {rows} exact box A0 row matches, all 450 camera items bound for parity, and {join['bound64']} bound for dense camera arms. The remaining dense manifests are named in out/BLOCKERS.json. All {tests['tests']} regression tests pass. The report, GPU request and SHA256-verified archive are delivered; no GPU or network work ran.\n")
 paths=[p for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md')]
 paths+=list((ROOT/'configs').glob('*.json'))
 paths+=[ROOT/'scripts'/n for n in (*DELIVERY_SCRIPTS,'bind_camera.py','finalize_v3.py')]
 paths+=[p for p in (ROOT/'inputs').rglob('*') if p.is_file() and p.name!='KIT_SPEC_tower_frames.md']
 paths+=[OUT/n for n in ('REPORT.md','DRYRUN.json','GPU_NEED.json','BLOCKERS.json','CAMERA_BINDING.json','CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch','TESTS.json','VALIDATION.json','dryrun_v3.log','tests_v3.log','bind_camera.log')]
 paths+=[ROOT/'work'/n for n in ('mutate.py','reviewer_mutate_original.py','a0_rerun.py','part_a_cpu.py','write_fix_report.py')]
 paths+=[p for p in (OUT/'fix_validation').rglob('*') if p.is_file()]
 paths+=[OUT/'FIX_REPORT.md']
 paths+=[T/n for n in ('A_POSE.json','A_DEPTH.json','A_SCALE.json','A_DISTANCE.txt','B_LADDER_TRAIN.txt','B_GAINS_ONCE.txt','HELDOUT_once.txt','C_PARITY.json','C_CAMERA.txt','DECISION.json','PASS_TIMING.json','AVAILABILITY.json','CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch')]+[ROOT/'STATUS.md']
 archive=OUT/'sb_ktfix3.tar'
 with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
  for p in sorted(set(paths)):
   if not p.is_file():continue
   info=tar.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with p.open('rb') as f:tar.addfile(info,f)
 h=sha(archive);(OUT/'sb_ktfix3.tar.sha256').write_text(h+'  out/sb_ktfix3.tar\n')
 with tarfile.open(archive) as tar:
  members=tar.getnames()
  for n in ('out/REPORT.md','out/DRYRUN.json','out/GPU_NEED.json'):assert n in members
 write_json(OUT/'PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(members),report_lines=len(report.splitlines()),code_sha256=digest(pins)))
 print(json.dumps(dict(dryrun=dry['status'],tests=tests['tests'],archive_sha256=h,archive_bytes=archive.stat().st_size,report_lines=len(report.splitlines()))))
if __name__=='__main__':main()
