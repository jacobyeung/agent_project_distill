# D0 job B packet: the first GPU leg (mode t, world 4, Orchard advanced), warm start from the step-544 export, rows v5

Lane cont_ops4 (trinity-1-3). Card: `PRELAUNCH_CARD_D0.md` (v5 numbers). Review: `REVIEW_CONFIRMATION_R10.md` (B: r10 GO AFTER FIXES, r11 GO after the Orchard manifest check, done 03:19Z).

## What runs
- Kit `okh7/x_f5c353f7` (READY), derived on the Orchard login from sealed kit `x_07ca49df` by `derive_kit.py` (4ad1a5ac). Run 359fcc3c, persistent root `okh7/r/63e57182` (created by the wrapper at start). Config d6827df0, identity 80f4af947f0ca9edfac04041cf65e079edb92752618b2de6dc4078491a88f1ba, admission contract aaf2d7b045632f14d96cfc62adbf2a1eab5212d713ac6ebaed03c1b44309ca19, manifest 231c98dcc568b4a1d5123bd827c50c7e651dffa602141670e1716c9ce2fc61ae (ANON_OK a9ad5b5e, CLEAN; a.py PASS).
- Changes from the sealed kit: VQA stream receipt (rows v5 4af43b40, 152,123 rows; receipt c95023e4 at `i_bb09a77d/vb5.json`), pool selection without ROUTE_direct (f232d416), init artifact m544 (1d6eeb28; repacked `i_bb09a77d/m.tar`, 42457dbd), new run identity, review.json, staging.json and 4.json bound to the identity.
- Wrapper `i_bb09a77d/b5/jb.sh` (3b8f0162): job 169097's wrapper with the kit paths, the export-session check (44 sessions minted 2026-11-15T23:19Z for run 359fcc3c, assumed expiry 2026-11-22T23:19Z) and `vt.py` before restore, plus the slot fallback to GCS (r10).

## Gates inside the job (any failure ends the job; no retry)
1. Export sessions present (44 keys, mode 600) and `vt.py` on every new archive.
2. In-job admission: native mode p on the full population under the new identity (the D0 rows' first full admission at world 4; job A2 tests it on CPU in parallel).
3. GPU first-step gate `all_rank_native_v1`: every rank's first batch through the full forward with finite losses before the first update.
4. Watch on steps 1-3 (mine, every minute): pose, VQA and pointing losses against m544's steps 530-544 (`work/BASELINE_530_544.json`); routing exempt (opener reset, confound 1). An alarm means scancel, on your authorization in the GO.

## Submission (on your GO)
`cd /project/community/jjyeung/okh7/i_bb09a77d && TZ=UTC env -u TK_JOB_START sbatch -J a15_cot_apddbe32d7 -o /dev/null -e /project/community/jjyeung/okh7/x_f5c353f7/o/%j.err b5/jb.sh` (`-A mt01 -p advanced -N1 --gres=gpu:4 -c 48 --mem=800G -t 24:00:00 --no-requeue --signal=B:USR1@3600`).
- Slurm's estimate (`--test-only`, 03:20Z): start 2026-11-16T22:51Z (14:51 PT).
- Cancel before start if A2's stage 1 or stage 2 fails (your 00:59Z rule).
- The advanced QOS allows 4 GPUs per user, so B and the LEG-S1 continuation cannot run at the same time.

## Effects and cost
- 4 H100 for 24 h per allocation; 1,000 steps at about 131 s is two allocations (about 146-190 GPU-h with admission). Step 100 lands about 4 h and step 200 about 7.5 h after the first step.
- Project: the kit (about 250 MB) and, at the allocation's end, the 113 GB slot in `r/63e57182` (176 GB free at 00:42Z). If project lacks the slot plus 20 GB, the slot goes to `gs://.../q8/d2d30e36/359fcc3c_s<step>.tar` instead (exit 6); if that fails too, the exact resume is lost and the weights remain on GCS (milestone and stop exports).
- GCS: milestone exports m1, m50, m100, m200, m400, m600, m800, m1000 and stop exports through the minted sessions.

## Mirror and records
- Orchard-resident: kit, bundle and records with sha256 in STATUS.md. Local build in `work/d0/a2/v5b/` on trinity-1-3, mirrored to trinity-0-13:/scratch/jjyeung/n30_mirror/cont_ops/mirror_d0_v5.tar (sha256 69cea70f, session files excluded).

## Records
- Reviews in the events folder: REVIEW_JOB_B_R9.md, REVIEW_CONFIRMATION_R10.md, REVIEW_CONFIRMATION_R11.md (B: the code fixes pass; only the Orchard manifest check remained, done).
- On Orchard: `x_f5c353f7/k/review.json` ddd34ff2, `k/staging.json` 133bffea, `k/4.json` 3f64925a (modes p, t, u; until 2026-11-26T00:00Z; production_go_granted false, a separate GO is required), `ANON_OK.json` a9ad5b5e.
- Ledger token meanings are kept on trinity-1-3 (`cont_ops/work/ORCHARD_LEDGER.jsonl`).
