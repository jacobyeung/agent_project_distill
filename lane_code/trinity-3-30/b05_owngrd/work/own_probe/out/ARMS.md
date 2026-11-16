# Encoder inputs and readouts

Sizes below are **width × height**. Every arm resizes the complete RGB frame with bicubic interpolation, without a crop or pad. Region masks use area pooling. Layers are one-based unless stated otherwise.

| Arm | Encoder and input | Pixel normalization | Patch; spatial grid | Four taps; final control | Source of numbers |
|---|---|---|---|---|---|
| A1 | Student Qwen3.5 vision, 640 × 480 | `(RGB/255 − 0.5)/0.5` | 16; 40 × 30 | 7, 14, 21, 27; 27 | T0 `base/config.json` and `base/preprocessor_config.json`; experiment resolution in design §2 |
| A2 | Same student weights, 1024 × 768 | Same as A1 | 16; 64 × 48 | 7, 14, 21, 27; 27 | Same bundle; design §2 |
| A3 | V-C `depth.model.visual`, 1024 × 768 | Same as A1 | 16; 64 × 48 | 7, 14, 21, 27; 27 | Same vision config; local `heads.pt` tensor namespace; design §2 |
| A4 | G3T, 518 × 392, ordered 32-frame clip | Provider sends `[0,1]`; aggregator applies ImageNet mean `(0.485,0.456,0.406)`, std `(0.229,0.224,0.225)` | 14; 37 × 28 | 6, 12, 18, 24 (code indices 5,11,17,23); 24 | Local `g3t_vendor/vggt/models/aggregator.py`; design §2 resolution |
| A5 | C-RADIOv4-SO400M, 1024 × 768 | Provider sends `[0,1]`; pinned RADIO input conditioner applies its own normalization | 16; 64 × 48 | `ceil(D/4), ceil(D/2), ceil(3D/4), D`; expected 7,14,21,27 for D=27; D | Design §2 and W3; staged pinned RADIO config and block count must confirm D, patch and conditioner. Source/weights absent locally |
| A6 | DINOv3 ViT-L/16, 1024 × 768 | Staged processor's `image_mean` and `image_std`; expected ImageNet values above | 16; 64 × 48 | 6, 12, 18, 24; 24 | Design §2 and W1; staged config/processor must confirm depth, patch and normalization. Optional/gated inputs absent |
| A7 | SAM 3 PE-L+, **1008 × 1008 in both smoke and probe** | `(RGB/255 − 0.5)/0.5` | 14; 72 × 72 | 8, 16, 24, 32; 32 | Receipt-pinned `sam3/model_builder.py`, `_create_vit_backbone`; `sam3_image_processor.py` |
| A8 | A2 + A4 at their respective inputs | Each component's documented normalization | A2 grid; A4 interpolated to that grid for dense heads | Both components' four taps; both final layers for control | A2/A4 sources above; fixed paired-arm definition |
| D2 | Optional DINOv2-L/14-register diagnostic, 518 × 392 | Staged processor mean/std; expected ImageNet values | 14; 37 × 28 | 6, 12, 18, 24; 24 | Design §2 stand-in definition; staged config and processor must confirm. It cannot substitute for A4 |

Qwen supports dynamic resolution; 640 × 480 and 1024 × 768 are experiment settings within its documented patch/merge constraints. The outside dynamic-resolution arms use the design's experiment sizes, not a claim that their default classification processor uses that size. Missing source documentation or an incompatible provider interface must produce a recorded failure or skip before fitting.

Local source locations:

- T0 bundle: `/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle/base/`.
- G3T source: `/scratch/jjyeung/orch_cd/integ_v3/work/tree/student_pilot/g3t_vendor/`.
- Design and citations W1/W3: `/scratch/jjyeung/orch_cd/design_g3d/d_ownenc/out/DESIGN.md`.
- Required SAM source copy: `/scratch/jjyeung/orch_cd/mdg_next/work/data/sam3src`. `SAM_SOURCE_CHECK.json` records all six expected hashes and whether this copy matches. All six source hashes match. The local source inventory is 4,739,916 bytes. Architecture numbers were also checked against the named upstream files in the receipt; no source tree was scanned or copied from network storage.

Every encoder exposes exactly four taps. Extraction fits per-channel means and variances on the training split only, with variance floor 1e-6. Each standardized tap receives non-affine token layer normalization, deterministic channel averaging, and another layer norm. Four taps contribute 256 channels each; the final layer contributes 1,024. The unstandardized four-tap control omits channel standardization. A8 uses the fitted transforms of both components and reduces their concatenation to 1,024. All readouts have identical learned head capacity. Region pooling L2-normalizes each pooled tap.

The GPU smoke compares features inside real instance masks on original and mirrored frames. Correct correspondence must beat the unflipped mask position and all prespecified shifted/transposed controls. A provider cannot extract features unless this gate passes. The CPU test uses a real frame and real instance masks with an image-derived descriptor, and rejects shifted, transposed and noise grids. Real GPU-provider outcomes remain pending. SAM also requires a recorded bf16-autocast forward at 1008×1008.

G3T weights: `/dev/shm/jjyeung_mdg_next/g3t` on trinity-2-18; stage to `/dev/shm/jjyeung_evalx/g3t` on trinity-1-18. Use `WEIGHTS.gpu.json` on the target.
