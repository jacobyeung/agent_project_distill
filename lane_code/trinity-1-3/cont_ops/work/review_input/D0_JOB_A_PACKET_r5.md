# D0 job A packet: m544 repack and native admission (mode p) on `general`, CPU only

## Why two jobs, not one
The kit's own gates rule out repack + p + c in one job. `b/g.py` lets mode p run on a kit with status PREPARATION_ONLY and a 4.json that allows p. Mode c needs status READY. READY needs review.json, and staging.json with `missing: []` (g.py:98-117), and staging verification needs the repacked m544 archive, which only a job can make. Mode c also needs exactly one GPU (b/i.py GPU['c'] = 1, i.py:60-68). Order:
1. **Job A (this packet):** repack plus mode p on `general`, CPU only, kit status PREPARATION_ONLY. This settles admission of the D0 rows, including route planning in VQA.
2. Staging verification, independent review of the derived config and admission contract, ANON_OK scan, then a READY derivation.
3. **Job B:** mode t on `advanced` at world 4. In-job admission and the GPU first-step gate `all_rank_native_v1` check every rank's first batch. A separate 1-GPU mode c job on `general` is optional.

## Inputs (all verified on Trinity; `d0_tools/v1`, `d0_tools/job`)
- Rows v1: rows_rebuild's `/project/community/jjyeung/okh7/b31a069738d1e2f9/r.sqlite` (4487181b).
- The job receipt is the rows_rebuild receipt `r.json` (f1600070) with `database.path` moved to `AS/ap/bb09a77d/v/rows.sqlite` (fc9fea77). Its source `S.sha256` is waived as provenance, and its division is the file the sealed VQA receipt pins (sealed bytes fetched, 524b14f9).
- Pool selection: `pool_selection_d0c.json` (05985ea7), the sealed selection with ROUTE_direct DEFERRED.
- Init: m544, artifact 1d6eeb28. Repacked to `/project/community/jjyeung/okh7/i_bb09a77d/m.tar` with members `ap/8865619b/runs/469ddece/m544/{heads.pt, full_weights/*}` and `ap/d0i04e67f96/m544/artifact.json`.
- Identity: run 04e67f96, kit 7cb63d1e, persistent root `/project/community/jjyeung/okh7/r/1b235d89`. Fixture derivation on Trinity: config 3e9eb72e, identity 3d00fbd3; closure passes.

## Steps before submission (operator, Orchard login, small writes only)
1. Upload one bundle (under 1 MB) to `okh7/i_bb09a77d/`: `v.json` (job receipt), `M544_SOURCE.json`, `repack_m544.py` (20b49c74), the kit inputs and derive_kit (ef166e88).
2. Run derive_kit on the login node from the sealed kit `okh7/x_07ca49df` to `okh7/x_7cb63d1e`. It writes about 250 MB (k/ with the two large sealed tars), with status PREPARATION_ONLY and a new 4.json (modes [p], identity-bound, until 2026-11-26).
3. ANON_OK: a.py refuses mode p until ANON_OK.json is CLEAN. **Question:** who scans? Default: the same Codex reviewer scans the changed and new members, and confirms that unchanged members are byte-identical to the kit scanned on 2026-11-13.
4. Run `sbatch --test-only` and the write test (64 KiB in `okh7/x_7cb63d1e/o/`).

## Submission (on your GO)
`cd /tmp && TZ=UTC sbatch -o /dev/null -e /project/community/jjyeung/okh7/x_7cb63d1e/o/%j.err < ja.sh` (ja.sh 3cb2fb10: `-A mt01 -p general -c 32 --mem=800G -t 06:00:00 --no-requeue -J a15_cot_ap543f18fd`). The script:
1. Runs `repack_m544.py`. It reads the four GCS parts with the Orchard gcloud configuration (as evalx27 does) and checks each part, the whole stream (3ed73aea), the artifact, heads and manifest pins, and every manifest file. It writes the tar on node /tmp, copies it to project, and uploads it as one new GCS object (name in the ledger). It writes `o/<job>.REPACK.json`, which holds the member sha256s and the bytes of full_weights.json for the READY derivation.
2. Runs `b/r.sh p 0`.

Repack was tested locally on a synthetic 4-part export, and a one-byte corruption was refused. The GCS read path in production is untested here (evalx27's proof job read the same four parts in 124 s).

## Start estimates (sbatch --test-only, 21:00Z)
- `general`, CPU, 32 cores, 800G: start 2026-11-15T23:15Z (15:15 PT), behind 170008.
- `general`, 1 GPU (for a later mode c): start 23:15Z.
- `advanced`, 4 GPU, 24 h: start 2026-11-16T05:33Z (21:33 PT).

## Cost and effects
- About 10-20 min of repack plus mode p (1 h 45 min in 169097) on one `general` slot.
- Project writes: 21.6 GB (m.tar) plus about 250 MB of kit. 315 GB free at 21:00Z.
- One GCS object of 21.6 GB.
- No GPU. evalx27's 170008 is untouched; job A queues behind it.

## Stop and report
Any failure ends the job without retry. I watch `o/<job>.a.steps`, `o/<job>.steps` and `.err` every minute at first, then every 10 minutes. I report the admission verdict: whether route-planning VQA rows are admitted, the per-stream counts, and the refusals.
