import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
from common import *
import tarfile,hashlib,json
out=ROOT/'out';dry=read_json(out/'DRYRUN.json');tests=read_json(out/'TESTS.json');pins=read_json(out/'CODE_SHA256.json')
assert dry['code_sha256']==pins['code_sha256']==digest(code_pins())
assert tests['status']=='PASS'
# Availability record, not an invented scored item.
(out/'tower_frames/PER_ITEM.jsonl').write_text(json.dumps(dict(kind='availability',status='MISSING',reason='No GPU captures priced',input_sha256=dict(INPUTS)),sort_keys=True)+'\n')
paths=[ROOT/name for name in pins['files']]
paths += [ROOT/'inputs'/name for name in ('KIT_SPEC_tower_frames.md','HEAD_ACCURACY_DESIGN_20261119.md','pose_k1.py','SOURCES.json','CODE_SOURCES.json')]
paths += [out/name for name in ('CODE_SHA256.json','EDITED_LINES.json','EDITED_LINES.patch')]
archive=out/'sb_ktow.tar'
with tarfile.open(archive,'w',format=tarfile.PAX_FORMAT) as tar:
 for path in sorted(set(paths)):
  info=tar.gettarinfo(str(path),arcname=str(path.relative_to(ROOT)))
  info.uid=info.gid=0;info.uname=info.gname='';info.mtime=0
  with path.open('rb') as f:tar.addfile(info,f)
h=sha(archive);(out/'sb_ktow.tar.sha256').write_text(h+'  out/sb_ktow.tar\n')
with tarfile.open(archive) as tar:
 members=tar.getmembers();forbidden=[m.name for m in members if m.name.endswith(('.npz','.png','.pt','.safetensors','.jsonl')) or 'MANIFEST' in m.name or '__pycache__' in m.name]
 assert not forbidden
write_json(out/'PACKAGE.json',dict(status='PASS',archive='out/sb_ktow.tar',sha256=h,bytes=archive.stat().st_size,members=len(members),data_files=forbidden,code_sha256=pins['code_sha256']))
edits=read_json(out/'EDITED_LINES.json')['edits'];by={}
for e in edits:by.setdefault(e['file'],[]).extend(e['edited_lines'])
editlines=['- `'+p+'`: '+','.join(map(str,sorted(set(lines))))+'.' for p,lines in sorted(by.items())]
report=f'''The tower-frames kit is built for CPU review. GPU execution remains BLOCKED by missing inputs; GPU use was 0 hours.

Built: lane-owned tree and reader code; N=32/64 lifting, visibility and geometry; all-slot G3T depth; raw-name SAM 3 replay; A/B/C pricing, bars, seeds, per-capture receipts, and three GPU launchers. The language model retains 32 anchors. `code/README.md` defines input contracts and the single kbox winner hook.

CPU evidence (commands run with CUDA_VISIBLE_DEVICES empty):
- `bash scripts/cpu.sh code/dryrun.py > out/dryrun.log 2>&1` produced `out/DRYRUN.json`.
- A: five stored K1 captures; pose, depth, A0 and A2 self-comparison differences are all exactly 0. Each distance arm covers 10 rows. Rebuilt own-scale geometry equals the cached geometry arrays exactly.
- B support: N=32 lifting equals the original tree on all five captures; N=64 visits 64 slots. Required kbox A0 row parity is MISSING: `/scratch/jjyeung/orch_n30/sb_kbox/out/box_ladder/PER_ITEM.jsonl` contains no A0 rows at this read.
- C: synthetic reader move/turn formatting PASS. Real 440/450 parity is MISSING: `/scratch/jjyeung/orch_n30/swarm_an/kit/san_kit.py` is absent on this node. No capture-to-export mapping was inferred.
- The dry run took {dry['seconds']:.3f} seconds; peak CPU RSS was {dry['peak_cpu_kib']} KiB. Its aggregate status is BLOCKER.
- `bash scripts/cpu.sh code/test_kit.py > out/tests.log 2>&1`: {tests['tests']} tests PASS, including raw-name alias filtering, 64-frame geometry, anchor-only output, bootstrap bars, scale bridging, and corrupt-output rejection.
- `bash -n scripts/cpu.sh scripts/gpu_environment.sh scripts/run_A.sh scripts/run_B.sh scripts/run_C.sh` passed; all delivered Python files parse with `ast.parse`.

Future GPU commands, from `/scratch/jjyeung/orch_n30/sb_ktow` (not executed):
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_A.sh` — expected 0.5 GPU-hours; 1-hour part cap.
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_B.sh` — expected 2.5 GPU-hours; 4-hour part cap; requires an A bar PASS.
- `CUDA_VISIBLE_DEVICES="${{CARD:?assigned GPU required}}" bash scripts/run_C.sh` — expected 0.6 GPU-hours; 1-hour part cap; DA3 remains enabled after an A stop.
- Every launcher wraps `/data3/shared/scripts/vnice/vnice.sh`; the shared deadline is six hours from first GPU start. Asset reads resolve under `/scratch`; writes stay in this workspace. Valid DONE output hashes skip completed captures; partial attempts and HALTED runs block automatic retry.
- Memory: the specification budgets one 48-GB card; actual 64-frame G3T peak is MISSING. `code/dryrun.py` searched `RUN2.log`, `RUN2b.log`, and `run_tower_sam_2/worker.log` under `/scratch/jjyeung/k1`; none contains a peak-memory measurement. No card was chosen. Launch requires a verified log measurement and a separate GPU GO.

Every edited line in the lane copy (new line numbers; original lines and exact text are in `out/EDITED_LINES.json` and `.patch`):
{chr(10).join(editlines)}

Statistics: pose uses 5,000 paired capture draws; distance/camera use 10,000 paired room draws with item weighting; seed 20261119 throughout. A implements pose/short-displacement and lifting bars; B requires positive train lower bound and held-out point; C requires +3 displacement points, positive lower bound, and no rotation/direction loss over 1 point. Missing results never pass. B held-out output permits one completed look after code review.

Outputs: `out/tower_frames/` contains every required output name, availability records, bar decisions and timing receipts. Unrun prices say MISSING. `out/INPUT_AUDIT.json` lists four missing GT paths: the supplied manifest has 300 captures and 296 GT rasters. The GPU roster is restricted to those 296 existing GT captures.

Deviations and unresolved inputs:
- The named tree path is absent; the kit uses the local `b04host3/tree_rebuild/work/base/tree_b01ce449` mirror and `b04host3/b04_e2ehook/e2e_reader`. Byte equality to the remote R1 copy is unverified. The named preflight has no runtime/weight binding; manifest and capture receipts supply the local bindings.
- Part B cannot claim section 6b PASS until kbox supplies its reference A0 rows. Its winning gather/fusion rule binds through `configs/KBOX_WINNING_BOX_RULE.json` only after a pinned PASS decision.
- Part C needs an authoritative local export of the routed items, poses, scale, gravity, truths and frame joins. The sampled `g3s32/export` NPZ is a mask export, not a pose export. The synthetic check does not satisfy real parity.
- Full 64-frame selector labels are MISSING because GT has 32 anchors. The diagnostic code reports top-1 on the same 32 labelled anchors at both N values and states that scope.
- Dense boxes use dense points; printed lists contain only real shared anchors. Printed best is the largest shared anchor; an object with none refuses. Depth AbsRel samples the GT raster at the 51x51 endpoint grid with nearest pixels.
- Room-bootstrap draw count comes from the box-ladder specification. GPU forward passes, timing estimates and memory have not been validated on hardware. Staged weight hashes are verified by the future runner before loading.
- The archive was not mirrored: the task forbids network and SSH. No GPU, network, Git, tmux or process-control action was run.

Archive: `out/sb_ktow.tar` contains code, configs, scripts, specs and review receipts; no data, weights or tensor caches. `scripts/package_delivery.py` created it and checked {len(members)} members. Verify with `sha256sum -c out/sb_ktow.tar.sha256`.
SHA-256: `{h}`.
Code identity: `{pins['code_sha256']}` (`out/CODE_SHA256.json`).
Writing skills: no-archaeology and summary; no borderline history sentences were retained.
'''
assert len(report.splitlines())<=80,len(report.splitlines())
(out/'REPORT.md').write_text(report)
(ROOT/'STATUS.md').write_text('Stage 4: The CPU review kit is packaged in out/sb_ktow.tar with SHA-256 '+h+'. All ten regression tests pass, and five-capture pose/depth/conversion/A0/A2 self-comparisons have zero differences. The aggregate dry run remains BLOCKER because kbox A0 references are absent; real camera parity and measured K1 peak GPU memory are also MISSING. The report lists all edited lines, launch commands, limits and deviations. No GPU or network work ran.\n')
print(json.dumps(dict(archive_sha256=h,archive_bytes=archive.stat().st_size,report_lines=len(report.splitlines()),dryrun=dry['status'],tests=tests['status']),indent=2))
