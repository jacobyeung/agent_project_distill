# Step-400 reader on trinity-2-28

The kit reruns the first 50 items of read A from Orchard job **173060**, package `a15_cot_apdc76460c3a164`, in OFF mode. It pins step **400**, run `6ed2c7aa`, artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The delivered A10b source and package bytes are authenticated; the adapter changes no sealed reader file.

**Deployment needs the 13 runtime parts in [MISSING.json](MISSING.json).** Their total is 10,497,433,600 bytes. The supplied staging inventory covers the model/input archives, SAM3, and package `a/6`; it does not cover the base Python/torch runtime. The kit performs no transfer, download, installation, SSH, or scheduler operation. All eight cards are occupied according to the dispatch; no card is selected by this kit.

## Coordinator sequence

Place the delivered kit at `/scratch/jjyeung/orch_n30/reads228/kit`, with its `A10b/package/` and `A10b/src/`. The coordinator must supply the exact local targets listed in MISSING.json before extraction can proceed. See [ENVIRONMENT.md](ENVIRONMENT.md) for the archive and interpreter mapping.

After choosing a card and a fresh output directory, run:

```bash
date -u
bash /scratch/jjyeung/orch_n30/reads228/kit/coordinator228.sh \
  "$CARD" /scratch/jjyeung/orch_n30/reads228/runs/a400check1
```

`CARD` must contain the chosen index or UUID. Do not use this command as a polling or relaunch loop. [coordinator228.sh](coordinator228.sh) contains the exact extract → relocate → install code → prepare → stage check → card gate → 50-item run → compare sequence and prints UTC time at every step. It stops at the first refusal. It uses `/usr/bin/python3` 3.6.8 only for stdlib staging, then `/scratch/jjyeung/b01ec87a6f29b/d/v/py` for control and worker execution. It uses the wrapper's Orchard flags, `-B -I`.

Input archives extract to `/scratch/jjyeung/b01ec87a6f29b/d`, matching their package destination `sj/b01ec87a6f29b/d`. Runtime `sj/` members map to `/scratch/jjyeung/`; `m/ap/` and `fsw/` members map beneath `reads228/runtime/`. Explicit `--relocate-runtime` rewrites only recognized Orchard absolute prefixes in `v/py`, `v/boot.py`, and the base environment's `pyvenv.cfg`. It saves authenticated originals and records both hashes. Runtime member lists and binaries are absent here, so the target import probe remains mandatory.

Preparation calls the sealed CPU entry. A completed READY receipt is rechecked without rerunning preparation. An incomplete restore refuses a relaunch. The stage check verifies source and weight pins, policy script pins, extraction/relocation receipts, exact package versions, module containment in the reader's audit roots, and disk budgets. Preparation and stage verification precede every card query.

The card gate requires two readings at least 300 seconds apart, each below 100 MiB with no compute or graphics process, the RTX 6000 Ada name, and 48,000–50,000 MiB total memory. It holds a UUID lock and fails closed. It cannot reserve a card against other programs.

## Run and return

After successful staging:

```bash
date -u
bash read228.sh A10b "$CARD"                 # defaults to 50 items
bash read228.sh A10b "$CARD" --items 50
```

Each invocation creates a fresh run directory and prints the return location. For a fixed output path use `bash run228.sh A10b "$CARD" /scratch/jjyeung/orch_n30/reads228/runs/a400check2 --items 50`.

The adapter calls the sealed operator and `runner.run(..., launcher=...)`. The sealed runner writes `metadata/reads/0/metadata/IDENTITY.json`, `projection.json`, and `a/30.json`. The return includes allocation/storage metadata and root logs. A clean 50-item prefix remains **50/636** with no full-read COMPLETE marker; the adapter returns exit 0 when the requested prefix finishes. The unchanged Orchard unpacker accepts that partial envelope. A failure before the first journal may produce a receipt that the unpacker refuses.

The worker runs under the SHA256-verified vnice and terminator scripts in its own process group. The control process can write a failure receipt when that group exits; a kill of the control process itself cannot guarantee a receipt. USER and LOGNAME are `jjyeung`; HOME, CUDA, matplotlib, Torch, Triton, and Hugging Face caches stay in the run directory. The first OOM writes telemetry, stops without retry, and returns code 42. Per-item allocated/reserved CUDA peaks and one-second nvidia-smi telemetry stay beside the return.

`--on` is optional and default OFF. It requires the separately verified so_read overlays; the supplied overlay inconsistency remains documented in [SO_READ_CONSISTENCY.json](SO_READ_CONSISTENCY.json). ON runs cannot establish the OFF device check.

## Compare

```bash
date -u
bash compare228.sh /scratch/jjyeung/orch_n30/reads228/runs/a400check1/ret \
  --orchard reference \
  --out /scratch/jjyeung/orch_n30/reads228/runs/a400check1/COMPARE.json
```

SAME_INSTRUMENT requires 49 or 50 identical extracted answers and identical call placement on all 50 items, with the authenticated A10b prefix/export and OFF settings. Placement is exactly `(index, family, call, served, at_token)`. Stage-1 floats remain in trace diffs and do not enter the placement gate.

The candidate must have `LOCAL_RUN.json` with backend `trinity-local`, host `trinity-2-28`, and mode `OFF`; `CARDS.json` must name RTX 6000 Ada; every journal environment host must begin with `trinity-2-28`; RETURN_ID must differ from job 173060. Orchard-vs-Orchard is ineligible. Output paths must resolve beneath `/scratch/jjyeung`. These are provenance consistency checks, not cryptographic hardware attestation.

## CPU verification

```bash
date -u
bash tests/run_tests.sh
```

Tests write only under the workspace's `work/` tree. `READ228_TEST_WORK` can select another scratch `work/` directory. The test runner uses the dispatch CPU Python 3.12 plus the installed system Python 3.6.8 for bootstrap tests, hides CUDA, and limits CPU threads to eight. See [REPORT.md](REPORT.md) for exact outputs, failed regressions on the preserved kit, patch validation, and deployment limits.
