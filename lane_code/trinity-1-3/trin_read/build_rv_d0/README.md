# Reviewed ReVSI reader on Trinity

`rv-stage`, `rv-proof`, `rv-read`, and `rv-compare` wrap the reviewed official999 reader. Production covers 679 items and 261 tier-32 videos, with B2048 primary and ON16k/B4096 secondary. The reader, processor checks, generation, budget derivation, and scorer retain the bytes shipped in Orchard job 170037. The wrapper never edits answers.

The reader supports the pinned step-544 export and receipt-verified D0 exports from lineage `8865619b`, run `359fcc3c`, at a positive step. D0 uses a read-only adapter overlay with exactly four identity substitutions. All staged payload bytes remain pinned. See the D0 addendum below.

The build session runs CPU fixtures only. The commands below are for an operator after heavy-I/O approval and card coordination. They perform no SSH, network, Git, or Slurm submission. The kit consumes `SLURM_JOB_ID` as a local run token; no scheduler is invoked. A killed or failed command must not be retried automatically.

## Operator sequence

Run from trinity-1-3, lane trin_read3. Use fresh output directories and tokens. A token is one letter followed by 8–32 lowercase hexadecimal digits.

```bash
cd /scratch/jjyeung/orch_n30/trin_read/build_rv_d0
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
  build_rv_d0/tests/test_*.py -q -p no:cacheprovider \
  --basetemp=build_rv_d0/tests/d0_operator_fresh_01
```

`rv_payload/` is the active payload; `RV_PAYLOAD_PINS.json` authenticates it. The copied build_t6 commands and evidence remain available. `revsi_kit/` and its `RV_KIT_PINS.json` are inactive source evidence and are never imported by these commands. The step-544 production reader is byte-identical to job 170037. D0 overlays only the adapter identity constants. See `DIFF.md`, `REPORT_RV_D0.md`, and `RV_SOURCE_EVIDENCE.json` for scope and validation.


## D0 addendum

Run these commands only after the export has completed `python3 trinity_read.py stage-export` and media staging has completed. The existing CPU-only build session does not run them. Choose a positive staged step and fresh tokens/output directories. The SHA below comes from the stage-export receipt; the CLI cross-checks it against the artifact and the checker's recorded identity.

```bash
cd /scratch/jjyeung/orch_n30/trin_read/build_rv_d0
ROOT=/scratch/jjyeung/orch_n30/trin_read/root
STEP=100  # Choose the actual staged positive optimizer step.
ARTIFACT="$ROOT/fsw/ap/8865619b/runs/359fcc3c/m$STEP/artifact.json"
RECEIPT="$ROOT/exports/359fcc3c_m$STEP/RECEIPT.json"
SHA=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["artifact_sha256"])' "$RECEIPT")

./rv-proof --root "$ROOT" --artifact "$ARTIFACT" --sha256 "$SHA" \
  --frames 32 --gpu 0 --token p20261116d001 --out "$ROOT/rv_packets/p20261116d001"

./rv-read --root "$ROOT" --artifact "$ARTIFACT" --sha256 "$SHA" \
  --frames 32 --gpu 0 --token r20261116d001 --out "$ROOT/rv_packets/r20261116d001" \
  --proof "$ROOT/rv_packets/p20261116d001"
```

Admission requires `exports/359fcc3c_m<step>/{RECEIPT,CHECK,COMMAND}.json`. The receipt must be complete, and its path, run, step and artifact hash must match the request. Its checker result must match `CHECK.json`, with the unchanged checker/common source hashes in `COMMAND.json`. Both full and header-only staging receipts are accepted. A header-only staging receipt does **not** establish weight integrity: the adapter runs the unchanged full checker in both bind and launch, and completion requires its `VERIFIED` result. Missing or inconsistent receipts, other lineages/runs, nonpositive or mismatched steps, mismatched hashes, and links anywhere in the export tree refuse.

Each D0 packet stores `adapter_overlay/official_adapter.py` and `ADAPTER_OVERLAY.json`. The latter records the original adapter SHA, overlay SHA, all four exact old/new source snippets, the selected identity, a copy of the stage receipt, and hashes of its checker evidence. The sandbox binds that one file over `/scratch/jjyeung/rvkit/reader/official_adapter.py` after binding the immutable payload. Both the import probe and reader namespace receive the overlay. The wrapper verifies its deterministic bytes before execution and after completion; the namespace entry verifies the mounted SHA before entering the chain. `CONFIG.json` and `SANDBOX.json` retain the overlay receipt, and `EXIT.json` hashes it, the overlay file, `PROOF_SCOPE.json`, admission evidence and the bound request/code pins. The kit also records the effective adapter SHA in its own code pins.

D0 proof still runs the kit's unchanged 20-item prompt-byte/base-processor check and 10-item synthetic generation exercise. The prompt check's dry bind retains the kit's step-544 reference; it does not load those learned weights. C1 model staging copies processor, tokenizer and model metadata from the same pinned base. `PROOF_SCOPE.json` separates these model-independent checks from selected-export validation, staging and metadata-dependent processor checks. It explicitly excludes learned-token parity, model accuracy and real GPU fit. Production requires a successful proof for the same artifact, staging evidence and deterministic overlay.

The selected optimizer step appears in `CONFIG.spec`, `ADAPTER_OVERLAY.json` and `a0/request.json.reader`. The untouched chain writes the literal `544` in `AUTHORIZATION.json.step`; treat that field as the kit's protocol label, not the selected optimizer step. `PROOF_SCOPE.json` records this limitation. No chain, prompt, processor, media, cohort, batching, scorer or runtime file is patched. The adapter's original error text also retains “Step-544 artifact differs.”

For the pinned step-544 identity, the wrapper creates no adapter overlay and keeps the original configuration, namespace behavior and packet hash set. `rv-compare` remains restricted to step-544 production parity. D0 support does not enable 64 anchors or change any memory setting.
