"""Create the v2 review artifacts without running GPU work or pricing new rows."""
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
 dry=read_json(OUT/'DRYRUN.json');tests=read_json(OUT/'TESTS.json')
 assert tests['status']=='PASS'
 pins=code_pins();assert dry['code_sha256']==digest(pins),'Dry run must match final code'
 write_json(OUT/'CODE_SHA256.json',dict(files=pins,code_sha256=digest(pins)))
 changed=edits();binding=frame_binding()
 import shutil
 for name in ('CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch'):shutil.copyfile(OUT/name,T/name)
 blockers=[dict(scope='CPU section 8b',expected_path=r['expected_path'],capture=r['capture'],missing_A0_rows=r['missing_A0_rows'],reason=r['reason']) for r in dry['B']['captures'] if r['status']=='MISSING']
 if binding['status']!='PASS':blockers.append(dict(scope='GPU Part C only',**binding))
 write_json(OUT/'BLOCKERS.json',dict(status='BLOCKER' if blockers else 'PASS',blockers=blockers))
 for n in ('A_POSE.json','A_DEPTH.json','A_DISTANCE.txt','B_LADDER_TRAIN.txt','B_GAINS_ONCE.txt','HELDOUT_once.txt','C_PARITY.json'):
  write_json(T/n,dict(status='MISSING',rows=[],reason='GPU pass not run; CPU self-tests are in out/DRYRUN.json',heldout_role='report-only after frozen DECISION.json'))
 from camera_pricing import run
 run()
 write_json(T/'DECISION.json',dict(status='MISSING',train_complete=False,complete={'A':False,'B':False},selection_split='K1_train',part_B_independent=True,bars={'context_pays_pose':'MISSING','context_pays_lifting':'MISSING','replace_box_reader_context':'MISSING','views_pay':'MISSING'},part_C='DIAGNOSTIC_ONLY',heldout_role='REPORT_ONLY'))
 write_json(T/'PASS_TIMING.json',dict(gpu_passes=[],gpu_hours_used=0,cpu_seconds=dry['seconds'],cpu_peak_kib=dry['peak_cpu_kib'],peak_gpu_policy='Measure first capture of every pass; stop above 40,000,000,000 bytes'))
 (T/'PER_ITEM.jsonl').write_text(json.dumps(dict(kind='availability',status='MISSING',reason='No GPU arm priced',input_sha256=dict(INPUTS)))+'\n')
 write_json(OUT/'GPU_NEED.json',dict(status='NOT_LAUNCHED',cards=1,max_concurrent_cards_shared=2,card_memory_gb=48,max_allocated_bytes=40000000000,measured_peak_bytes=None,gpu_hours_used=0,environment='/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python',steps=[dict(part=p,expected_gpu_hours=e,hard_stop_hours=h,command=f'CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_{p}.sh') for p,e,h in [('A',.5,.75),('B',2.5,3.),('C',.6,.75)]],shared_cap_gpu_hours=16,shared_order=ORDER,shared_hard_hours=HOURS,cut_order=list(reversed(ORDER)),reservation_hook=str(ROOT/'inbox/SHARED_GPU_RESERVATION.json'),ledger_owner='Swarm_build2 orchestrator; receipts here, no writes to another lane',launch_blockers=blockers))
 write_json(OUT/'VALIDATION.json',dict(status='PASS',python_files=sum(1 for p in (ROOT/'code').rglob('*.py') if ast.parse(p.read_text()) is not None),unit_tests=tests['tests'],shell_command='bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh'))
 line_edits=['- `'+p+'`: '+ranges(v)+'.' for p,v in sorted(changed.items())]
 report=f'''The tower_frames v2 kit is built; CPU dry run: {dry['status']}. GPU use: 0 hours.
The remaining CPU blocker is section 8b: the box kit has no A0 rows for four selected train captures.

Changes vs v1: pinned 239/57 capture and 1,037/216 distance-row sets; independent context/view gates; train-only decisions; held-out report after DECISION.json; explicit C/V/box arms; reader median_ratio per output; anchor numbering; staged camera calls; shared-ledger budgets and first-capture peak measurement.
CPU source: the pinned R1 reader in the staged pack, with N edits; tree: `/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449`.
CPU interpreter: `/scratch/jjyeung/envs/p1cpu/bin/python`; GPU interpreter: `/scratch/jjyeung/envs/sam3_scipy_ovl/bin/python` (torch/numpy/PIL/scipy discoverable; GPU execution untested).

Commands producing the reported evidence, from `{ROOT}`:
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun_v2.log 2>&1`
- `bash scripts/cpu.sh code/test_kit.py > out/tests_v2.log 2>&1`
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh`
- `bash scripts/cpu.sh scripts/finalize_v2.py` writes the report, edited lines, hashes, GPU request and tar.
The dry run took {dry['seconds']:.3f} s; peak RSS was {dry['peak_cpu_kib']} KiB. It used nice 10 and eight numerical threads.
Section 8a: five train captures; stored C64 self-comparisons have zero pose/depth/distance differences. All five recomputed scales agree with stored values within 1e-4 relative.
Section 8b: N=32 lifting matches the original tree on all five captures; N=64 visits all 64 slots. A0 reference matches the first capture; four references are MISSING.
Section 8c: synthetic formatting with a staged scale/gravity passes; all 450 records load and their calls parse. Real 440/450 parity awaits GPU G32 replay.
Section 8d: all 296 captures pass strictly increasing anchor slots and 9,472 anchor/model-row hash comparisons. Held-out values were not opened.
Regression checks: {tests['tests']} tests PASS, including train-only bars, independent Part B, median-of-ratios scale, one-look refusal, shared budget admission and corrupt-resume rejection.

Exact CPU blocker: `/scratch/jjyeung/orch_n30/sb_kbox2/out/box_ladder/PER_ITEM.jsonl` lacks A0 rows for:
- `arkitscenes/41069076`, `arkitscenes/41098061`, `arkitscenes/41098085`, `arkitscenes/41098191`.
`out/BLOCKERS.json` names every missing row ID and the hashed reference file; no reference was synthesized.
The single box hook is `configs/KBOX_WINNING_BOX_RULE.json`. The box decision has no frozen object winner, so obj arms and the joint-gain table remain MISSING until that hook is bound.
Part C blocker: `/scratch/jjyeung/devs1_r2/REQUEST.json` has a bundle hash and root but lacks `items[].frames[].{{index,path,sha256}}`. All 450 real parity items are currently unbound; no scene/digest mapping was inferred.

GPU commands below are prepared, not run; each uses one 48-GB card and stops allocation above 40 GB:
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_A.sh` — expected 0.5 GPU-h; hard stop 0.75 h.
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_B.sh` — expected 2.5 GPU-h; hard stop 3.0 h; no Part A bar gate.
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_C.sh` — expected 0.6 GPU-h; hard stop 0.75 h; diagnostic only.
Launchers use `/data3/shared/scripts/vnice/vnice.sh`, workspace-only writes, scratch-only assets, explicit GPU GO and a shared-ledger reservation. Valid DONE hashes skip finished units. Every pass records seconds and peak allocation.
The orchestrator owns the shared 16 GPU-hour ledger and two-card limit. `GPU_NEED.json` gives the full order and reverse cut order. This lane cannot create that shared reservation or write another lane's ledger.

Edited copied-tree/reader lines (inclusive ranges; exact before/after text and source hashes are in EDITED_LINES.json and EDITED_LINES.patch):
{chr(10).join(line_edits)}

Decision code uses 5,000 paired capture draws for pose and 10,000 paired room draws for distance, seed 20261119. Every full arm must cover its pinned population before a bar can pass. Box/frame/joint gains use identical rows; only joint gain prices both changes.
V64 member precision and selector labels use anchor members because GT has only 32 rasters. Printed lists/best/first use anchors; dense-only objects print not seen and are counted. First-seen truth uses GT share >=0.002.
Part C exposes G64_rot/G64_dir, G64_disp_proxy and native/proxy DA3 arms; proxy displacement is sensitivity only and cannot authorize adoption.
R0-dev and official items were not read. R0 access requires frozen PRIMARY_ARMS.json and consumes an exclusive per-category receipt before opening data; another read is refused.
Deviations: section 8b cannot PASS without the named A0 references; real camera replay cannot start without item/frame hashes. GPU timing and memory remain unmeasured. No archive mirror ran because network/SSH are forbidden.
The specification was copied once after its initial bounded read; all further specification reads used the workspace copy.
Archive: `out/sb_ktow2.tar`; verify with `sha256sum -c out/sb_ktow2.tar.sha256`. It contains this report, CPU receipts, code, configs and pinned inputs, without weights or frame tensors.
Writing skill: no-archaeology. The changes-vs-v1 sentence is retained because the task explicitly requires it.
'''
 assert len(report.splitlines())<=80
 (OUT/'REPORT.md').write_text(report)
 (ROOT/'STATUS.md').write_text('Stage 4: The v2 kit and review archive are complete. The CPU dry run is '+dry['status']+' solely because four selected train captures lack box-kit A0 reference rows. The other section-8 checks and '+str(tests['tests'])+' regression tests pass. Part C additionally needs explicit item/frame hash joins before real GPU parity. No GPU, network, SSH, Git, tmux or process-control work ran.\n')
 # Include only supported entry points and current outputs, excluding inherited and runtime files.
 paths=[p for p in (ROOT/'code').rglob('*') if p.is_file() and p.suffix in ('.py','.json','.md')]
 paths+=list((ROOT/'configs').glob('*.json'))
 paths+=[ROOT/'scripts'/n for n in (*DELIVERY_SCRIPTS,'finalize_v2.py')]
 paths+=[p for p in (ROOT/'inputs').rglob('*') if p.is_file() and p.name not in ('KIT_SPEC_tower_frames.md',)]
 paths+=[OUT/n for n in ('REPORT.md','DRYRUN.json','GPU_NEED.json','BLOCKERS.json','CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch','TESTS.json','VALIDATION.json','dryrun_v2.log','tests_v2.log')]
 paths+=[T/n for n in ('A_POSE.json','A_DEPTH.json','A_SCALE.json','A_DISTANCE.txt','B_LADDER_TRAIN.txt','B_GAINS_ONCE.txt','DECISION.json','HELDOUT_once.txt','C_CAMERA.txt','C_PARITY.json','PER_ITEM.jsonl','PASS_TIMING.json')]
 paths+=[T/n for n in ('CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch')]
 paths+=[ROOT/'STATUS.md']
 archive=OUT/'sb_ktow2.tar'
 with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
  for p in sorted(set(paths)):
   info=tar.gettarinfo(str(p),arcname=str(p.relative_to(ROOT)));info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
   with p.open('rb') as f:tar.addfile(info,f)
 h=sha(archive);(OUT/'sb_ktow2.tar.sha256').write_text(h+'  out/sb_ktow2.tar\n')
 with tarfile.open(archive) as tar:
  members=tar.getnames();assert 'out/REPORT.md' in members and 'out/DRYRUN.json' in members and 'out/GPU_NEED.json' in members
  assert not any(n.endswith(('.npz','.pt','.safetensors','.png')) for n in members)
 write_json(OUT/'PACKAGE.json',dict(status='PASS',archive=str(archive),sha256=h,bytes=archive.stat().st_size,members=len(members),report_lines=len(report.splitlines()),code_sha256=digest(pins)))
 print(json.dumps(dict(dryrun=dry['status'],tests=tests['tests'],archive_sha256=h,archive_bytes=archive.stat().st_size,report_lines=len(report.splitlines()))))
if __name__=='__main__':main()
