`student_pilot.recording_pose` builds Run 1 A1 pose-only rows on CPU. It reuses
`pose_samples.encode_sample`, its gravity and scale calculations, its row schema,
and its photometric augmentation settings. It creates no depth labels.
The label-bank loader skips depth queries when the pose-only depth branch is
explicitly frozen. It retains empty depth tensors and leaves unfrozen depth
admission unchanged, so pooled rows need no original bank-frame match.

The sampler uses the dataset probabilities and raw-frame interval bounds in
[Cambrian-P v2, Appendix A.1, Table 14](https://arxiv.org/html/2605.22819v2#A1).
N is uniform over the members of {8, 16, 24, 32} that fit the recording at
the 30-frame minimum interval. Each scene produces 80 rows by default.
The existing pose-row loader reads PNGs, so this builder stages a pool rather
than offering an unsupported on-the-fly video option.

The 96-frame pool contains a random fixed-interval scaffold, a random
variable-interval scaffold, a stratified draw from each recording sixteenth,
and random draws that fill the remaining slots. Both scaffolds contain the
largest supported N. Rows select exact paths inside this pool. Collection rows randomly
permute pooled frames; video rows use a random feasible start and exact
30–100 raw-frame gaps. The pool therefore conditions the interval and start
distributions. This is a bounded-pool approximation, recorded in every row
and audit. The sampler chooses N from the recording's audited feasible sizes
before choosing a mode. It never substitutes a nearest frame, changes modes,
or changes the bounds to make a row fit.

Recordings shorter than 211 frames cannot support any requested video N.
They are deferred before sampling. Sparse ScanNet pose sets are also deferred:
127/64/32 poses cannot establish full-recording frame/pose count equality.
Full ScanNet poses would use its requested 0.6 video and 0.6 fixed probabilities.
The availability audit supplies full poses for ARKitScenes and ScanNet++.

An index entry may explicitly opt into sparse posed frames with `sparse_poses: true`
and `frame_numbers`, the distinct increasing raw ordinals of its poses. Their
count must equal `pose_count`, and each ordinal must be below `total_num_frames`.
The NPZ must carry the same ordinals in the same pose-row order. The opt-in
currently supports `table14` only. The pool and all draws use posed frames;
video draws select the nearest posed target among candidates that preserve
30–100 raw-frame gaps and a feasible remaining path. Ties select the lower
ordinal. Fixed mode fixes target spacing; effective gaps may differ. Every row
records both target ordinals and effective intervals. Sparse decoding uses
PyAV on CPU and checks the decoded count against `total_num_frames`. Full-pose
entries retain the existing sampler, decoder and row bytes.

Prepare the following small JSON inputs on the machine that holds the payloads.
Every pin is exactly `{"path": "/absolute/path", "sha256": "<actual digest>"}`.
The parent owns source staging and submission; this tool never connects to AWS.

* The request has schema `recording-pose-request-v1`, a `recordings` pin,
  `authorities`, and optional integer `seed` (17) and `rows_per_scene` (80).
* `authorities` requires `gate`, `vsi288`, `vsti`, `division`,
  `admission_policy`, and `extra_benchmarks` (a list of pins, possibly empty).
  The gate pins `configs/gate_heldout_scenes_v1.json` and must contain its 38
  distinct scenes. VSI pins an exact copy of `/data2/jjyeung/scene_288.tsv`
  and must contain 288 distinct two-column dataset/scene lines. VSTI is a
  complete scene authority, not a representative question subset; its JSON
  contains `scenes`. No authority may be omitted.
* The frozen division uses the repo's `train_scenes`, optional `heldout_scenes`
  and `heldout_group_ids`. The admission policy uses the existing
  `auxiliary_targets` `allowed_groups`/`excluded_groups` contract. If it names
  `required_exclusion_lists`, the request's `extra_benchmarks` must match those
  pins exactly. The parent must supply every additional benchmark authority
  used by admission. Additional JSON authorities contain `scenes`.
* Scene lists contain `[dataset, scene]` pairs or `dataset/scene` strings.
  Native dataset names and d1/d2/d3 are accepted. Native ScanNet identities
  close over repeat scans. Opaque gate tokens also close over ScanNet suffixes.
  A recording must belong to both the frozen division and admission policy.
* The recording index contains `recordings`, each with native `dataset` and
  `scene`, integer `total_num_frames` and `pose_count`, positive `fps`, `video`
  and `poses` pins, and `coordinate_frame` equal to
  `source_world_meters_opencv_camera_to_world`. `fps` only supplies the existing
  trainer's required timing metadata; sampling never uses it.
* Each pose payload is an NPZ with `c2w` (or `camera_poses`), `intrinsics`,
  `raster_hw`, `frame_numbers` (or `indices`), and `world_up` (or an explicit
  `world_up` vector in its index entry). Indices must be integer raw frame
  ordinals `0..pose_count-1`. Intrinsics may be one 3x3 matrix or one per frame
  and must already describe the decoded RGB raster. Poses must use metres and
  OpenCV camera-to-world axes. This is the explicit input contract; adapt an
  existing archive index to it without guessing coordinate conventions.
* A pose pin may additionally contain `member` and `member_sha256` to select
  an NPZ in an uncompressed tar, including a normalized member of
  `full_rec_poses_4380.tar` or `4951`. The builder authenticates both archive
  and member and never extracts them. The archive's real member schema must
  be checked by the parent on code-aws; production payloads were not read here.

Run with CUDA hidden, disabled bytecode, and single-threaded CPU libraries:

```bash
python -B -m student_pilot.recording_pose plan --request request.json --output plan.json
python -B -m student_pilot.recording_pose jobs --plan plan.json --plan-sha256 "$PLAN_SHA" \
  --frame-root /store/abcd1234/f --receipt-root /store/abcd1234/o \
  --deployment /store/abcd1234/c --output new_jobs
```

The plan lists the pool's raw frame numbers, admitted scenes, exclusions,
deferrals, and source hashes. Exclusions precede pool sampling and all payload
reads. Every stage/build invocation rechecks the authority files and their
hashes, so the parent must stage those files and preserve their pinned paths.

The generated Slurm script uses partition `cpu`, QOS `cpu-normal`, a 90-minute
limit, two CPUs, 8 GiB, no GPUs, and an array with concurrency `%4`. Its default
shard count assigns at most 16 recordings per task. This is a staging plan,
not a measured runtime estimate; select smaller shards before submission if
needed. The parent must precreate the receipt/log directory, set `PYTHON` to
the deployment's existing interpreter, run the anonymity gate, and submit it.
Job and script names are `a15_cot_ap<hex>`. Use opaque deployment/input/output
paths too; arbitrary supplied paths can still fail the anonymity gate.

Each task runs `stage --plan ... --plan-sha256 ... --frame-root ... --shard K
--shards S --output NEW.json`. It hashes the video, uses ffprobe's decoded
frame count to require exact equality with the full pose count, and uses
ffmpeg's raw ordinal selector to emit only pooled RGBs. Codec dependencies
and the count pass may decode other frames internally; no other frame images
are saved. No resizing or frame rate conversion occurs. Frames are PNGs at
`<frame-root>/<sha256[:2]>/<sha256>.png`, matching k3f8's addressing pattern.
Each receipt lists frame number, path, SHA-256, raster, and count evidence.
The CPU deployment needs its existing ffmpeg, ffprobe, NumPy and Pillow.

Collect the stage receipt pins into a JSON list, then run:

```bash
python -B -m student_pilot.recording_pose build --plan plan.json --plan-sha256 "$PLAN_SHA" \
  --staged-pins staged_pins.json --output new_rows
```

`pose_rows.jsonl` preserves POSE32_V2's outer row fields. Its `pose_sample`
adds `recording`, which records raw frame numbers, pool positions, interval
mode and signed effective intervals. `positions` also refers to the pool.
The trainer retains its required timing fields. `AUDIT.json` records source
pins, rows and scenes by dataset, exclusions and deferrals, N and interval
histograms, pool coverage, and target sanity. Outputs are new-only. All
fixtures and failed-attempt artifacts remain on disk.

Portable verification uses `/scratch/jjyeung/envs/p1cpu/bin/python -B -m
unittest tests.test_recording_pose -v` with CUDA hidden. Set `B2_TEST_OUTPUT`
to an owned scratch directory. Decoder tests use synthetic PPM streams;
they do not read production media or establish full staging throughput.

A1 all-frame mode uses `variant: "all_frames32"`, `pool_size: 96`, and
`rows_per_scene: 80`. Every row draws a fresh sorted uniform set of 32 distinct
posed raw ordinals from the fixed staged pool. Sparse index entries use their
explicit posed ordinals; this mode never substitutes nearby frames. The pool
still conditions the distribution, and changing `epoch` selects a new row
manifest. Every pose is relative to the first sampled frame, and every row
carries `anchors: [1,...,32]` and `temporal_grouping: "fused_pairs_all_frames"`.
The origin pose is supervised too. Gravity and trajectory scale retain the
existing definitions; scale now averages successive all-frame encoded translations.
The label loader gives these recording rows empty depth targets while retaining
legacy A0 depth supervision in mixed training. Exclusions and division checks
run unchanged before pool construction. A division without ARKit scenes cannot
admit ARKit recordings; the parent must supply any revised authority explicitly.

For Stage 1, set `all_frames: true` in a `decoupled-v-run-v1` config with mode
`decoupled_vc` (A1) or `decoupled_v`. Fresh V-C preparation can build its own
rows database; omit `reuse_preparation`. Reuse requires identical input pins
and the same all-frame setting. Keep the training bank as the original depth
bank and mix the new rows with A0 rows as selected by the parent. A0's 16 pose
and depth slots expand into even frame slots; odd slots are zero and masked.
Short A0 inputs retain their actual temporal length. The exported P3 artifact
names all 32 anchors and carries trainable `[32, dim]` frame queries; each fused
ViT state and grid repeats twice before its frame query is added. The V-C
private encoder and heads train; the original encoder and LM remain untouched.

Held-out inference requires the separate `student_pilot/all_frame_bank/v1`
bank. It has 32 camera slots and the original 16 depth slots, explicitly mapped
by `depth_anchor_frames: [1,3,...,31]` (zero-based). Build it with
`python -B -m student_pilot.all_frame_bank --request REQUEST --output BANK.npz
--report REPORT.json`. The request schema is `all-frame-bank-request-v1`, with
an `original` bank pin and `sources` entries containing `dataset`, `scene`,
`coordinate_frame: "source_world_meters_opencv_camera_to_world"`, and a `poses`
pin. Each NPZ contains `frame_indices`, `c2w`, `intrinsics`, `raster_hw`, and
`world_up` at exactly the bank's 32 raw indices. The builder rejects incomplete
GT, checks the even frames without fitting alignment, and preserves depth bytes.
Readout reports the gate on 32 poses, the gate on even poses, and the head_acc
rotation, centre, pair-direction and pair-MRA metrics for both subsets. The
even gate omits the 32-frame scale-head target; its depth points remain identical.

The A1 CPU pipeline (`student_pilot.a1_pipeline`) extends the training side of
an inherited division through a separately pinned authority. It preserves the
held-out fields and exclusion policy, closes ScanNet repeat scans, and reports
recordings too short for 32 distinct posed frames. The mixed manifest retains
A0's depth targets and uses content-addressed `/data2/k3f8` frame paths.

The A1 kit first hashes the complete run05 video index, then creates opaque
hardlinks (serial copies across filesystems). Only those two CPU operations
open private real-path files. Later operations use the pinned alias index.
The frame plan saves exactly the ordinals selected by its rows. One tar includes
those PNGs and the row-used A0 PNGs from the pinned original archive; the installer
verifies every digest after extraction. The plan job checks PyAV, Pillow, NumPy,
ffmpeg and ffprobe in the existing runtime before any frame array starts.

The approved B10 scanner and word list remain byte-identical. `a1_scan` assigns
disjoint row ranges to SQLite or canonical JSONL tasks and merges complete
reports into rscan-v1. It preserves the scanner's table/row/cell and line
locations, including sqlite_schema. Every shard hashes its immutable input.
The merge refuses gaps, overlap, duplicate tasks, changed pins and truncated
hits. Small JSON metadata uses a separate CPU array. No scan runs on the login
node. The parent submits only one CPU operation at a time, with arrays capped
at four tasks, and reseals after every measured binding changes.

The parent-approved held-out policy permits zero/masked odd (one-based) slots
only for d1; d2 requires all 32 slots. Its bank keeps the original 16 depth slots
and even-frame poses. Masked d1 scenes have no 32-frame scale target. The readout
counts only valid camera slots and reports both the available all-frame cohort
and the original even subset. This policy requires no `.sens` reads.

Frame writers publish PNGs with an atomic hardlink after writing complete bytes.
Concurrent tasks may share a digest without observing a partial file. Temporary
hardlinks remain on disk under the no-deletion policy; the tar includes only the
manifest-selected final PNG paths.
