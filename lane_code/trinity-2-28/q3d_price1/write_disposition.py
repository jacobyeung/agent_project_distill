import datetime
import hashlib
import json
from pathlib import Path

W = Path('/scratch/jjyeung/orch_n30/q3d_price1')
D = Path('/data2/jjyeung/agent_project_data/distill_design')
commit = 'bf91573212c3538fc314d2add05519d7e9fd6b7e'
now = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
entries = []
for metadata, repo, name in [
    ('qwen3d_files.json', 'katefgroup/Qwen-3D', 'qwen3d_3b.pth'),
    ('backbone_files.json', 'Qwen/Qwen2.5-VL-3B-Instruct', 'model-00001-of-00002.safetensors'),
    ('backbone_files.json', 'Qwen/Qwen2.5-VL-3B-Instruct', 'model-00002-of-00002.safetensors'),
    ('g3t_files.json', 'thatbrguy/g3t', 'model.safetensors'),
]:
    item = next(x for x in json.loads((W/'evidence'/metadata).read_text()) if x['path'] == name)
    entries.append(dict(repository=repo, file=name, bytes=item['size'], advertised_sha256=item['lfs']['oid'],
                        source='https://huggingface.co/{}/resolve/main/{}'.format(repo, name), downloaded=False))
total = sum(x['bytes'] for x in entries)
inventory = dict(timestamp_utc=now, code_commit=commit, weights=entries, stock_weights_bytes=total,
                 budget_bytes=20000000000, over_budget_bytes=total-20000000000,
                 weights_gib=total/2**30, remaining_if_budget_meant_20_gib=20*2**30-total,
                 kit_ready=False, governor_registration_attempted=False, cpu_dry_run_reached='not run',
                 note='Advertised LFS hashes are metadata, not local file verification. The budget conclusion concerns the stock loader with local G3T, not every possible loading implementation.')
(W/'evidence'/'INPUT_BUDGET.json').write_text(json.dumps(inventory, indent=2)+'\n')

p = D/'QWEN3D_PREDICTED_GEOMETRY_PRICING_20261120.md'
old = p.read_text()
(W/'evidence'/'PREREGISTRATION_INPUT.md').write_text(old)
registered = old.split('## Registered reading\n',1)[1].split('\n## Confounds',1)[0]
new = old.replace(old.splitlines()[2], 'Status: BLOCKED by the stock model footprint under the 20 GB workspace limit. The public code is cloned and inspected; the environment, executable kit and CPU dry run are not built. No accuracy measurement exists. The registered comparison below remains unchanged.', 1)
start = new.index('## Blocking evidence\n')
end = new.index('## Arms and parity\n')
new = new[:start] + '''## Blocking evidence

The stock Qwen-3D loader downloads a Qwen2.5-VL backbone with `from_pretrained` before loading the Qwen-3D checkpoint (`src/qwen3d/model.py:143`). The advertised file sizes below total **21,030,841,260 bytes (21.031 GB; 19.586 GiB)** with one G3T weight format. This exceeds a decimal 20 GB budget by 1,030,841,260 bytes, before Python, dependencies, tokenizers, a metric-depth fallback, or data. If the intended unit is 20 GiB, these weights leave only 443,995,220 bytes; no complete environment has been demonstrated within that remainder.

| Required stock weight file | Advertised bytes | Public source |
| --- | ---: | --- |
| qwen3d_3b.pth | 7,894,337,084 | [katefgroup/Qwen-3D](https://huggingface.co/katefgroup/Qwen-3D/tree/main) |
| Backbone shard 1 | 3,982,649,232 | [Qwen/Qwen2.5-VL-3B-Instruct](https://huggingface.co/Qwen/Qwen2.5-VL-3B-Instruct/tree/main) |
| Backbone shard 2 | 3,526,688,744 | Same backbone repository |
| G3T model.safetensors | 5,627,166,200 | [thatbrguy/g3t](https://huggingface.co/thatbrguy/g3t/tree/main) |

Only one G3T format is counted. Its alternative `model.pt` is 5,627,541,266 bytes. API responses and advertised LFS SHA256 values are saved in `W/evidence/`; no weight file was downloaded or locally hashed. `W` means `/scratch/jjyeung/orch_n30/q3d_price1`.

No governor refusal is claimed. The session can write registrations and the existing `iogov_agent` tmux session is present. The operations record explains that an idle node can show “silent” until registration. No stream was registered because the footprint check stopped large staging first. No failed or killed transfer was retried.

The budget finding applies to the stock loader plus local G3T. A validated loader that initializes from the Qwen-3D checkpoint without separately storing the backbone, or existing exports for the exact selected RGB frames, could reduce the requirement. Neither is established here; this record does not claim that every possible implementation is impossible under 20 GB.

''' + new[end:]
new = new.replace('The README describes MAX_FRAME_NUM=-1 as all frames; the evaluation configuration still needs inspection.', 'The README describes MAX_FRAME_NUM=-1 as all frames, but this pinned configuration defaults to MAX_FRAME_NUM=450 (`config.py:192`), with no override in the inherited evaluation YAML files. The default-frame A comparator must retain 450; an all-frame run would be a separate comparator. Evaluation uses rounded linspace sampling across the trajectory when the cap applies (`dataset_mapper_scannet.py:424`).')
start = new.index('## Input inventory and execution status\n')
new = new[:start] + '''## Input inventory and execution status

The public repository is [ll220/qwen3d](https://github.com/ll220/qwen3d), cloned once with `--depth 1` into `W/src`. The commit is **bf91573212c3538fc314d2add05519d7e9fd6b7e**, read from the clone's packed refs without another Git command. README, `docs/DATA.md`, `docs/RUN.md`, mapper, model, config, backprojection and evaluator paths were inspected.

| Input or deliverable | Verified status |
| --- | --- |
| Code and ScanNet split lists | Present under W/src; code and metadata footprint about 8.4 MB before this report |
| Qwen-3D, backbone and G3T weights | Public; exact advertised sizes above; all absent from W |
| ScanRefer annotations | Required ScanEnts3D variant: `ScanRefer_filtered_val_ScanEnts3D.json`, converted by `data_preparation/refexp/make_splits.py` to `ScanRefer_filtered_val_ScanEnts3D_val.csv`; [source zip](https://scanents3d.github.io/ScanEnts3D_ScanRefer.zip); bytes not measured, not staged |
| Posed ScanNet frames | Colour, millimetre depth PNGs, per-frame c2w poses and calibrated intrinsics; default also uses inpainted depth and per-frame dataset metadata. [Preparation source](https://github.com/ayushjain1144/odin/blob/main/data_preparation/scannet/README.md); subset bytes unknown, no fetch authorized |
| ScanNet mesh and labels | Mask3D processed scene arrays plus train_validation_database.yaml, mesh coordinates, superpoints and semantic/instance labels; required by default mapper and evaluator. Missing in W; size unknown |
| Other ScanNet metadata | docs/DATA.md names [katefgroup/UniVLG scannet assets](https://huggingface.co/katefgroup/UniVLG/tree/main/scannet); required preprocessing inventory remains incomplete; size unknown |
| Existing cluster inputs | Named records locate frames64 on trinity-3-30 and geometry kit/exports on trinity-1-18. Those are remote node-local paths, not verified on this node. Named logical roots /data2/k7pd and /data2/k8pd do not exist here. No broad cluster search occurred |
| Metric scale donor | Step-544 donor with frozen G3T FoV (V2) is the recorded rule; the referenced donor outputs are on trinity-1-18 and do not establish a new-scene inference path here |
| Metric-depth fallback | Permitted by brief; no weights, revision or preprocessing pinned before the footprint stop |
| Scene/frame manifests | Not built; bundled ScanNet validation IDs alone do not establish ScanRefer query coverage or available matching frames |
| Environment, adapter, alignment, bootstrap, run_read.sh | Not built; W/kit is empty |
| Tests and CPU dry run | Not run: no real-scene round trip, tokenization, voxel pooling, arm-A/arm-B forward or known-transform test |
| GPU price and run command | Unpriced; no verified runnable command. Do not submit a GPU read from this directory |

Named-record inventory: `POSE_DATA_SOURCES_20261108.md`, `GEOMETRY_BACKEND_BAKEOFF_20261111.md`, `COMPONENT_EVIDENCE_SOURCES_OFF_AWS_20261119.md`, and `TOWER_ARM_SCALE_DRIFT_20261119.md`. Their inspected contents and the INDEX matches are saved under `W/evidence`. The pose-source record describes sparse depth samples (64 points per anchor), not dense sensor depth suitable for the requested parity test. The geometry record confirms 64-frame export machinery; it does not verify exports for this ScanRefer subset. Remote artifacts were not accessed by SSH.

## Geometry leakage in the repository defaults

A depth-and-pose-only swap does **not** make this repository's default path RGB-only. `USE_GHOST_POINTS=True` and `USE_SEGMENTS=True` are defaults (`config.py:169,193`). The mapper loads mesh coordinates, colours, superpoints and labels from processed ScanNet arrays (`dataset_mapper_scannet.py:824–867`). The model interpolates contextualized features onto those mesh points before mask decoding (`model.py:1365–1387`). Thus dataset geometry enters the forward, rather than serving only as a scoring reference.

The evaluator also constructs both predicted and target boxes from `scannet_coords` (`referrential_grounding_evaluator.py:379–426`). Simply replacing that array would change the target geometry as well. A valid adapter must keep predicted point support separate from the unchanged scoring mesh, transform predicted masked points into the dataset frame after the forward, then reuse the repository's box construction and IoU convention (strictly greater than 0.25/0.5). Dataset poses and axis alignment must not leak into B's forward through mapper preprocessing.

Preserving the 5 cm voxel size, pooling algorithm and token limits does not require retaining sensor-mesh support in B. However, replacing sensor mesh/superpoints with RGB-derived support adds a decoder-support change that must be disclosed and tested. Turning ghost points off blindly is not a validated substitute. Gate 0 must first establish the default A path; an RGB-only support path then needs explicit verification that no dataset geometry reaches the forward. C1 and C2 attribution may otherwise include this additional support change.

## Options rejected and failure checks

- Staging the stock weight set exceeds the decimal 20 GB cap. No large transfer was started. Sequential downloads cannot remove their accumulated footprint under the no-deletion rule.
- Quantization changes the evaluated model and has no Gate-0 evidence here. It is not silently substituted to meet the budget.
- Initializing the backbone from configuration and loading all weights from qwen3d_3b.pth could avoid duplicate storage, but checkpoint key coverage and exact output equivalence are unverified. This remains a possible implementation, not an established solution.
- Reusing an existing G3T export requires identical RGB frame IDs, preprocessing, intrinsics, coordinate conventions and scale provenance. A generic 32-anchor or benchmark export cannot establish that parity.
- Keeping ScanNet mesh points or superpoints in B's model input violates the RGB-only interpretation. Replacing the evaluator's target mesh with predicted geometry would invalidate scoring.
- Dataset-derived primary scale, similarity alignment and unequal frame lists remain rejected. Camera-centre alignment must report residuals and reject an underdetermined fit.
- Synthetic geometry tests cannot stand in for the requested real-scene round trip to 1e-4. No such test is claimed.

## Disposition

Post a BLOCKER for the stock weight footprint, with the geometry-support issue beside it. The kit is not ready. Before a resumed build stages weights, it needs a demonstrated path within the storage limit, real sensor frames for the dry run, and a way to separate RGB-derived decoder support from dataset-only scoring geometry. No GPU-minutes estimate is defensible without the scene/query inventory and a timed pilot; the future estimate must count four matched-frame arms, default-frame A, oracle-scale variants and geometry inference separately.

`/scratch` had 2.9 TB free before and after inspection, above the 150 GB stop threshold. No GPU, Slurm/Orchard job, SSH, deletion, environment installation, or transfer above 20 MB ran. No stream or other agent's work was stopped. The existing INDEX entry is retained without a second line, as instructed. This blocked directory has no sealed runnable tar or mirror; the brief forbids SSH.

Writing audit: the preregistered decision rules are preserved verbatim. The operations facts remain only where they establish current authorization and prevent a false governor-blocked claim.
'''
assert registered == new.split('## Registered reading\n',1)[1].split('\n## Confounds',1)[0]
p.write_text(new)
status = '''# q3d_price1 status
Updated UTC: {now}
Status: BLOCKED; kit is not ready; no experiment exists.
Code: W/src, commit {commit}; one shallow clone completed.
Stock Qwen-3D + required backbone + local G3T: {total} bytes, exceeding decimal 20 GB before environment/data.
Evidence: W/evidence/INPUT_BUDGET.json and the three public model file listings, including advertised LFS hashes.
Protocol issue: default decoder consumes ScanNet mesh points/superpoints; depth/pose-only replacement leaves sensor geometry in B.
Environment, adapter, manifests, tests, CPU dry run, bootstrap and run_read.sh: not built; W/kit is empty.
No large downloads or governor registration attempted; no governor refusal claimed; existing node agent is present.
No GPU, jobs, SSH, deletion or stops of other agents. /scratch has 2.9 TB free.
Record: /data2/jjyeung/agent_project_data/distill_design/QWEN3D_PREDICTED_GEOMETRY_PRICING_20261120.md; registered rules preserved, no second INDEX line.
Resume: establish storage-compliant loading and exact-frame inputs, then build RGB-only decoder support with scoring geometry isolated. GPU read still needs review and GO.
W = /scratch/jjyeung/orch_n30/q3d_price1
'''.format(now=now,commit=commit,total=total)
(W/'STATUS.md').write_text(status)
E=Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/q3d_price')
(E/'STATUS.md').write_text(status)
print(json.dumps(dict(record=str(p), registered_rules_sha256=hashlib.sha256(registered.encode()).hexdigest(),weights_bytes=total),indent=2))
