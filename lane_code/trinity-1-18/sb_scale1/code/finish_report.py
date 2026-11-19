"""Render the frozen results and document missing forward-pass inputs."""
import sys
sys.dont_write_bytecode=True
import json
import tarfile
from pathlib import Path
from collections import defaultdict
import numpy as np
import scale_analysis as s

out=s.OUT
result=s.read(out/'SCALE_RESULT.json')
bars=s.read(out/'BARS_FROZEN.json')
cs=s.training()
progress=Path('/scratch/jjyeung/k1/own_170235/native/probe/PROGRESS.jsonl')
pins={str(p):s.sha(p) for p in [Path(__file__),Path(s.__file__),s.MANIFEST,s.ART400,s.ART544,s.BOUNDARY,progress,out/'SCALE_RESULT.json',out/'BARS_FROZEN.json',out/'resources.log',out/'tests.log']}
train_ids={c['canonical'] for c in cs}
train_keys={s.digest(c['canonical'])[:16] for c in cs}
archives=[]
for archive in [Path('/scratch/jjyeung/orch_n30/k1_ops3/work/own7/ad2472b1be07d4193.result.tar.gz'),
                Path('/scratch/jjyeung/orch_n30/k1_ops3/work/own7/canary/c75955208369b4e48.result.tar.gz')]:
    pins[str(archive)]=s.sha(archive)
    receipts=[]
    with tarfile.open(archive,'r:gz') as stream:
        for member in stream:
            parts=Path(member.name).parts
            if len(parts)<2 or parts[-1]!='PHASE_COMPLETE.json' or parts[-2] not in train_keys:
                continue
            data=stream.extractfile(member).read()
            rec=json.loads(data)
            assert rec['checkpoint']['sha256']==s.sha(s.ART544)
            receipts.append(dict(member=member.name,sha256=s.hashlib.sha256(data).hexdigest(),checkpoint_step=544,
                                 checkpoint=rec['checkpoint'],files=rec['files']))
    archives.append(dict(path=str(archive),sha256=pins[str(archive)],training_receipts=receipts))
events=defaultdict(dict)
for line in progress.read_text().splitlines():
    # Read timing metadata for train captures only, never predictions or scores.
    if not any(('"canonical": "'+c+'"') in line for c in train_ids):
        continue
    r=json.loads(line)
    if r.get('event') in ('capture_start','capture_commit'):
        events[r['canonical']][r['event']]=r['unix']
durations={c:e['capture_commit']-e['capture_start'] for c,e in events.items() if {'capture_start','capture_commit'}<=set(e)}
assert all(v>0 for v in durations.values())
d=np.array(list(durations.values()))
timing=dict(source=str(progress),source_sha256=pins[str(progress)],training_captures=len(d),
            median_seconds=float(np.median(d)),mean_seconds=float(np.mean(d)),
            p10_p90_seconds=np.quantile(d,[.1,.9]).tolist(),
            estimated_gpu_hours_242_at_mean=float(d.mean()*len(cs)/3600),
            estimate_basis='Historical step544 own-phase GPU capture_start to capture_commit, train captures only; extrapolation to step400, excludes staging and setup; original GPU model not verified.',
            minimum_vram_gib=40, durations_seconds=durations)
requests=[]
for c in cs:
    requests.append(dict(canonical=c['canonical'],room=c['room'],k1_split='train',
        capture_sha256=s.digest(c),anchor_indices=c['anchor_indices'],
        frames=[dict(index=c['dense_frames'][i]['index'],path=c['dense_frames'][i]['path'],sha256=c['dense_frames'][i]['sha256']) for i in c['anchor_slots']],
        own_depth_shape=[32,51,51],expected_new_output=str(out/'own400'/s.digest(c['canonical'])[:16]/'own.npz')))
needs=dict(input_sha256=pins,additional_own_archives=archives,step400=s.read(s.ART400),cpu=dict(status='MISSING',
    reason='Step400 weights/artifact bundle not found in the bounded local checkpoint/K1 searches. No CPU forward pass can be measured from export pins alone. The existing GPU runner explicitly requires CUDA and >=40 GiB; CPU inference would need a separate device-compatible entrypoint.',
    limits=dict(cores=8,ram_gb=40),measured=False),gpu_estimate=timing,captures=requests,missing_gt=result['missing'])
s.dump(out/'NEEDS_INPUTS.json',needs)

def fmt(a):
    if a['status']=='MISSING':return 'MISSING'
    return f"{a['mra']:.3f} [{a['ci95'][0]:.3f}, {a['ci95'][1]:.3f}]"

rows=['| Arm | Fold 1 MRA [95% CI] | Fold 2 MRA [95% CI] | Combined MRA [95% CI] | Combined median served/GT |',
      '|---|---:|---:|---:|---:|']
labels={'A':'A: step 544 scale','B':'B: step 400 scale','C':'C: calibrated A','D':'D: calibrated B','E':'E: GT per-capture scale','F':'F: global raw-G3T scale'}
for arm in 'ABCDEF':
    a=result['combined']['arms'][arm]
    ratio=f"{a['median_ratio']:.6f}" if a['status']=='OK' else 'MISSING'
    rows.append('| '+labels[arm]+' | '+' | '.join(fmt(f['arms'][arm]) for f in result['folds'])+' | '+fmt(a)+' | '+ratio+' |')
diff=result['combined']['paired_differences']['C-A']
text=f"""# K1 training camera-displacement scale analysis

One fixed factor gives step 544 a small improvement: **{diff['points']:+.3f} MRA points [{diff['ci95'][0]:+.3f}, {diff['ci95'][1]:+.3f}]** across the two test folds. The fitted factors are {result['folds'][0]['coefficients']['C']:.6f} and {result['folds'][1]['coefficients']['C']:.6f}. Both folds meet the frozen improvement rule. This is evidence about K1 training rooms; it does not establish performance on any held-out split.

**Q2 is MISSING.** Step-400 K1 own-depth predictions were not found. B, D, B−A, and D−B cannot be estimated. The step-400 export manifest verifies artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`, step 400, run `6ed2c7aa`.

{chr(10).join(rows)}

| Contrast | Fold 1 points [95% CI] | Fold 2 points [95% CI] | Combined points [95% CI] |
|---|---:|---:|---:|
"""
for contrast in ['B-A','C-A','D-B']:
    cells=[]
    for f in result['folds']+[result['combined']]:
        x=f['paired_differences'][contrast]
        cells.append('MISSING' if x['status']=='MISSING' else f"{x['points']:+.3f} [{x['ci95'][0]:+.3f}, {x['ci95'][1]:+.3f}]")
    text+='| '+contrast+' | '+' | '.join(cells)+' |\n'
text+='\n| Quantity | Fold 1 | Fold 2 |\n|---|---:|---:|\n'
for title,values in [
    ('Fit factor C',[f['coefficients']['C'] for f in result['folds']]),
    ('Fit factor F',[f['coefficients']['F'] for f in result['folds']])]:
    text+='| '+title+' | '+' | '.join(f'{v:.6f}' for v in values)+' |\n'
for arm in 'ACEF':
    text+='| Median served/GT '+arm+' | '+' | '.join(f"{f['arms'][arm]['median_ratio']:.6f}" for f in result['folds'])+' |\n'
text+=f"""
The existing per-capture scale is close to calibrated: its combined pair-median served/GT ratio is {result['combined']['arms']['A']['median_ratio']:.6f}. Removing own depth and fitting one global raw-G3T scale gives {result['combined']['arms']['F']['mra']:.3f} MRA. The GT per-capture diagnostic reaches {result['combined']['arms']['E']['mra']:.3f}; it uses test GT and is not deployable. Its least-squares objective does not guarantee the maximum possible MRA.

## Population and frozen method

The manifest contains 242 K1 training captures in 221 rooms. Local GT is available for **{result['captures']} captures in {result['rooms']} rooms**, yielding **{result['pairs']:,} eligible pairs**. The frozen halves have 110 and 111 rooms; the scored test halves have 110 and 109 rooms after missing-GT exclusions. Each room appears in exactly one test fold. No held-out capture payload, R0-dev, dev-S1 item, BENCH item, or withheld item row was scored or opened as an evaluation input. The combined split manifest was parsed to select training captures and verify their existing capture digests; its item rows were not used.

The item rule is the prompt's all-pairs rule: all i<j among the 32 anchors with both GT poses valid and GT displacement at least 0.1 m. This is not the dev-S1 item generator. G3T camera encodings are decoded to camera centres before distances are computed. MRA averages ten strict tests `abs(pred−GT)/GT < 1−theta`, theta=0.50,…,0.95. Pair scores are pooled within each room, then rooms receive equal weight. Ratios in the table are pooled pair medians; the JSON also records the median of per-room medians.

C and F minimize room-balanced squared log error on the opposite half: `c=exp(mean_room(mean_pair(log(GT/pred))))`. E fits a separate zero-intercept distance least-squares scale per capture. Intervals use 10,000 room bootstrap draws, seed 17, with paired draws for C−A. They condition on the fitted coefficients and do not include coefficient-refitting uncertainty. The combined estimate pools out-of-fold room scores. The decision requires a strictly positive paired lower bound in both folds and combined; it does not impose a minimum practical gain.

`out/BARS_FROZEN.json` contains the room lists, complete metric, decision rule, missing-input policy, and code SHA-256. It was written before displacement scoring. Both freezing and scoring refuse when score files exist.

## Input identity and missing data

The 242 training `own.npz` files under `/scratch/jjyeung/k1/own_170235/native/probe` have per-capture receipts tied to the step-544 artifact manifest (SHA-256 `1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef`). That manifest explicitly records step 544 and private-ViT depth backing. Every scored depth, tower, and GT file was hash-verified.

The additional `own7/canary/native/probe` set has two training captures and the same step-544 identity. The `own7/ad2472b1be07d4193.result.tar.gz` and `own7/canary/c75955208369b4e48.result.tar.gz` archives have {len(archives[0]['training_receipts'])} and {len(archives[1]['training_receipts'])} training receipts respectively; all inspected training receipts bind to step 544. Archive and member hashes are in `NEEDS_INPUTS.json`. `run_convert_1` and `run_convert_2` receipts also bind to step 544; they are derived geometry, not independent own-depth checkpoints. The report recomputes scale from raw own-depth grids. Detailed set counts and receipt hashes are in the bars file. The bounded searches found no step-400 K1 depth set or local step-400 weight bundle.

The rule JSON and estimator were read from `/scratch/jjyeung/orch_n30/sb_records/work/policy_tree/student_pilot/`. The exact implementation takes the clip-wide median of finite confidence and keeps only confidence strictly above it, finite positive G3T depth, and finite own depth strictly between 0.1 and 10 m. It then takes the median own/G3T depth ratio across the 32×51×51 grid. The requested decision-record lines 13 and 35 were read once and agree with this rule.

Missing GT captures:
"""
for r in result['missing']:
    text+=f"\n- `{r['capture']}`: `{r['expected']['path']}` (expected SHA-256 `{r['expected']['sha256']}`).\n"
text+=f"""
## Reproduction and validation

Run from `/scratch/jjyeung/orch_n30/sb_scale1`. All reported MRA scores, intervals, ratios, counts, and coefficients come from:

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/scale_analysis.py freeze
/usr/bin/time -v env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/scale_analysis.py score > out/score.log 2> out/resources.log
```

The existing outputs intentionally prevent another scoring run in this workspace. The scorer reuses the exact named E3 `load_capture` and `mra` functions and camera decoder through AST extraction, avoiding the harness's workspace-writing startup hook. The harness directory was not modified.

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/test_scale.py
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/finish_report.py
```

Six unit tests passed: synthetic strict scale filters, room disjointness/determinism, existing-score refusal, MRA parity, camera-centre decoding, and equal-room log fitting. Scoring took 26.31 seconds wall time and 147,512 KiB peak RSS (`out/resources.log`). No GPU or network code ran. Inputs and code are pinned in each output JSON. `NEEDS.md` specifies the missing forward pass and resource estimate; `NEEDS_INPUTS.json` enumerates its exact 242 training captures and 32 anchor-frame pins per capture.

This internal report retains requested checkpoint names and split details because they are necessary to reproduce the experiment. It contains no superseded result narrative.
"""
(out/'SCALE_REPORT.md').write_text(text)
needs_text=f"""# Missing inputs for step-400 comparison

**MISSING:** K1 training own-depth grids for step 400, artifact `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`, leg R1 job 172660. The verified export manifest records run `6ed2c7aa`, archive object `q8/8865619b/6ed2c7aa_m400.tar`, archive SHA-256 `dcd49569e1555e18c403207f429de7b352f806bb11827fb57aa9973f4ceec7b5`, member directory `m400`. Expected heads: `m400/heads.pt`, SHA-256 `e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7`. The artifact, full-weight manifest and preparation pins are recorded in `NEEDS_INPUTS.json`. No exact existing local step-400 weights path was found; none is invented here.

Run the step-400 own depth forward on all **242 K1 train captures**, **32 RGB anchors per capture** (7,744 frame slots). `NEEDS_INPUTS.json` lists every capture, room, anchor index, RGB path, RGB SHA-256, capture digest, and proposed new output path. The 239 captures with local GT can be scored immediately after that forward; the three missing GT paths are separately listed. No held-out captures are required.

Reproduce `GPU.own` in the pinned `native_kit/boundaries.py`: load the step-400 artifact and its matched config/data receipt with the sealed runtime; use each capture's original `model_row` RGB-only prompt and exact 32 anchor frames; preserve its frame layout and preprocessing; run `_prepare_decode` under `closed_adapters` without token generation; query `own.depth_head` on the resulting depth map at the 51×51 grid spanning 0–1000 on each anchor. Save a finite `[32,51,51]` metre-depth array and a receipt binding the checkpoint, code, capture, and output hashes. The depth head uses its private ViT backing; the existing runtime must supply all of its required context. Do not substitute a standalone head call without proving matching inputs. Reuse the already cached G3T grids, confidence, and poses. SAM and G3T forwards are unnecessary.

**CPU feasibility: MISSING / unmeasured.** The required step-400 weight bundle was not found in the bounded local K1/checkpoint searches. Export pins and source code alone cannot run a one-capture forward. The existing `GPU` boundary explicitly rejects CPU and requires at least 40 GiB VRAM; a CPU-compatible entrypoint would need verification. Whether a complete forward fits 8 cores and 40 GB RAM remains unknown. No GPU code was run. Do not interpret the lightweight scoring runtime as a model-forward measurement.

**GPU planning estimate:** approximately **{timing['estimated_gpu_hours_242_at_mean']:.2f} GPU-hours** for 242 captures, plus model loading and staging. This extrapolates the mean **{timing['mean_seconds']:.2f} seconds/capture** from {timing['training_captures']} recorded step-544 training-capture own forwards; the median is {timing['median_seconds']:.2f} seconds and the 10th–90th percentile is {timing['p10_p90_seconds'][0]:.2f}–{timing['p10_p90_seconds'][1]:.2f} seconds. The source GPU model was not verified, and this is not a measurement of step 400. The existing runner requires one GPU with at least 40 GiB VRAM. Recalibrate with one training capture on the intended device before scheduling the full pass.

The timing estimate comes from train-only `capture_start`/`capture_commit` metadata in `{progress}`, SHA-256 `{pins[str(progress)]}`. Produce all counts and timing arithmetic with:

```sh
env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 nice -n 10 /scratch/jjyeung/envs/p1cpu/bin/python code/finish_report.py
```

After predictions and missing GT are supplied, use a new experiment output directory and freeze its bars before any new scoring; the existing result is protected against overwrite. Keep B−A and D−B on identical frame pairs and room folds.
"""
(out/'NEEDS.md').write_text(needs_text)
print(json.dumps({k:v for k,v in timing.items() if k!='durations_seconds'},indent=2))
