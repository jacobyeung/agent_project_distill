# Own-encoder probe API

The CPU build supplies room admission, frozen encoder handles, four probe heads, fixed decision rules, and G3T taps. GPU smoke results and the measured branch-O key choice remain pending. T1 results produce a provisional choice before teacher labels exist. Use `out/GPU_COMMAND.md` to run E-A on the allocated GPU.

## Room admission

Add this lane's `out/` to `PYTHONPATH` and import `room_gate`. Call `read_manifest(path)` before opening training images, rasters, masks or features. It validates the entire manifest before returning rows. `read_manifest(path, 'tuning')` admits only the 31 tuning scans. Both modes reject the clean 33 scans. A path containing a clean scan also raises `RoomViolation`.

```python
import room_gate
room_gate.room('scannet', 'scene0400_01')  # scannet/scene0400
rows = room_gate.read_manifest('out/b2_manifest.jsonl')
evaluation = room_gate.read_manifest('out/tuning_manifest.jsonl', 'tuning')
room_gate.check_row(row, 'training')
room_gate.guard_path(path, 'training')
```

```bash
python out/room_gate.py check out/b2_manifest.jsonl
python out/room_gate.py check out/tuning_manifest.jsonl --purpose tuning
```

The CLI exits 0 for admitted manifests and 3 for violations, printing offending rooms. Dataset aliases, ScanNet rescans, ARKit venues, qualification rooms, nested paths and room splits are checked. Unknown ARKit videos fail closed. Keep `room_gate.py`, `EVAL_ROOMS.json` and `EVAL_ROOMS.sha256` together. `O1_REVIEW.md` records the independent 46-check review.

The training manifest has 6,560 frames in 205 scans and 184 rooms: 5,280 training frames and 1,280 validation frames. The tuning manifest has 992 frames, 31 scans and 221 named objects. `image_size` is `[width,height]`; `image_size_hw` is `[height,width]`. Slots are zero-based; `frame_index` is the source frame index. Each training instance supplies its ID, name and pixel area at the 240×320 raster size. The 45 additional exclusions explain the difference from the 8,000-frame inventory.

## Frozen features

Add `work/` and `out/` to `PYTHONPATH`. The weights argument accepts the matching dictionary in `WEIGHTS.example.json`. All model loads are local. Optional HF models require `LOCAL_PIN.json`; see `DOWNLOADS.md`.

```python
import json
from own_feats import load, encode, pool, name_embed
weights = json.load(open('out/WEIGHTS.example.json'))
encoder = load('qwen_vit', weights['qwen_vit'], 'cuda:0')
maps = encode(encoder, pil_frames, (480, 640))
from own_feats.core import readout_maps
stats = json.load(open('/dev/shm/jjyeung_probe_r3/feats/A1/CHANNEL_STATS.json'))['statistics']
regions = pool(readout_maps(maps, 'four', stats), (masks, frame_indices))
names = name_embed(['chair', 'kitchen cabinet'])
tokens, means = names.tokens, names.mean
```

`encode` takes the loaded handle and returns a list of CPU fp16 tensors `[frames,height,width,channels]`. Call `encoder.encode(..., cpu_dtype=torch.float32)` for CPU parity checks. Parameters stay frozen; GPU execution uses bf16 autocast. Qwen/V-C load only vision tensors. The language model never enters GPU memory. Frames remain in caller order; Qwen duplicates each image for its temporal patch size of two and restores row-major spatial order before returning maps.

| Arm name | Probe | Size H×W | Taps |
|---|---|---|---|
| `qwen_vit` | A1 / A2 | 480×640 / 768×1024 | One-based blocks 7, 14, 21, 27; 4×1152 channels |
| `vc_vit` | A3 | 768×1024 | Same taps from V-C depth ViT |
| `g3t` | A4 | 392×518 | Zero-based blocks 5, 11, 17, 23; 4×2048 channels |
| `cradio_v4_so400m` | A5 | 768×1024 | Four quarter-depth backbone taps |
| `dinov3_vitl16` | A6 | 768×1024 | Four quarter-depth taps; CLS/register tokens removed |
| `sam3_pe` | A7 | 1008×1008 | PE blocks 8, 16, 24, 32 |
| `dinov2_vitl14_reg` | D2, optional | 392×518 | Four quarter-depth taps; not a G3T result |

A8 concatenates aligned A2/A4 region features in RAM and reduces them to the common 1,024-channel width. Qwen/V-C dimensions must be multiples of 32; patch-14 arms require multiples of 14. Smoke tests use each arm’s exact configured input. G3T must receive all 32 ordered clip frames together for the probe.

`pool(maps, masks)` uses masks `[regions,H,W]`. A single map frame may serve all masks; otherwise provide one mask per frame or the explicit `(masks, frame_indices)` tuple. It resizes masks by area averaging, computes an area-weighted mean, L2-normalizes each tap and concatenates taps. Empty masks produce zeros. Dense maps never enter the disk cache.

`name_embed` returns `NameBatch`: `tokens [N,P,4096]`, `mean [N,4096]`, a Boolean padding `mask`, `token_ids`, `rows_sha256`, and `tokenizer_sha256`. It reads only the requested frozen embedding rows. The means exclude padding. Training and scoring names use SAM's local `common.phrase` normalization.

## Probes and artifacts

`extract.py` fits channel moments on 1,320 stride-selected train frames, then selects every fourth training slot and up to eight regions per frame by a fixed seed-17 hash. It extracts every tuning candidate member. The planned cache has 12,411 training/validation regions and 4,582 tuning members. Each scene shard records input hashes, authority hash, rule hash, code binding and weight identity. The writer refuses a cumulative feature cache above 2 GB. A8 creates no extra cache.

T1 fits 1,200 listwise steps on GT regions in training rooms and validates on separate rooms. Its optional 300-step SAM-score fusion also fits only training rooms. T2 fits a two-block, 256-dimensional mask decoder for 1,500 steps on 1,500 O5-positive frames. T3 fits name-conditioned presence for 1,500 steps on POS/ABSENT agreement labels. T4 fits an identity projection for 800 steps. All three readouts use 1,024 input channels and identical head capacity per task. T2/T3 globally shuffle examples with seed 17 and batch size four. All heads have fewer than six million parameters. See `ONLINE_SCHEMA.md` for O5 inputs.

`RULES.json` and its SHA freeze R1, R1+, R2–R4, arm choice and 4,000-draw seed-17 bootstrap settings. `card.py` leaves missing measurements pending. T1 selector checkpoints contain both feature and fusion states when fusion labels exist; only a passing card authorizes their downstream use. Routed tuning diagnostics run separately through `routed_tuning.py` and the existing X2 scorer.

## G3T integration

`out/g3t_taps.py` is a portable copy; keep `out/provenance.py` beside it. During an existing full G3T forward:

```python
from g3t_taps import TapCapture
with TapCapture(model.eval(), (392, 518), frame_order=lm_order) as capture:
    prediction = model(images)
maps = capture.maps  # keys '5', '11', '17', '23', 'trunk'
```

`lm_order` is a permutation of all input frame indices. Omit it when input already follows LM order. Maps are `[F,h,w,C]` on the model's device; `trunk` aliases block 23. The temporary sparse-retention context keeps the four probe taps plus the distinct first head tap without changing state-dict keys. It restores the model's forward method on exit. `MEMORY_AUDIT.md` distinguishes this full-model optimization from the existing camera-only lean path.
