Apply after N's first proof. Priority and application order: **03, 04, 02**. **01 stays OFF**: patch 01 cannot hit in the production topology in a way that avoids native work. Its estimated saving is zero or worse. The builder fixes the node-local run path; another node lacks the source, and a complete same-node journal already supports native reuse.

```bash
patch --batch --fuzz=0 -p1 -i "$L/out/patches/03_checkpoint_verify_memo.diff"
patch --batch --fuzz=0 -p1 -i "$L/out/patches/04_launch_phase_timing.diff"
patch --batch --fuzz=0 -p1 -i "$L/out/patches/02_parallel_frame_sha.diff"
```

Check patch SHA256 and base pins in `patches/manifest.json`. Each patch also applies independently to build 20. Review any build-21 port; reject fuzz or failed hunks. Patch 01 is supplied for review with defensive fixes, not for enablement. Rebuild and rescan the source archive, executable inventory and source/config seals before running a changed kit. If 01 is included, inventory its new `b/pc.py` too.

Keep all switches OFF for the normal proof. Then enable one candidate at a time:

| Switch | Check |
|---|---|
| `TK_CHECKPOINT_VERIFY_MEMO=1` | First check fully hashes; unchanged repeats in the same allocation hit. New job/clock, changed marker/payload/binding or purge must rehash or refuse. |
| `TK_LAUNCH_TIMING=1` | Steps separate the job guard/chooser, recursive p guard, parent u guard and stage-lock wait. Missing/unwritable logs must not abort. |
| `TK_PARALLEL_FRAME_SHA=1` | Start with `TK_FRAME_SHA_WORKERS=4`; compare verdict/count and measure f2 alone on warm local storage. |

Patch 03's **estimate is 4–10 min per resume launch**. Four `complete()` calls run through the job guard, direct chooser, recursive p guard and parent u guard; the memo removes three full reads. The measured 675-s and 86-s gaps support this inference. Mode p measured 140.57 and 145.27 min; useful reuse requires the native changes in [CROSS_RUN_STORE_DESIGN.md](CROSS_RUN_STORE_DESIGN.md).

Run the five patch test scripts and `work/run_native_regression.py` using the exact CPU environment and commands in [REPORT.md](REPORT.md). Fresh standalone, recommended-set and combined patch applications are checked. Exact output and before/after regressions are indexed in [tests/review_round1/INDEX.md](tests/review_round1/INDEX.md). The expanded gate explicitly reports ten unavailable Gloo tests and one unstaged-pool test; rerun those in their supported environment. Five stale admission-fixture failures reproduce on input and patched trees. Preserve every native authorization, parent, checkpoint and all-rank first-step gate.

## Review round 1: finding -> fix -> test

| Finding | Fix and regression |
|---|---|
| 1 | 01 OFF; claim/design contract and same-path/purge tests. |
| 2 | MISS preserves destination; partial reuse and foreign-binding refusal. |
| 3 | 03 first; report contract and four-process guard/chooser test. |
| 4 | Inherited lock marker, 600-s timeout; symlink and duplicate t/u tests. |
| 5 | Real `c.sh` staging matrix with stubbed dependencies. |
| 6 | Guard logs and time both guards; missing/unwritable output and failure tests. |
| 7 | Full relevant native modules; selection regression and expanded gate. |
| 8 | Remove unused names; inspect all written cache JSON names/fields. |
