# Ground-call capture kit

**Status: BLOCKED for launch.** The CPU-tested overlay and join are available. The supplied reader record does not state a numeric printed-gap tolerance, the exact step-544 package has not been compared with this lane's local A10b source, and the Orchard authenticated entry sequence has not been exercised with this overlay. `policy.json` therefore refuses live mode before loading weights. A reads-lane review is owed; this kit is not a launch approval.

The first experiment covers step 544's exact 150 dev-S1 distance items. Its 149 calling items supply 298 ground calls and 149 gap calls; the one non-caller remains a no-call record. The model performs the original prompt prefill to obtain its gravity and depth heads, then the reader executes the recorded calls. It generates no reasoning or answer tokens. The 32 language-model/grounding anchors and the reader's **64 native G3T frames** stay bound to the original frame manifest and RGB hashes.

The baseline is Orchard job 171253, package `/project/community/jjyeung/b9ef552934627`, original job script `BATCH.sh`. The record pins its payload by prefix `8be887e3`, delivery `okh7/7b422049/1.tgz` by prefix `57d2a513`, and PACKAGE.json by prefix `18e81733`. Its canonical logical root is `/scratch/jjyeung/b01ec87a6f29b`: unpacked code `p`, checkpoint `d/e`, G3T in the artifact binding `d/binding.json`, SAM `d/k/sam3.pt`, frames `d/f`, interpreter `d/v/py`. These are record-backed locations, not a fresh Orchard check. `READER_R1_20261117.md` and `events/reader_r1/20261118T0529Z_RESULT_r1_read_pins_handoff_to_cont_ops13.md` supply the settings. The A10b package, job 173060, lives at `/project/community/jjyeung/okh7/a15_cot_apdc76460c3a164`; its local code is a CPU fixture, not a substitute for verified step-544 code.

`run.py` uses the reader's `make_capped_real`, pinned frame binder, prompt preparation, lazy perception, and original call hook. It observes function-return locals with `sys.setprofile`. It neither edits sealed files nor adds model forwards. The observer retains every detector-returned proposal, including those rejected by early lifting, as lossless column-major RLE with frame, source index, score, presence and exact prompt. Here “proposal” means the original detector's retained outputs under its joint-score/cap contract, not logits discarded inside SAM. It records linked-track membership, every accepted candidate's masks and features, exact selector inputs, all logits including null, choice, selected masks, early lift outcomes, final lift centroid/extent/support, fitted box in world and f1 coordinates, and camera/intrinsic/canvas/scale metadata. An empty pool never invokes the selector; its null slot has an explicit index and `slots=null`, rather than a fabricated logit.

The final lift summary describes the points the reader actually keeps. `frame_count` counts supported frames, while `point_frames` identifies the best frame whose points feed the box. The GT join uses the unrounded fitted-box centroid, not the mean of the point cloud. Raw masks are 480×640 and selected masks 240×320; GT must explicitly supply both grids. The join never silently resizes or guesses a coordinate transform.

The writer saves one gzip JSONL and a final receipt. It flushes each complete item and refuses compressed output above **1,900,000,000 bytes**. It creates the trusted receipt only after every item passes parity. Frames, best-frame index, call sequence, served state and nonnumeric responses must match exactly. Gap comparison is absolute metres with a configurable record-backed tolerance. The packaged tolerance is **unset**: the named record and smoke event discuss bitwise GPU nondeterminism but give no numeric bound. CPU fixtures use 0 m; a unit test demonstrates acceptance at 0.01 m and rejection at 0.009 m, which does not authorize either for a real read. A mismatch aborts the job and leaves no trusted receipt. A memory or output-cap failure has the same effect.

The production entry needs the reads lane to supply a reviewed policy with exact source hashes, verify the step-specific checkpoint, and integrate this wrapper into the original authenticated namespace/staging sequence. No weights, frames or environment should move to Trinity. The job template `0.sh` requests general, one H100, eight CPUs, 200 GB host memory, and 12 hours. Its required variables are `K` (opaque overlay directory), `P` (sealed unpacked package), `S` (prepared settings), and `O` (fresh local output). The resource-level submission skeleton is:

```bash
K=/scratch/jjyeung/5b97d3c2e8a10 P=/scratch/jjyeung/b01ec87a6f29b/p \
S=/scratch/jjyeung/5b97d3c2e8a10/2.json O=/scratch/jjyeung/5b97d3c2e8a11 \
sbatch --export=ALL --partition=general --gres=gpu:h100:1 --time=12:00:00 \
  --job-name=a15_cot_ap5b97d3c2e8a10 /scratch/jjyeung/5b97d3c2e8a10/0.sh
```

This is **not a runnable submission handoff**: the exact namespace bootstrap and staging/return seal remain unbuilt, and the delivered policy rejects it. `0.sh` is the inner wrapper the reads lane must attach to that bootstrap. The wrapper must retain the reader's cache roots and audit permissions. Do not invoke an existing full-answer job script as a shortcut. No submission command was executed here.

## CPU validation

From the bundle root:

```bash
OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' python -B -m unittest discover -s kit/rerun2 -p 'test_*.py' -v
OPENBLAS_NUM_THREADS=1 CUDA_VISIBLE_DEVICES='' python -B kit/rerun2/run.py --dry-run --out NEW_LOCAL_DIRECTORY
```

The nine new tests cover exact local production `StageOne.features`/`select` bodies with CPU producer/weight doubles, real lifting/provider bodies with synthetic geometry, unchanged return values, RLE, null slots, all six stages, unknown annotations, frame binding, rigid transforms, parity failures and the size cap. Eleven existing funnel tests also pass. Neither torch nor weights were loaded. Test directories remain on `/tmp`.

Dry reports for step 544, step 400 and frame flags 64/96 are in `work/rerun2/`. They reach argument parsing, 150-item manifests, complete synthetic schema/RLE write/read, fabricated all-item parity and a synthetic GT join. The 64/96 flags only parse; they do not simulate a dense inference adapter. The synthetic capture uses one object, three rectangular-mask frames and one candidate: **1,344 compressed bytes/item at 544**, **1,343 at 400**. These are measured fixture sizes, not a forecast for real masks. Real size/item and throughput remain unmeasured. Raw mask roundtrip and all-item parity are necessary checks; this CPU evidence does not establish GPU parity or runtime integration.

## Optional flags and budget

| Flag | Required extra inputs and implementation | Orchard availability | Planning GPU-minutes |
|---|---|---|---:|
| Default `--step 544 --frames 32` | Exact original package, settings, checkpoint, 32 anchors/64 tower frames | Record-backed from job 171253; availability not queried | 80–120 H100-min |
| `--step 544 --frames 64` | Nested added RGB hashes, extra own-depth queries/geometry, variable-frame contract and selector coverage features; keep original LM input | Original 64 tower frames exist by record, but they do not establish the kit's nested 64-anchor set or compatible own-depth queries | 160–240 H100-min |
| `--step 544 --frames 96` | Above plus 96 bound source frames and memory check | No matching 96-frame manifest identified | 240–360 H100-min |
| `--step 400 --frames 32` | Step-400 export/settings and A10b source pins; replay includes malformed/cap-reaching attempts | Record-backed from job 173060 | 60–90 H100-min |
| `--step 400 --frames 64/96` | Both step-400 and respective dense-arm requirements | Extra RGB bindings and dynamic adapter unverified | 120–180 / 180–270 H100-min |

The baseline reads took 77.30/57.96 H100-min including answering. These budgets round upward and scale by anchor count; they are provisional reservations, not measured ground-only cost or guaranteed bounds. A first-item timing/memory receipt must establish whether to continue. The 12-hour limit caps one allocation at 720 GPU-minutes. Optional dense arms refuse live mode as delivered. The held-out items and their measurements are never training rows.

## Ground truth on Trinity

`gt_staging.json` lists all **60** required captures, each exact expected filename, host, and known inventory byte size. `gt_available.txt` lists the **38** matching files in `trinity-1-18:/scratch/jjyeung/orch_cd/dose_pool/out/{t1_gt,arkit_gt}/gt`, totaling **160,652,325 bytes**. The other **22** expected files are explicitly unlisted with unknown sizes. The first 4,000,000 bytes of `events/k1_ops3/ORCH_CD_MIRROR_1_18_FILES.txt` contain all 93 entries in those two named GT directories; only this bounded prefix was read. Listed sizes are inventory evidence, not fresh remote stat results. No alternative copy is asserted.

After the transfer owner authorizes it, run `bash gt_stage_on_1_18.sh /ABSOLUTE/LOCAL/gt_available.txt` **on trinity-1-18**, using its existing session. The script sends one archive directly to trinity-2-28.ib and extracts on scratch. It never passes through `/data*`, the head node or a laptop. The 22 missing files need a separate authoritative manifest or raster production; the script does not silently pretend to stage them.

The join additionally requires reviewed item/name→instance bindings, complete visibility including zero masks for every exact source index, annotation-validity flags, full-extent oriented boxes and annotation camera poses/axis conventions. Those fields must be converted from the actual NPZ schema into the `join.py` JSON contract. The NPZ contents were not accessible here, so a production NPZ adapter is not implemented. Camera/scale capture supports this conversion, but does not itself certify alignment. Metric alignment must use reviewed camera coordinates with a rigid transform; fitting a GT scale is rejected.

Once a capture has a matching all-item parity receipt and the reviewed GT JSON exists:

```bash
python kit/rerun2/join.py --capture LOCAL/0.jsonl.gz --receipt LOCAL/1.json \
  --gt LOCAL/gt.json --out LOCAL/stages.jsonl
```

The synthetic tests exercise this join's S0–S5 logic. Missing upstream evidence yields U. The join matches raw proposals and selected masks at IoU > 0.5, requires at least half of nonempty selected masks to match, counts distinct matched frames, and tests the fitted centroid against the full OBB at the strict 0.25 m boundary. This rule still needs a real-instance sensitivity review.
