# A4 reader on trinity-2-28

This kit runs A4's sealed reader on one RTX 6000 Ada card and compares its first 50 items with Orchard job 172744. It has CPU validation only. **No Ada fit or same-instrument result has been measured.**

**A4 requires m200, step 200.** Its sealed `9.json` and authenticated return agree on that export. The `package/a/0.json` template names m544, but A4 rejects that export. The supplied `a/1.json` and `a/export.json` placeholders are filled from the authenticated return in this delivery. Every sealed package member and all 927 source files remain unchanged. See [REFERENCE_PROOF.json](REFERENCE_PROOF.json) and [STAGE_PLAN.json](STAGE_PLAN.json).

The runtime environment, weights, and frames are not in this delivery. The stage plan lists exact known sizes, hashes, and destinations. The IO-governor README and pinned `q/env.json` bytes were absent from the mirror. The coordinator must resolve the marked TODOs before deployment.

## Cont_ops command

After the authorized staging and preparation below, run this **on trinity-2-28**:

```bash
/scratch/jjyeung/a4228/kit/read228.sh /scratch/jjyeung/a4228/kit/A4/package 0
```

Replace `0` with one card index or UUID. The command verifies staging, requires two idle readings five minutes apart, runs all 636 items with extensions OFF, packages a return, and invokes A4's unchanged unpacker. Its final JSON names the accepted output. A failure exits nonzero. Do not ingest a directory merely because it exists; require unpack exit status 0 and inspect its completion status.

`READ228_CONTROL_PYTHON` may select a staged Python 3.12 control interpreter. It defaults to `/scratch/jjyeung/envs/p1cpu/bin/python`. The reader itself uses the package's pinned launcher, `/scratch/jjyeung/b01ec87a6f29b/d/v/py`. That launcher must resolve to a CUDA environment under `/scratch/jjyeung/envs`. Do not substitute this node's CPU test torch for the reader environment.

## Stage once

1. The coordinator authorizes heavy IO and plans the transfer with an admin: the required archive set exceeds 30 GB. Obtain `/data3/jjyeung/orch_n13_20261026/io_governor/README.md` and fill the register/launch fields in [STAGE_PLAN.json](STAGE_PLAN.json). **TODO: the mirror has no governor README, so this kit deliberately supplies no guessed register/launch command.** Use one registered sequential stream, at most 8 MB/s through the head node, and honor the aggregate 18 MB/s user limit. A killed transfer is not retried without the user's answer.
2. Place this delivery at `/scratch/jjyeung/a4228/kit` on 2-28. Transfer one archive over the approved compute-node InfiniBand route. The agent that built this kit performed no transfer. The stage plan's `Trinity_delivery` sources name the files to include; package/source content is already bundled here.
3. Place each `input_archives[].parts[]` and `runtime_archives[].parts[]` at its exact `target`. The plan retains original Orchard source paths as provenance. These paths are never opened by the reader on Trinity. `stage228.archive_map` maps archive sources to node-local targets before extraction. The sealed preparation and runner receive their existing `package`, `output`, `settings`, `export`, `binding`, and `python` configuration fields; no reader source is rewritten and no `/project` mount is required.
4. Stage the authenticated template runtime closure under `/scratch/jjyeung/envs` and its required local Python base-runtime path. **TODO: inspect the authenticated runtime archives and `a3.tar`'s `q/env.json`; the mirror lacks their contents.** Preserve the `v/py` launcher and `v/site` overlay contract. The package requires exact receipt versions of torch, torchvision, transformers, and scipy, with transformers at least 5.12. The dispatch's torch 2.11/CUDA 12.9 statement is not a recovered A4 environment receipt. Do not install or download packages during a read. See [ENVIRONMENT_TODO.md](ENVIRONMENT_TODO.md).
5. Extract the input archives and install the sealed code using the commands below. All paths stay on `/scratch`. A preexisting regular file is reused only if its bytes match the authenticated stream; mismatches stop extraction without overwriting it. Existing SAM3 therefore receives a full hash/byte check, not a size-only exemption. The extractor refuses archive links for coordinator inspection. It never deletes files or joins the four export parts into another 21.58 GB file.

```bash
cd /scratch/jjyeung/a4228/kit
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
export OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false
PY=/scratch/jjyeung/envs/p1cpu/bin/python
nice -n 10 "$PY" -I -s -B stage228.py A4/package --install-code
nice -n 10 "$PY" -I -s -B stage228.py A4/package --extract-inputs
nice -n 10 "$PY" -I -s -B stage228.py A4/package --prepare --out /scratch/jjyeung/a4228/PREPARED.json
```

`--prepare` calls the unchanged `orchard_h10.entry` action 0. It verifies framework versions and restores the pinned model without a GPU. It refuses an existing restore; subsequent reads run the check without `--prepare`. Do not automatically rerun failed or killed preparation.

The planned peak is **120,716,601,141 bytes (120.72 GB, estimate)**. This includes 32,613,048,320 bytes of input archives, their pinned 32,606,119,221 expanded bytes, 10,497,433,600 bytes of template archives, a 40 GB runtime expansion allowance, and a 5 GB operating allowance. Runtime expansion is unmeasured. Preflight counts the named local trees and requires at least 5 GB below the 150 GB cap, plus 200 GiB free on scratch. Keep m544 out of this A4 deployment; staging both exports would invalidate this budget. Runtime extraction and transient-cache bounds remain deployment checks, not measured facts.

## Run and compare the first 50

```bash
cd /scratch/jjyeung/a4228/kit
./run228.sh A4/package 0 /scratch/jjyeung/a4228/prefix50 --items 50
./compare228.sh /scratch/jjyeung/a4228/prefix50/ret \
  --orchard reference --out /scratch/jjyeung/a4228/prefix50/COMPARE.json
```

Use a fresh output directory. The bundled `reference/` contains the first 50 real Orchard records; [REFERENCE_PROOF.json](REFERENCE_PROOF.json) binds them to job 172744's return archive. You may pass the complete original A4 `ret/` directory instead. The comparator authenticates the baseline prefix, checks item order, export, operator, source bindings, and OFF configuration, then reports equality counts and a per-item diff.

The fixed ruling is **49 or 50 identical answers and identical call placement on all 50**. Calls must match in order, literal arguments, service status, and token position. Answers use A4's exact `answer_text` extraction, with no numerical tolerance. Trace equality is reported separately; it does not add a criterion to the orchestrator's ruling. Trace comparisons exclude only `seconds`, `timings`, `audit`, `perception_memo`, `read_cache`, and `read_profile`; audit violations are still refused. Full-text, token, and every output-field equality count are also reported.

Exit status 0 means `SAME_INSTRUMENT`, 1 means `DIAGNOSTIC_ONLY`, and 2 means a malformed or untrusted input was refused. A 50-item return remains partial: `SUMMARY.json` says 50/636 and there is no `COMPLETE.json`. Only all 636 completed items produce that marker.

## Reader behavior and output

`run228.sh <package> <card> <out> [--items N] [--on]` invokes the original `tower_sequence.run` with a local process adapter. The adapter uses the original `worker_args`, and the worker executes the original `orchard_h10.entry` action 2. A4's type sequence is `[3, 0, 1, 2, 4]`, with one persistent tower generator and shard `0/1`. Item limits use its existing cooperative stop-file hook after the Nth durable journal commit; they do not replace or truncate the item manifest.

OFF preserves A4's `candidates_argmax`, G3T-only perception memoization, call cap, precision, and decoder settings. The adapter does not seed the model, select a different attention kernel, reduce precision, enable offload, or modify reader output dictionaries. The four worker CPU-thread environment values match A4's original runner. Memory observation is an explicit worker switch, separate from the OFF/ON cache switch.

The launcher uses `CUDA_VISIBLE_DEVICES=<selected UUID>` and `/data3/shared/scripts/vnice/vnice.sh`. Both idle readings must show less than 100 MiB and no compute or graphics process. A local UUID lock serializes this kit's launchers; another program can still claim the card after a reading. The kit does not reserve a GPU or stop another user's job.

The sealed five-GPU-hour budget remains a five-hour single-card deadline. A4 stops admitting work 30 minutes before that deadline and abandons an unfinished read 20 minutes before it. Ada may need longer than Orchard; no runtime forecast is asserted. A signal stops admission and lets the current read drain. The first CUDA OOM exits 42 and never triggers a retry or another worker. A hard OS kill can leave diagnostic files without a valid ingestible journal.

Outputs are:

| Path under `<out>` | Contents |
|---|---|
| `ret/metadata/reads/0/metadata/journals/<type>/0/` | Original A4 journals, environment bindings, and per-type summaries. |
| `ret/SUMMARY.json` | Full-plan completion count and requested-prefix status. |
| `ret/COMPLETE.json` | Present only for a successful 636-item return. |
| `return/result.tar.gz`, `return/EXIT.json` | Original A4 return-envelope fields, with truthful `trinity-local` provenance. The numeric ID is local, not a Slurm job. |
| `telemetry/memory.jsonl` | Model-load peak and per-item maximum allocated/reserved CUDA bytes. Peaks reset at each item boundary. |
| `telemetry/nvidia-smi.csv` | One persistent `nvidia-smi -l 1` process records device memory and utilization every second. |
| `telemetry/OOM.json` | First OOM phase, item if known, and available memory peaks. |
| `telemetry/FRAMEWORK.json` | Framework versions, actual GPU, kernel choices, numerical settings, host MaxRSS, and worker status. |
| `RESULT.json` | Return paths and status; the launcher never declares hardware parity. |

For a manually launched prefix run, invoke the unchanged unpacker through the isolated-import wrapper:

```bash
nice -n 10 "$PY" -I -s -B unpack228.py --operator A4 \
  --archive /scratch/jjyeung/a4228/prefix50/return/result.tar.gz \
  --exit /scratch/jjyeung/a4228/prefix50/return/EXIT.json \
  --out /scratch/jjyeung/a4228/kit/accepted50
```

The output must stay beneath the operator's parent directory; this is A4's existing unpack containment rule. The wrapper changes only the Python import path needed by `-I`. It runs the original unpacker bytes.

## ON status

`--on` can activate only the supplied `so_read` loader and cache overlays. It cannot participate in the OFF same-instrument ruling. **The current upstream delivery is inconsistent and ON is unavailable.** [SO_READ_CONSISTENCY.json](SO_READ_CONSISTENCY.json) gives the missing file and hash mismatches. No alternative implementation is substituted.

After the coordinator provides a coherent, reviewed delivery and updates its manifest and extension pins, installation is explicit:

```bash
nice -n 10 "$PY" -I -s -B install_extensions228.py --enable-extensions
./run228.sh A4/package 0 /scratch/jjyeung/a4228/cache_trial --items 50 --on
```

The installer authenticates the three supplied patches and every resulting extension file. The ON profile uses the supplied processor/vision/SAM caches with their 12 GiB host allowance; original reader files remain unchanged. ON still needs its own GPU correctness and memory validation. A failing install leaves its files for inspection and is not silently retried.

## CPU validation

Run `tests/run_tests.sh` on trinity-1-18 with the specified CPU environment. Tests write retained fixtures beneath this workspace; they invoke no GPU, network, SSH, or scheduler. They cover path mapping, pin and occupancy refusals, stream extraction, exact worker arguments, unchanged maker bindings, OOM handling, original-unpacker acceptance, and the fixed comparison ruling. [FRAMEWORK_EVIDENCE.md](FRAMEWORK_EVIDENCE.md) cites the installed torch source. [REPORT.md](REPORT.md) records exact validation results and remaining work.

The additive [patch](patches/01_trinity_adapter.diff) creates `read228/` beside the input A4 tree and changes no existing file. Apply it with `patch --batch --fuzz=0 -p1`, then populate its authenticated assets with `bootstrap228.py --input-A4 <supplied A4 root> --out <patched read228>/A4`. This operation fills only the two unsealed input metadata files from the return. Run the patched `tests/run_tests.sh` through `bash`; executable bits are not encoded in a plain unified diff. The direct delivery already includes these assets and executable wrappers.
