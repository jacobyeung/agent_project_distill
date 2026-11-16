# Reviewed ReVSI reader on Trinity

`rv-stage`, `rv-proof`, `rv-read`, and `rv-compare` wrap the reviewed official999 reader. Production covers 679 items and 261 tier-32 videos, with B2048 primary and ON16k/B4096 secondary. The reader, processor checks, generation, budget derivation, and scorer retain the bytes shipped in Orchard job 170037. The wrapper never edits answers.

The supported model is the pinned step-544 export. **D0 requests refuse:** the kit's `official_adapter.py` hardcodes the artifact SHA256 and step 544 in both binding and launch. Selecting a D0 export requires a reviewed change to that contract. The wrapper first applies build_t6's artifact lineage admission, then enforces the kit's narrower identity.

The build session runs CPU fixtures only. The commands below are for an operator after heavy-I/O approval and card coordination. They perform no SSH, network, Git, or Slurm submission. The kit consumes `SLURM_JOB_ID` as a local run token; no scheduler is invoked. A killed or failed command must not be retried automatically.

## Operator sequence

Run from trinity-1-3, lane trin_read3. Use fresh output directories and tokens. A token is one letter followed by 8–32 lowercase hexadecimal digits.

```bash
cd /scratch/jjyeung/orch_n30/trin_read/build_rv
ROOT=/scratch/jjyeung/orch_n30/trin_read/root
ARTIFACT="$ROOT/fsw/ap/8865619b/runs/469ddece/m544/artifact.json"
SHA=1d6eeb28f51688c414cfe069d3d9da2f9308a4d8cc7b80261b14a5973c5f15ef

./rv-stage --root "$ROOT" --tar ../dl/rv_media.tar

./rv-proof --root "$ROOT" --artifact "$ARTIFACT" --sha256 "$SHA" \
  --frames 32 --gpu 0 --token p2026111601 --out "$ROOT/rv_packets/p2026111601"

./rv-read --root "$ROOT" --artifact "$ARTIFACT" --sha256 "$SHA" \
  --frames 32 --gpu 0 --token r2026111601 --out "$ROOT/rv_packets/r2026111601" \
  --proof "$ROOT/rv_packets/p2026111601"

./rv-compare \
  --a /scratch/jjyeung/orch_n30/evalx27/work/kit_revsi/build/a348bc58686 \
  --b "$ROOT/rv_packets/r2026111601" --out "$PWD/COMPARE_170037.json"
```

System Python 3.6 can run the boundary CLI. The namespace uses the staged CPU environment and the kit's isolated vLLM interpreter. `--bwrap` defaults to `/usr/bin/bwrap`; the pinned Orchard bwrap cannot substitute for the host executable.

`rv-stage` accepts only an uncompressed tar of exactly the manifest's 261 regular files. It rejects extra/missing/duplicate members, links, devices, traversal, size mismatches, and hash mismatches. It never follows the manifest's `/data2` source fields. Every video must pass its SHA256 check before the receipt is written. An existing or partial destination causes refusal. The command preserves the 200 GiB free-space floor.

Videos live at `root/rv_media/`. A read-only bind presents them as `/scratch/jjyeung/rvmedia`; the kit reads that path through `spec.inputs.video_root` and `roots.revsi_video_root`. No `/home` or `/data*` media copy occurs. `RECEIPT.json` records every member pin and the archive hash. Proof/read rehash the staged videos before using them. Neither command waits for downloads.

`rv-proof` invokes the kit's complete phase A: decode all 261 clips, verify frame plans, run its accepted 20-item prompt-byte/real-processor check, and exercise two items per category through the kit's fake engine. Thus the proof report has **10 synthetic generation items**, while `PARITY.json` has **20 real processor checks**. These are different checks. The unrelated dev-S1 phase B is disabled, matching the reviewed proof command. Proof scores are not model performance. Production requires this proof's authenticated successful packet for the same payload and artifact.

`rv-read` invokes the same unmodified chain in production mode. It retains max_seqs 32, inflight 16, greedy generation, and all three arms. Model copies are made by the kit itself; the runner reserves 45 GiB in addition to the 200 GiB free-space floor. It neither uses hard links nor changes engine settings to fit memory.

## Runtime, sandbox, and completion

All fields of the kit's `ORCHARD_ASSETS.json`, including every runtime archive part hash, match the staged build_t6 configuration. The kit requires vLLM 0.32.0 in `/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/19252904/e`, which is the staged environment. A different asset pin or observed vLLM version refuses execution. `RUNTIME_FIT.json` records the static evidence; each run performs build_t6's CPU import probe before GPU admission.

The namespace retains build_t6's root mappings, isolated network, private caches/tmp/shm, host bwrap checks, and read-only llguidance stub overlay. It binds this build at `/trinity-build` and `/trinity-rv`, and the exact payload at `/scratch/jjyeung/rvkit`. The stub remains bound only inside the sandbox and raises on any call. Successful execution requires import evidence and **zero generation-time calls**. The probe's deliberate failure test has a separate log.

The wrapper runs through `/data3/shared/scripts/vnice/vnice.sh` with one selected card. Admission requires two readings 60 seconds apart, the same UUID, at least 40 GiB total, less than 100 MiB used, and no compute process. `CARD.json` retains both readings, including failed admission evidence. The operator selects the intended 48 GB card. `SANDBOX.json` records binds, argv, bwrap, stub, driver libraries, glibc, and runtime probe evidence. `MEMORY.jsonl` samples usage; it does not establish an exact peak.

A packet contains the kit's `a0/results/0/` journals, `report/{B2048,ON16k,B4096}.json`, `FRAME_PLAN.json`, `COMPLETE.json`, and wrapper `EXIT.json`, `CONFIG.json`, `SANDBOX.json`, `CARD.json`, `PROBE.json`, `LLGUIDANCE.json`, and logs. Accept a packet only when **both** the kit's `COMPLETE.json` and `EXIT.json.status == "COMPLETE"` exist. A stub or sampler failure can fail EXIT after the kit writes COMPLETE. EXIT pins the reports, principal journals, configuration, and completion evidence. Partial files remain for inspection; the wrapper deletes nothing.

`rv-compare` accepts either an unpacked packet or an Orchard preparation directory containing `packet/` and `fetched/EXIT.json`. Both inputs must be complete, nonsynthetic, step-544 production packets with all 679 IDs. It checks journal scores against the kit's report rows, reports token equality and first zero-based divergences for every item in each arm, and reports per-category score equality, subtype-weighted category means, and both five-category means. It recomputes no answers and makes no token substitutions. A valid comparison with differing tokens still exits successfully; inspect the equality shares.

## Frames and memory

`--frames` defaults to 32. Each tier-32 clip supplies 32 anchors, duplicated into 64 input frames. This is not a tier-64 read. The supplied media manifest contains only tier-32 clips. `--frames 64` refuses before any GPU query.

A real 64-anchor read needs the tier-64 videos and their pinned manifest, tier-64 question rows, source indices, a decoded frame plan with 64 anchors expanded to 128 frames, and fresh serialized prompt pins and real-processor parity. The evaluator contains tier-64 input hashes, but this adapter and its frame-plan checker require tier 32. New media and reviewed adapter/frame-plan changes are necessary; duplicating the existing 32 frames again does not satisfy that contract.

Job 170037 used 3,111,992 prompt tokens and 119,158 source output tokens. Its visual component was 2,853,312 tokens. At unchanged spatial resolution, 64 anchors would add approximately 2,853,312 visual tokens, bringing prompts to roughly 5,965,304 tokens before extra timestamp/text effects. This is a conditional estimate: processor resizing can change the token count. A measured 64-frame plan and processor run are required for an exact total.

The Orchard generation/staging/merge stage took 7.99 minutes; the recorded chain stages totaled 8.91 minutes on its H100. Trinity 32-frame time and 64-frame time are unmeasured. Doubling anchors does not justify doubling those minutes: generation lengths, prefill, resizing, and GPU throughput differ. `RUNTIME_FIT.json` leaves those costs null rather than inventing a runtime estimate.

The engine uses BF16, max_model_len 49,152, gpu_memory_utilization 0.90, max_num_seqs 32, inflight 16, max_num_batched_tokens 8,192, tensor_parallel_size 1, seed 17, one video and zero images per prompt, and disabled prefix caching. The kit requests 16,384 source output tokens with temperature zero. Other engine options retain the pinned runtime's defaults.

Step-544 has 9,409,813,744 parameters and 18,819,721,016 serialized weight bytes (17.527 GiB). Weights fit within a 48 GiB card's 43.2 GiB engine budget. Full engine fit remains unverified: KV cache, activations, CUDA graphs, and multimodal profiling also consume memory. An OOM must stop the path; this wrapper does not reduce context, batching, or utilization.

## CPU tests

Use a basetemp that does not exist; pytest can delete an existing basetemp.

```bash
cd /scratch/jjyeung/orch_n30/trin_read
PYTHONDONTWRITEBYTECODE=1 kit_src/.venv/bin/python -B -m pytest \
  build_rv/tests/test_*.py -q -p no:cacheprovider \
  --basetemp=build_rv/tests/rv_operator_fresh_01
```

`rv_payload/` is the active payload; `RV_PAYLOAD_PINS.json` authenticates it. The copied build_t6 commands and evidence remain available. `revsi_kit/` and its `RV_KIT_PINS.json` are inactive source evidence and are never imported by these commands. The active production reader is byte-identical to job 170037. See `DIFF.md`, `REPORT_RV.md`, and `RV_SOURCE_EVIDENCE.json` for scope and validation.
