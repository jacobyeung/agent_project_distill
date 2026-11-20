from pathlib import Path
import json
import subprocess

W = Path('/scratch/jjyeung/orch_n30/q3d_price1')
D = Path('/data2/jjyeung/agent_project_data/distill_design')
E = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/q3d_price')
stamp = subprocess.check_output(['date', '-u', '+%Y%m%dT%H%MZ'], universal_newlines=True).strip()
record_name = 'QWEN3D_PREDICTED_GEOMETRY_PRICING_20261120.md'
event_name = f'{stamp}_BLOCKER_q3d_price1_governor_unavailable.md'
evidence = {
    'stamp_utc': stamp,
    'host': 'trinity-2-28',
    'governor_state_updated': '2026-11-20T02:34:32+00:00',
    'governor_node_state': 'trinity-2-28 silent',
    'tmux_iogov_agent': 'present; python3; pane PID 127712; pane_dead=0',
    'governor_registration_attempted': False,
    'reason': 'Governor streams directory is outside the session writable roots; no live node agent according to STATE.md.',
    'checkpoint_url': 'https://huggingface.co/katefgroup/Qwen-3D/blob/main/qwen3d_3b.pth',
    'checkpoint_display_size': '7.89 GB; exact bytes and SHA256 not fetched',
    'repository_url': 'https://github.com/ll220/qwen3d',
    'repository_commit': None,
    'dry_run': 'not started',
    'scratch_free_before_and_after': '2.9T',
    'gpu_minutes_used': 0,
}
(W / 'BLOCKER_EVIDENCE.json').write_text(json.dumps(evidence, indent=2) + '\n')
record = '''# Qwen-3D grounding with predicted geometry

Status: BLOCKED before clone, environment installation, or experiment. No accuracy measurement exists. The kit is not ready. This record registers the intended comparison before any run.

The question is how much ScanRefer grounding accuracy Qwen-3D-3B loses when G3T predicts geometry from the same RGB frames instead of using sensor depth and dataset poses. That difference decides whether its decoder merits a grounding-head experiment for our RGB-only model.

## Blocking evidence

At the governor snapshot updated 2026-11-20T02:34:32Z, `STATE.md` lists `trinity-2-28 silent`. The `iogov_agent` tmux session exists (python3, pane PID 127712, pane_dead=0), so a second agent must not be started. Session presence does not establish governor liveness. Its log tail ends at 2026-11-19T18:31:10Z; the cause of silence is unverified.

The governor requires a live node agent and a registered, stopped, ratelimit-paced pipeline before payload transfer. `register.py` writes an atomic stream record under the configured shared streams directory. `/data3/jjyeung/orch_n13_20261026/io_governor/streams` is outside this session's writable roots. Approval escalation is disabled. Registration was not attempted; this is an unavailable prerequisite, not a claimed governor rejection. No download pipeline was started. The build brief explicitly requires stopping and posting a BLOCKER when registration is unavailable.

The public [repository](https://github.com/ll220/qwen3d) and [3B checkpoint](https://huggingface.co/katefgroup/Qwen-3D/tree/main) exist. The checkpoint listing reports 7.89 GB, which exceeds the 20 MB registration threshold. The checkpoint is not proven to exceed the 20 GB workspace budget. Missing admission, rather than model availability or capacity, blocks this build.

## Arms and parity

| Arm | Depth input | Camera input |
| --- | --- | --- |
| A | Sensor depth | Dataset poses |
| B | G3T depth multiplied by deployable metric scale | G3T poses, with translations multiplied by the same scale |
| C1 | G3T depth multiplied by that scale | Dataset poses |
| C2 | Sensor depth | G3T poses, with translations multiplied by that scale |

Use the repository's ScanRefer validation evaluator and its 3B checkpoint. Report Acc@0.25 and Acc@0.5. Freeze 100 validation scenes with all their queries, using seed 20261120, before inference. The explicit scene list remains unwritten because annotations and the repository were not staged. Freeze identical frame IDs for all four arms, targeting 64 frames subject to verification of G3T's supported count. Report A again at the repository's default frame setting. The README describes MAX_FRAME_NUM=-1 as all frames; the evaluation configuration still needs inspection. Preserve the repository's voxel size, pooling, and token limits.

## Scale and coordinates

The named record [TOWER_ARM_SCALE_DRIFT_20261119.md](TOWER_ARM_SCALE_DRIFT_20261119.md) specifies OwnDepthScale: median(donor metric depth / G3T depth) on the 32x51x51 grid, above the clip's median G3T confidence and with donor depths in 0.1–10 m. Apply the factor once to both G3T depth and camera translations. The bound donor is step 544, conditioned on frozen G3T intrinsics (V2). The record names donor grids on trinity-1-18; these grids do not demonstrate inference availability for new ScanRefer scenes on this node.

The donor inference path has not been reproduced locally. The brief therefore permits a fallback median ratio of a monocular metric-depth model to G3T depth, using RGB only. That fallback is planned but no model, revision, preprocessing, or valid-pixel mask is pinned. It must be pinned before inference; do not label it OwnDepthScale or claim scale readiness.

Report an oracle per-scene scale separately. A proposed explicit definition is the median valid sensor-depth/G3T-depth ratio on corresponding pixels of the fixed frames. It is a diagnostic and must never enter the primary scale path.

Put predicted geometry in G3T's gravity-aligned z-up frame without dataset-pose input to B. For scoring B and C2, fit a proper rigid transform from scaled predicted camera centres to matching dataset camera centres: rotation and translation only, no scale. Apply it to predicted geometry before constructing dataset-frame axis-aligned boxes; rotating only box centres is insufficient. C1 uses dataset poses as an intentional model input. Record alignment residuals and reject underdetermined camera-centre fits rather than silently fitting scale. Dataset poses used to align B for scoring never enter its model inputs.

## Registered reading

1. Gate 0: A must agree with the paper's 62.2 Acc@0.25 within three percentage points, allowing subset noise through its interval. Operationally, stop for environment mismatch if A's 95% scene-bootstrap interval does not intersect [59.2, 65.2]. Report the point estimate and interval even if broad. Keep the default-frame A result beside the matched-frame A result.
2. Compute B minus matched-frame A using a paired scene bootstrap with 10,000 draws, seed 20261120, and 95% percentile intervals. Resample the same scene IDs in every arm and retain every query in each sampled scene; aggregate query successes over query counts. Do not resample queries independently or silently drop failed scenes.
3. A difference at Acc@0.25 of -5 points or better means “predicted geometry suffices; the decoder recipe is a grounding-head candidate.” A difference of -15 points or worse means “needs sensor geometry; closed.” Between those thresholds, C1 and C2 identify the depth and pose contributions. Report uncertainty beside the point-estimate classification.

## Confounds required beside any result

- ScanRefer validation scenes overlap our benchmark scenes. This is a diagnostic only; no output becomes a training row or initialization.
- The checkpoint trained on sensor geometry. Its drop is intended as a pessimistic bound on loss after training with predicted geometry, not a measured or guaranteed bound for such training.
- The deployable scale rule is ours, not the paper's. An oracle scale column is not RGB-only.
- C1 and C2 can reveal interacting depth and pose errors; their changes need not sum to B minus A.

## Input inventory and execution status

| Input or deliverable | Verified status |
| --- | --- |
| Public Qwen-3D repository | README inspected online; not cloned; commit not recorded |
| qwen3d_3b.pth | Public listing: 7.89 GB; not downloaded; exact bytes/hash unverified |
| Qwen2.5-VL-3B-Instruct backbone | README identifies it; required local files and total size unverified |
| ScanRefer validation annotations | Not staged or inventoried; exact source and size need docs/DATA.md inspection |
| ScanNet colour, depth, intrinsics, poses and scoring assets | Not staged; scene coverage, source paths and sizes unverified; no frame download authorized tonight |
| G3T checkpoint/exports and metric donor | Scale rule located in the named record; usable local artifacts unverified |
| Environment, adapter, lists, alignment, bootstrap, run_read.sh | Not built because the registration prerequisite blocks the build |
| CPU dry run and adapter tests | Not run; no tokenisation, pooling, forward pass, or scene round trip reached |
| GPU-minutes estimate | Not supportable before evaluator inspection and a timed pilot; no invented number |

Read-only discovery covered the specified INDEX search, the scale record it names, the lane/admin rules, the governor instructions and state, and public project/repository/model pages. The inventory is incomplete; no broad filesystem scan was performed. `/scratch` had 2.9T available before and after discovery. No GPU, job submission, SSH, Git operation, deletion, or large transfer occurred.

## Options rejected and failure checks

- Unregistered curl/pip, an alternate transfer path, or a second node agent would bypass required IO controls; reject them.
- A generic geometry scaffold cannot establish parity with an uninspected evaluator; do not report it as a ready kit.
- Dataset-derived primary scale, similarity alignment, and unequal frame lists would confound the comparison; reject them.
- A tiny-frame synthetic test cannot replace the requested scene round trip. Completion requires sensor unprojection parity to 1e-4, identical arm frame lists, and recovery of a known rigid transform.
- Evaluation may require mesh points, labels, or GPU-only operators in addition to posed frames. Inspect the pinned evaluation path and account for their sizes before staging.
- The combined backbone, checkpoint, G3T, metric model and environment may exceed 20 GB. Verify exact sizes before admission and stop if the budget cannot be met.

Resume requires governor admission to be available within an authorized write scope and this node to be live in STATE.md. Then perform the one shallow clone, pin its commit, complete the named-record inventory, build and test the adapter, and run the CPU dry path. Independent review and an orchestrator GO remain necessary before the GPU read. No executable GPU command or kit tar is available in this blocked build.

Writing audit: no project-history sentence was retained. Operational paths and internal scale details are included because this is the requested internal build record.
'''
with (D / record_name).open('x') as f:
    f.write(record)
with (D / 'INDEX.md').open('a') as f:
    f.write(f'\n- [{record_name}]({record_name}): Qwen-3D sensor-versus-G3T grounding diagnostic; arms and decision bars registered; BLOCKED before build because trinity-2-28 is silent in the IO governor and its registration directory is outside the session writable roots. No run or accuracy result.\n')
status = f'''# q3d_price1 status
BLOCKED {stamp}: governor admission unavailable; no kit ready.
Host: trinity-2-28. Governor snapshot 02:34:32Z lists this node silent; iogov_agent session exists.
Registration requires writes outside the session writable roots; not attempted. No transfer started.
Public 3B checkpoint listing: 7.89 GB. Code public; clone/commit pending.
Record: {D / record_name}
Evidence: {W / 'BLOCKER_EVIDENCE.json'}
Environment, code, tests, scene/frame lists, dry run and tar: absent. GPU minutes used: 0.
No GPU command is ready. No agent, service or job was stopped. Nothing requires deletion.
Resume only with writable governor registration and live node admission, then complete the original build brief.
'''
(W / 'STATUS.md').write_text(status)
(E / 'STATUS.md').write_text(status)
event = f'''# BLOCKER: q3d_price1 governor registration unavailable
UTC: {stamp}; host: trinity-2-28.
Governor STATE.md updated 2026-11-20T02:34:32Z lists trinity-2-28 silent.
iogov_agent exists (python3, pane PID 127712); no second agent started.
register.py must write shared streams records outside this session's writable roots; escalation is disabled.
Registration was not attempted; no governor rejection or successful admission is claimed.
Public code: https://github.com/ll220/qwen3d ; no clone/commit yet.
Public checkpoint: https://huggingface.co/katefgroup/Qwen-3D/tree/main ; qwen3d_3b.pth listed as 7.89 GB.
The checkpoint exceeds 20 MB and cannot move before admission. No large download started.
Evidence: {W / 'BLOCKER_EVIDENCE.json'}
Preregistration and incomplete inventory: {D / record_name}
INDEX.md received one line. Environment, adapter, tests, scene/frame lists and dry run were not built/run.
No kit tar/SHA256 or executable GPU command exists; GPU estimate unpriced, GPU use zero.
Scratch free before/after: 2.9T; only small local evidence/report files written.
Resume condition: authorized registration access and a live node agent, then complete and independently review the CPU kit.
'''
assert len(event.splitlines()) <= 20
with (E / event_name).open('x') as f:
    f.write(event)
print(E / event_name)
print(D / record_name)
