# Step-400 reader on trinity-2-28

This kit reruns the first 50 items of read A from Orchard job **173060** in OFF mode. It pins A10b package `a15_cot_apdc76460c3a164`, step **400**, run `6ed2c7aa`, and artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The sealed reader, preparation code, package configuration and item order remain unchanged.

Place the complete kit at **`/scratch/jjyeung/orch_n30/reads228/kit2`**. This delivery selects kit2 in STAGE_PLAN for the package's `a/6`; the unchanged unpacker also requires its output inside the kit. The coordinator verified all 21 input/runtime archive parts in `reads228/dl/` against their pins at 18:37Z on 2026-11-19. [MISSING.json](MISSING.json) retains their original source provenance and exact local pins. The kit verifies every SHA256 itself, never trusts `.sha_ok` alone, and never fetches.

Stage on trinity-2-28 before selecting a free card:

```bash
date -u
bash /scratch/jjyeung/orch_n30/reads228/kit2/coordinator228.sh --stage-only
```

All eight cards were occupied at the coordinator's check. Wait for a free card, then run once with a chosen index or UUID:

```bash
date -u
bash /scratch/jjyeung/orch_n30/reads228/kit2/coordinator228.sh --run-only \
  "$CARD" /scratch/jjyeung/orch_n30/reads228/runs/a400check1
```

The output directory must be fresh. Any refusal after the run directory exists needs a fresh run name. Do not retry a failed or killed command automatically. The coordinator checks the run-name characters before staging; the launcher also applies the sealed `opaque()` rule to the entire output path before its stage check. Names containing reserved substrings, such as `h1`, `sam`, `head`, `own`, `room`, or `model`, refuse immediately.

`--stage-only` verifies runtime pins, extracts, installs code, probes the namespace, prepares, checks staging and probes operator imports. It never queries a GPU, takes a UUID lock or creates a run directory. `--run-only` revalidates staging and operator imports, gates one card, runs 50 items, compares, unpacks and writes the corpus-ingest receipt. Each step prints `date -u` and stops on failure. The two-argument invocation remains a combined stage-and-run command.

**Staging uses private runtime and logical roots.** Every runtime member stages under `reads228/private_rt/` with its archive-relative `sj/`, `m/` or `x/` layout. Pass 1 authenticates all parts and headers across all three archives, hashes file bodies, compares existing members, and rejects unknown namespaces, unsafe paths/links, unsupported types and topology conflicts before any runtime member is created. Pass 2 extracts only after the full preflight succeeds. Matching existing members retain their bytes, inodes, modes and modification times. The two `x/` helpers are recorded in STAGE_CHECK.json and never bound or executed. The kit extracts its own input archives and sealed source under `/scratch/jjyeung/orch_n30/reads228/private/b01ec87a6f29b/`. Inside the package namespace, that directory is bound at `/scratch/jjyeung/b01ec87a6f29b`. The other lane's shared `d/k` and `d/s` are never read, modified or counted as this kit's inputs. The private SAM3 comes from a2.tar. Extraction uses `--skip-old-files`, checks every member's size/hash, and refuses unexplained files in this kit's destinations. Extraction logs live under `reads228/extraction_logs/`.

**The package interpreter runs the operator.** Native CPython at `private_rt/sj/uv-python/cpython-3.12.13-linux-x86_64-gnu/bin/python3.12` performs stdlib stage, gate and comparison work. The package's own `orchard_job.namespace` receives `private_rt` and supplies its sj/fsw/m-ap/uv binds; the kit selects root-owned `/usr/bin/bwrap` 0.4.0 and adds the private logical-root bind plus narrow kit/control/output binds. It never binds the private runtime root or its `x/` helpers into the namespace. The unchanged `d/v/py` executes preparation, the import probe and the sealed operator through the adapter. The worker inherits that namespace, runs under the authenticated package `d/q/vnice.sh`, and has no nested bwrap. No policy file is read from `/data3`. LOCAL_RUN records the namespace, both bwrap identities, operator interpreter/probe and package policy paths. See [ENVIRONMENT.md](ENVIRONMENT.md).

Before any snapshot, idle gate, UUID lock or run directory, the operator probe imports `e2e_reader.perception_memo`, `h1eval.h10.launch`, `h1eval.items`, `h1eval.modes` and `h1eval.cli` using the exact namespace/interpreter command used for the operator. A failure records `STAGE/OPERATOR_PROBE.json` and refuses with exit code 2. No authenticated runtime member, settings byte, logical path or `pyvenv.cfg` is rewritten. There is no native-site-directory fallback.

Runtime extraction records every member's name, type, size and link. [RUNTIME_LISTS.json](RUNTIME_LISTS.json) summarizes the three supplied lists: 115,837 headers and 10,371,055,588 file-content bytes. The registry in STAGE_PLAN links each namespace to package receipts and its in-namespace path. Exact header digests also pin membership to the coordinator lists. STAGE_CHECK includes those lists, verifies the paths/modules needed by sealed preparation, checks exact framework versions and audit-root coverage, and rejects unexplained files before preparation. It also retains runtime inventory when a stage check refuses. Runtime expansion is capped at 40 GB; staged footprint must stay below 145 GB, leaving 5 GB below the 150 GB limit. Free scratch must remain at least 200 GiB. These limits do not claim a measured target footprint.

After staging, the direct handoff also works:

```bash
date -u
bash read228.sh A10b "$CARD" --items 50
```

The gate requires two readings at least 300 seconds apart, each below 100 MiB with no process, the same UUID, and an RTX 6000 Ada with 48,000–50,000 MiB. Its lock coordinates this kit; another program can still take the card afterward. The worker runs under the pinned vnice/terminator scripts in its own process group. The first OOM stops without retry, writes OOM.json and returns 42; both `out of memory` and `alloc_failed` RuntimeErrors count as OOM. All wrappers set HOME, XDG directories, TMPDIR and framework caches on local scratch. The cluster terminator's `/tmp/terminator` file is the mandated exception.

A successful prefix has **50/636**, `SUMMARY.failure=null`, and no FAILED.json. EXIT.status remains FAILED because the full read is incomplete. The unchanged unpacker authenticates that envelope. Coordinator unpacking writes `kit2/ingest/<run-name>`; [ingest228.py](ingest228.py) uses SUMMARY and the comparison to publish `CORPUS_INGEST.json`. READY_FOR_CORPUS names the unpacked directory for the corpus consumer; this kit does not modify an external corpus database.

SAME_INSTRUMENT requires at least 49 identical answers and all 50 identical call placements, plus equal complete binding and settings dictionaries. Placement is `(index, family, call, served, at_token)`; stage-1 floats remain trace diagnostics. FIRST50 pins reference IDENTITY and every included reference journal environment. Candidate SUMMARY, failure markers, OFF mode, local host, Ada card, journal hosts and a distinct local return ID are mandatory. Differences list their keys. These checks establish consistency, not hardware attestation.

The optional `--on` overlays default OFF and cannot establish the OFF device check. Their supplied consistency issue remains in [SO_READ_CONSISTENCY.json](SO_READ_CONSISTENCY.json).

```bash
date -u
bash tests/run_tests.sh
```

CPU tests hide CUDA and limit threads to eight. The regression suite also runs the native control path with `-I -S -B`, without numpy or torch; its separate operator subprocess has the CPU test environment. GPU worker operations are doubles. Tests write only under the workspace's `work/` tree; READ228_TEST_WORK can select another allowed scratch test directory. [REPORT.md](REPORT.md) contains exact outputs, regression evidence, the complete coordinator command sequence and target-only checks still required.

The coordinator-authorized stage-only invocation from kit2 starts with no private runtime after the reported refusal. It stages the complete private copy and ignores the 443 shared entries left by that refusal. No removal or shared-file reuse occurs. A successful later stage-only invocation verifies and preserves the existing private files, reuses READY.json, and repeats the namespace/import checks. It does not rerun preparation. See [COORDINATOR.md](COORDINATOR.md) for the stage-first sequence and the single card-gated run. There is no automatic retry after failure or termination.

The operator installs the sealed `install_process_guard(out)` before loading the operator or spawning children. The test harness runs bootstrap tests with actual `/usr/bin/python3` 3.6.8 when available and runs both control-boundary suites without site-packages. Full target runtime imports, preparation and Ada/H100 parity remain deployment checks.
