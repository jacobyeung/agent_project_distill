# Build: own-encoder grounding head (branch O, T-1 stage) — training kit, CPU-verified

You implement code only, on CPU. Rules: no git, no ssh, no network, no GPU, no file removal of any kind (rename if you
must move something aside), no recursive search outside the directories named here, no reads under /home or /data*
except the design file below. Write only under /scratch/jjyeung/orch_n30/b05_owngrd/code (package `owngrd`, tests in
`code/tests`) and scratch outputs under /scratch/jjyeung/orch_n30/b05_owngrd/tmp_codex. Python:
/scratch/jjyeung/envs/allospatial_1111_v1/bin/python (torch 2.12 on CPU, torchvision, scipy, transformers 5.4 with
qwen3_5, safetensors, pytest). Keep the existing modules and their 16 passing tests unchanged in behaviour
(`cd code && python -m pytest -q tests`). Limit torch to 16 CPU threads.

## Read first
- Design: /data2/jjyeung/agent_project_data/distill_design/GROUNDING_OWN_ENCODER_20261110.md — read only lines 74-88
  (section 1.4), 124-167 (sections 3.1-3.5) and 275-end (P7 audit).
- Existing code: code/owngrd/{common,eligibility,vocab,build_manifest,teacher,labels}.py (teacher output format, label
  schema `owngrd-labels-v1`, eligibility Gate). Reuse their helpers (rle_decode, atomic writes, Gate).
- Reference code (read, copy what helps, never import from these paths at runtime):
  /scratch/jjyeung/orch_n30/tree_rebuild/work/base/tree_b01ce449/student_pilot/mask_grounding_head.py (MDG decoder:
  resnet18 stem, point-sampled focal/dice mask loss, _DecoderBlock; its _Attention lives in grounding_head.py in the same
  directory), .../reread.py (Qwen ViT re-read, TAP_LAYERS 9,17,25,27),
  /scratch/jjyeung/orch_n30/b05_owngrd/work/own_probe/work/own_feats/core.py (pack_qwen/unpack_qwen, Qwen3_5VisionModel
  load and tap hooks) and names.py (name embedding from frozen embed rows).

## Inputs (all on this node)
- Frozen Qwen3.5 ViT + embedding rows of the step-544 export: work/m544sub/sub/subset.safetensors (keys `model.visual.*`
  and `model.language_model.embed_tokens.weight` [248320,4096] bf16; sha256 in SHA256SUMS there); vision config in
  work/from118/t0bundle/base/config.json (`vision_config`: depth 27, hidden 1152, patch 16, temporal 2, merge 2);
  tokenizer files in the same directory. ResNet-18 stem weights work/from118/weights/resnet18-f37072fd.pth.
  (work/ = /scratch/jjyeung/orch_n30/b05_owngrd/work)
- Teacher manifest work/manifests/TEACHER_K1.json (286 captures, 32 frames each at 640x480 or 480x640, names with roles,
  GT raster path + sha). GT rasters (inst [32,h/2,w/2] int32, -1 unlabelled; ids; labels; valid) under work/gt/x/.
- Frames for 12 captures under work/frames/<sha[:2]>/<sha>.png (list: work/inv/frames12_caps.json).
- Real teacher labels do not exist yet (the GPU teacher pass is pending). For tests, make teacher output with the stub
  (`python -m owngrd.teacher --stub`) and labels with `python -m owngrd.labels`, on a 12-capture manifest whose frame
  paths point at work/frames (see small_manifest in code/tests/test_teacher.py). Everything must accept real labels
  unchanged.

## Build (modules in owngrd/)
1. `vit.py`: load the frozen Qwen3.5 vision model from subset.safetensors + config (strict load, requires_grad False,
   eval, record a sha256 over the loaded state); `taps(frames, size_hw)` returns the 4 tap maps (blocks 9,17,25,27,
   one-based) [F, gh, gw, 1152] at patch resolution (duplicate each frame for the temporal patch, as core.py does) and the
   merged final tokens [F, gh/2, gw/2, 1152]. Re-read size is a parameter (default 480x640 landscape; portrait frames
   use 640x480). `name_query(names)`: token embeddings of normalized names from the frozen embed rows (tokenizer from
   t0bundle), padded [N,P,4096] + mask; hash-pin the rows used. A per-frame feature cache (fp16, keyed by frame sha +
   ViT sha + size) on /scratch is optional but must be exact.
2. `head.py` (~50M trainable parameters in total; report exact counts per module):
   - Presence head (~2M): over ALL frames of the clip (frame count is a parameter: 32 and 64 must work) from merged
     tokens, conditioned on the name query -> per-frame presence logit + clip logit. At inference it shortlists 4 frames
     (top-4 with a minimum slot separation of 2).
   - Decoder OGD (~45M): memory = projected ViT taps (learned tap mix) + resnet18 stem at stride 4/8 (MDG style) +
     2D/frame position; per (name, frame) 16 instance queries + 1 presence token, initialised from the name query;
     4 blocks; per query: match logit, mask logits at stride 4, box (cxcywh, normalized), IoU estimate, 128-d
     L2-normalized identity embedding. Score = sigmoid(presence token) x sigmoid(match).
   - Selector (~3M): listwise over at most 5 clip candidates plus "none". Candidates: greedy cross-frame clustering of
     per-frame query outputs with score >= 0.2 by identity-embedding cosine (threshold in config); candidate features =
     max/mean score, support frames, presence, mean IoU estimate, embedding coherence. Top-5 by max score.
3. `losses.py` (design 3.2, weights in config): Hungarian matching (scipy) of queries to target instances per frame;
   targets = POS masks (teacher mask resized to stride 4) and MISS rasters (GT raster of the instance, flagged
   low-resolution, weight labels.MISS_WEIGHT); focal BCE + dice on 12,544 sampled points (MDG settings); match-score
   focal BCE (matched=1; queries overlapping a HARDNEG proposal at IoU>0.5 =0 at that row's weight; other unmatched=0);
   presence BCE on frame labels where `presence` is not None; clip BCE on `clip_presence` where not None; box L1+GIoU;
   supervised-contrastive identity over matched queries keyed by GT instance id across the clip's frames (negatives:
   other instances and HARDNEG instances); selection listwise CE (target = the candidate covering the GT instance in a
   frame with mask IoU >= 0.5, else "none" when the clip label is 0; skip and count names with several GT instances in
   the clip); score distillation BCE to teacher presence for frames whose presence label is None and for names whose
   role is confuser/absent. Every term returns a finite value (zero when its targets are empty) and is logged separately.
4. `data.py`: items = (capture, name). Decoder frame choice in training: up to 4 frames, at least one POS frame when the
   name has any, plus hard frames (teacher presence > 0.5 with label 0 or None) and random fill, seeded per
   (epoch, item). Room split: K1 `heldout` captures never train; among `train` captures hold out ~10% of ROOMS
   (deterministic hash of the room) as training-room validation. The dataset calls Gate.admit on every capture it reads,
   refuses a manifest whose gate digest differs from its receipt (as teacher.py does), and refuses held-out captures in
   the train split. Frame count (32/64) flows from the manifest.
5. `train.py`: AdamW, warmup+cosine, bf16 autocast on CUDA only, grad clip, validation every N steps reporting the
   design 3.4 stop-rule metrics: candidate recall@5 (GT instance covered by a top-5 candidate with IoU>=0.5 in some
   frame), mask IoU of matched POS, on-target share, false presence on ABSENT pairs at 85% coverage; the stop rules
   (fail-fast at step 600: recall@5 < 70% or IoU < 0.44; plateau; kill rule; hour cap) as a function returning
   CONTINUE/STOP with a reason. Exact resume: checkpoint = model, optimizer, scheduler, RNG states (python, numpy,
   torch), data cursor, stopper state, config hash, label-set hash, ViT sha; resuming from step k reproduces the
   uninterrupted run bit-exactly on CPU. Refuse to resume on a config/label/ViT hash mismatch. Logs as JSONL.
6. `export.py`: save the trained head (safetensors + meta JSON with all hashes) and load it back.

## Tests (code/tests, CPU, each under 2 minutes, none writes a real-size checkpoint)
- tiny-config full path: stub labels on >= 3 captures -> data -> head forward -> every loss term finite, and nonzero
  where its targets exist -> 20 optimizer steps decrease total loss.
- real ViT first batch: load the real frozen ViT from subset.safetensors on CPU and run one real batch (1 capture,
  2 names, 4 frames at the default re-read size) through vit -> head (real config) -> losses; assert shapes and
  finiteness; record seconds and peak RSS. It may be skippable by env var, but run it.
- exact resume (tiny config): 10 steps straight vs 5 + checkpoint + resume 5; losses and parameters equal exactly.
- eligibility: data refuses a manifest holding a dev-S1 capture, a withheld-80 capture, a benchmark capture (one test
  each; take examples from work/auth/DEVS1_MANIFEST.json, WITHHELD_ROOMS_80.json with CAPTURES.json, and
  BENCH_SCENE_EXCLUSIONS_v2.json; see code/tests/test_eligibility.py) and a `heldout` capture in the train split.
- frame count: presence head runs on 32 and 64 frames.
- selector: candidate clustering + listwise target on a synthetic case.

## Deliver
Code + passing tests (paste the pytest summary), `code/HEAD_README.md` (short: modules, config, CPU first-batch
command, pilot command template with --hours cap, log fields, parameter counts), and `tmp_codex/BUILD_REPORT.json`
(test results, parameter counts, real-ViT first-batch seconds and RSS, sha256 of every file you wrote). Implement the
design; do not judge it. List every choice you made that this brief does not specify.
