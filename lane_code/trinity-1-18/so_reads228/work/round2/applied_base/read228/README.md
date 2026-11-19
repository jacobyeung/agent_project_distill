# Step-400 reader on trinity-2-28

This kit reruns the first 50 items of read A from Orchard job **173060** in OFF mode. It pins A10b package `a15_cot_apdc76460c3a164`, step **400**, run `6ed2c7aa`, and artifact SHA256 `5083243cfedd2a389dfca579c5452e7d0c73b03a58e1cb7d204292ddd10e67cd`. The sealed reader, preparation code, package configuration and item order remain unchanged.

Place the complete kit at **`/scratch/jjyeung/orch_n30/reads228/kit`**. This exact path is required because STAGE_PLAN pins the package's `a/6` there; the unchanged unpacker also requires its output inside the kit. The coordinator has authorized the 13 runtime parts as staged in `reads228/dl/`. [MISSING.json](MISSING.json) retains their original source provenance and exact local pins. The kit verifies every SHA256 itself, never trusts `.sha_ok` alone, and never fetches.

```bash
date -u
bash /scratch/jjyeung/orch_n30/reads228/kit/coordinator228.sh \
  "$CARD" /scratch/jjyeung/orch_n30/reads228/runs/a400check1
```

`CARD` is one chosen index or UUID. The output directory must be fresh. Do not run this command in a retry loop. [coordinator228.sh](coordinator228.sh) verifies runtime pins, extracts, installs the sealed code, probes the package namespace, prepares, checks staging, gates one card, runs 50 items, compares, unpacks and publishes a corpus-ingest receipt. Each step prints `date -u`; any failed stage stops the sequence. A diagnostic comparison is still unpacked, but cannot produce READY_FOR_CORPUS.

**Shared files are preserved.** `/scratch/jjyeung/b01ec87a6f29b/d/k` and `d/s` belong to `swarm_build`. Input extraction authenticates the archives, lists every conflicting existing member, and uses GNU tar `--skip-old-files`. Every member must match by size and SHA256. Staging refuses with a list of files that neither an archive nor sealed preparation explains. It never moves, overwrites or deletes those files. The coordinator resolves any conflict with that lane.

**The package supplies the namespace.** `/usr/bin/python3` performs stdlib bootstrap work. The staged native CPython 3.12 controls the job outside bwrap. The package's own `orchard_job.namespace` supplies its `sj`, `fsw`, `m/ap` and uv CPython binds; `/usr/bin/bwrap` 0.4.0 executes the unchanged `d/v/py` for the import probe, preparation and worker. LOCAL_RUN records the executed binary's identity and the package's distinct bwrap pin. Neither authenticated a4 members nor `pyvenv.cfg` are edited. A namespace failure stops; there is no relocation fallback. See [ENVIRONMENT.md](ENVIRONMENT.md).

Runtime extraction records every member's name, type and size. STAGE_CHECK includes those lists, verifies the paths/modules needed by sealed preparation, checks exact framework versions and audit-root coverage, and rejects unexplained files before preparation. It also retains runtime inventory when a stage check refuses. Runtime expansion is capped at 40 GB; staged footprint must stay below 145 GB, leaving 5 GB below the 150 GB limit. Free scratch must remain at least 200 GiB. These limits do not claim a measured target footprint.

After staging, the direct handoff also works:

```bash
date -u
bash read228.sh A10b "$CARD" --items 50
```

The gate requires two readings at least 300 seconds apart, each below 100 MiB with no process, the same UUID, and an RTX 6000 Ada with 48,000–50,000 MiB. Its lock coordinates this kit; another program can still take the card afterward. The worker runs under the pinned vnice/terminator scripts in its own process group. The first OOM stops without retry, writes OOM.json and returns 42; both `out of memory` and `alloc_failed` RuntimeErrors count as OOM. All wrappers set HOME, XDG directories, TMPDIR and framework caches on local scratch. The cluster terminator's `/tmp/terminator` file is the mandated exception.

A successful prefix has **50/636**, `SUMMARY.failure=null`, and no FAILED.json. EXIT.status remains FAILED because the full read is incomplete. The unchanged unpacker authenticates that envelope. Coordinator unpacking writes `kit/ingest/<run-name>`; [ingest228.py](ingest228.py) uses SUMMARY and the comparison to publish `CORPUS_INGEST.json`. READY_FOR_CORPUS names the unpacked directory for the corpus consumer; this kit does not modify an external corpus database.

SAME_INSTRUMENT requires at least 49 identical answers and all 50 identical call placements, plus equal complete binding and settings dictionaries. Placement is `(index, family, call, served, at_token)`; stage-1 floats remain trace diagnostics. FIRST50 pins reference IDENTITY and every included reference journal environment. Candidate SUMMARY, failure markers, OFF mode, local host, Ada card, journal hosts and a distinct local return ID are mandatory. Differences list their keys. These checks establish consistency, not hardware attestation.

The optional `--on` overlays default OFF and cannot establish the OFF device check. Their supplied consistency issue remains in [SO_READ_CONSISTENCY.json](SO_READ_CONSISTENCY.json).

```bash
date -u
bash tests/run_tests.sh
```

CPU tests use the dispatch Python, hide CUDA, and limit threads to eight. Tests write only under the workspace's `work/` tree; READ228_TEST_WORK can select another allowed scratch test directory. [REPORT.md](REPORT.md) contains exact outputs, regression evidence, the complete coordinator command sequence and target-only checks still required.
