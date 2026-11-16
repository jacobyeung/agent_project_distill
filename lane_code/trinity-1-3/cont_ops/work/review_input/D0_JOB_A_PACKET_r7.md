# D0 job A packet: m544 repack and native admission (mode p) on `general`, CPU only

## Why two jobs, not one
The kit's own gates rule out repack + p + c in one job. `b/g.py` lets mode p run on a kit with status PREPARATION_ONLY and a 4.json that allows p. Mode c needs status READY. READY needs review.json, and staging.json with `missing: []` (g.py:98-117), and staging verification needs the repacked m544 archive, which only a job can make. Mode c also needs exactly one GPU (b/i.py GPU['c'] = 1). Order:
1. **Job A (this packet):** repack plus mode p on `general`, CPU only, kit status PREPARATION_ONLY. This settles admission of the D0 rows, including route planning in VQA.
2. Staging verification, independent review of the derived config and admission contract, ANON_OK scan, then a READY derivation from the sealed kit.
3. **Job B:** mode t on `advanced` at world 4, on a kit derived again from the sealed kit with the final rows and new run, kit and root tokens. Job A's mode p binds its persistent root `r/1b235d89` to job A (b/r8.py writes `RUN.json` with job A's id), so that root and run 04e67f96 are retired after job A; derive_kit refuses a root that exists. Job B's wrapper runs `vt.py` before `b/r.sh`, as job A does. In-job admission and the GPU first-step gate `all_rank_native_v1` check every rank's first batch.

## Inputs (Trinity copies in `d0_tools/r7/`)
- Rows v1: rows_rebuild's `/project/community/jjyeung/okh7/b31a069738d1e2f9/r.sqlite` (4487181b).
- Job receipt `v.json` (fc9fea77): rows_rebuild's `r.json` (f1600070) with `database.path` moved to `AS/ap/bb09a77d/v/rows.sqlite`. Its source `S.sha256` is waived as provenance; its division is the file the sealed VQA receipt pins (524b14f9).
- Pool selection: rows_rebuild's DEFERRED form (`pool_selection_d0_v2.json`, bb5483e7), staged as `k/pool_selection_13b52fee.json`: ROUTE_direct DEFERRED with the sealed SCENE_room_sppK key set, selected_rows 83,184.
- Init: m544, artifact 1d6eeb28, repacked to `okh7/i_bb09a77d/m.tar` with members `ap/8865619b/runs/469ddece/m544/{heads.pt, full_weights/*}` and `ap/93ccadab/m544/artifact.json`.
- Identity: run 04e67f96, kit 7cb63d1e, root `okh7/r/1b235d89` (absent on Orchard at 21:55Z).

## Done on the Orchard login (21:55Z)
1. Bundle uploaded to `okh7/i_bb09a77d/` (195 KB; sums match): `v.json`, `M544_SOURCE.json` (efa496fd), `repack_m544.py` (e68e9095), `vt.py` (672df2c1), `ja.sh` (522a159d), `derive_kit.py` (4ad1a5ac), `over.json` (e1d5f725), `4.json` (2ef379e7: modes [p], 0 GPUs, identity 164c708c, until 2026-11-26), `pool_selection_13b52fee.json`, `artifact.json`, `sealed_vqa_receipt.json`, `E00_MEMBERS.json`.
2. Derived `okh7/x_07ca49df` -> `okh7/x_7cb63d1e`: status PREPARATION_ONLY, config 8d141f0e, identity 164c708c, manifest d58f3385, no absent payloads; closure 11 additions, 9 removals, 7 chained export members. Its config, 0.json, 1.json and pool selection are byte-identical to the Trinity fixture derivation; launch.json differs only in status.

## Steps left before submission
1. ANON_OK.json CLEAN from the reviewer's scan of the final manifest (round r7), written into `x_7cb63d1e`.
2. `sbatch --test-only` and the write test (64 KiB in `x_7cb63d1e/o/` and in `i_bb09a77d/`).

## Submission (on GO, after the steps above)
`cd /tmp && TZ=UTC sbatch -o /dev/null -e /project/community/jjyeung/okh7/x_7cb63d1e/o/%j.err < /project/community/jjyeung/okh7/i_bb09a77d/ja.sh` (`-A mt01 -p general -c 32 --mem=800G -t 06:00:00 --no-requeue -J a15_cot_ap543f18fd`). The script:
1. Refuses an existing `m.tar` or `m.tar.partial`, then runs `repack_m544.py`. It reads the four GCS parts with the Orchard gcloud configuration (as evalx27 does; no URL or upload session is minted, so nothing travels in stdin) and checks each part, the whole stream (3ed73aea), the artifact, heads and manifest pins, and every manifest file. It writes the tar on node /tmp, copies it to project, verifies the copy, and uploads it as one non-composite GCS object `q8/69cb3a6a/9ec4a68bf49b.tar`, checked by size and md5. It writes `o/<job>.REPACK.json` with the member sha256s, the tar sha256 and md5, and the bytes of full_weights.json for the READY derivation.
2. Runs `vt.py` on the derived kit: it streams every new tar entry (`m.tar`, 21.6 GB, from project) and refuses any member that is not a regular file, not listed or not named by the listed full_weights.json, any sha256 mismatch or conflicting pin, any absent listed or manifest-named file, duplicates, and any new member or extra destination that lands on an `e00` member or a sealed placement. c.sh extracts every member and checks only the listed ones; this check closes that gap without changing the sealed code.
3. Runs `b/r.sh p 0`.

Repack was tested locally on a synthetic 4-part export (a one-byte corruption was refused); the production GCS read is untested here (evalx27's proof job read the same four parts in 124 s).

## Start estimates (sbatch --test-only, 21:00Z; rerun before submission)
- `general`, CPU, 32 cores, 800G: 2026-11-15T23:15Z (15:15 PT). At 21:53Z our account had no job on general (170008 has ended).
- `advanced`, 4 GPU, 24 h: 2026-11-16T05:33Z (21:33 PT).

## Cost and effects
- About 10-20 min of repack, a few minutes of vt.py, then mode p (1 h 45 min in 169097) on one `general` slot.
- Project writes: 21.6 GB (`i_bb09a77d/m.tar`), the kit `x_7cb63d1e` (about 250 MB, written), `x_7cb63d1e/o/<job>.{a.steps,repack.log,REPACK.json,vt.json,err,steps}`, mode p's `x_7cb63d1e/arm/` and `x_7cb63d1e/runs/`, and `r/1b235d89/RUN.json` (bound to job A). 296 GB free at 21:53Z.
- Node-local writes: `/tmp/jjyeung/w_<job>/` (21.6 GB tar plus work, left to the node's /tmp cleanup) and c.sh's staging and run trees under `/tmp/jjyeung/okit_8865619b/`. The repack refuses to start below archive size plus 50 GiB free.
- One GCS object of 21.6 GB. No GPU. Nothing under Orchard /home.

## Stop and report
Any failure ends the job without retry. I watch `o/<job>.a.steps`, `o/<job>.steps` and `.err` every minute at first, then every 10 minutes. The RESULT event reports the admission verdict (route-planning, facing and total rows admitted and refused per family), whether the pool selection without ROUTE_direct materializes, the repacked export's sha256 and GCS name, and mode p's first-batch statistics.
