# C1-r delta review: trainer 76b80b9c, kit config b4254f7a (Claude Opus, 2026-11-08)

**VERDICT: GO. I found no blocking item.** The delta implements the merged design and fixes B1-B3. I found nothing in it that would crash the run, stop it learning, or train a wrong target. The launch still needs the kit's normal pre-launch chain (N2), which refuses loudly until it is done.

Scope: the worktree at `c1r/work/repo_c1r` (HEAD ref `c1r-g3t` = 76b80b9c, read from the ref file), plus kit `b/i.py`, `b/w.py` and `k/b4254f7a.json`. I used no git. I ran CPU-only checks: 35 unit tests (`test_c1r_align`, `test_c1r_w1`, `test_c1r_review`), an independent numerical check of the Pearson and CCC terms, and `c1r_run.validate` on the kit config. I made one read-only code-aws call.

## BLOCKING
None.

## Non-blocking (in priority order)
1. **The m100 canary and the m400 gate cannot run yet.** `readout.contiguous_clips` is null (`k/b4254f7a.json` readout block). `c1r_run.evaluate` refuses (`c1r_run.py:455-456`), and so does the gate (`carrier_c1_run.py:87-89`).
   - Training is unaffected. Identity excludes this key (`carrier_c1_run.py:33-34`).
   - Fix: pin C1-b's 38-scene contiguous manifest before step 100. The duplicate readout needs no partner inventories (`c1r_data.py:170-172`).
2. **The kit still seals the old 62ee4d8a source.** `k/7.json`, `k/0.json` and the trainer tar all name 62ee4d8a, and `k/4.json` allows only mode c.
   - `authenticate` (`c1r_run.py:79-86`) and `i.py:87-91` refuse until the kit is resealed at 76b80b9c and the run is re-prepared. The guards, timing, review and authorization pins must then be regenerated. All of these failures are loud.
3. **Throughput.** The pinned `c1r_dense.py:451-459` hashes each shard blob once per process, and `:501-512` hashes every array, including `patch_full`, with the patch term off.
   - In each 4-h allocation, each rank touches about 400 of the 443 shards, so it reads and hashes roughly 1.5 TB with SHA. Expect slow early steps after every (re)start; `data_seconds` will show it. FP1's p95 of 60 s may be optimistic.
   - The pinned files cannot change, so the timing evidence must come from measured steps.
4. **The coverage audit is long, and coverage must be nearly complete.**
   - `c1r_data.py:108-156` reads and hashes the whole published store in one CPU process, so give the mode-a job hours of wall time.
   - `i.py:61-74,116` requires 225 steps of coverage (7,200 rows). Rows are shuffled across recordings, so in practice the whole cache must be published first.
5. **Check the optimizer grouping under FSDP once.** The FSDP/Gloo test was skipped. At step 1, confirm that `gradient_norms` contains `heads_pretrained` (`carrier_c1_run.py:295`). The naming path is the same `clean_name` path C1-b used (`carrier_c1_run.py:574`, `c1r_run.py:184-194`), so the risk is low.
6. **C1-r vs C1-b changes several things at once.** The two arms differ in:
   - layout: duplicate, 32 temporal patches with 1 CAM per patch, vs spread, 16 patches with 2 CAMs each;
   - anchor sampling: dense jitter;
   - the teacher terms;
   - head init and the LR split.

   The readout records these confounds (`c1r_data.py:223-229`). State them with any delta.
7. **The design's memory estimate is low (doc nit).** If H = 4096, the 2H projector has about 50M FP32 parameters, which is about 0.8 GB per GPU with AdamW states, not 0.4 GB.
