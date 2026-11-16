# Refute check, change 5 reader-harness (2026-11-16)
Verdict: refuted (queue saving not supported); frame guard and no-fork claims partly hold.
1. "1 to 4 h of queue per read": ORCHARD_PACKED_JOB_FEASIBILITY_20261114.md line 5 says "expected one-to-four-hour queue gain" for packing 3 reads + P0 into one advanced job, not per read; based on "roughly thirteen-hour general-queue forecasts" (forecasts, not starts).
2. Measured general queues (events/evalx27): proof 169991 submitted ~18:43Z, ran 19:35Z (~50 min); production 170008 afterok start 19:55:55Z (0 min); ReVSI proof 170035 submitted ~21:17Z done 21:23Z; production 170037 started 21:23:55Z (0 min). afterok chaining already gives ~0 queue between reads.
3. Existing kit already sequential: readk/kit/reader/chain.py line 1 "Run full families sequentially and retain compact authenticated returns."
4. D0 milestone reads are staggered by training progress (ruling 1102Z: step-200 read waits for m200 .done ~17:50Z) and the brief puts them out of scope; one long plan job also conflicts with the ruling's time-limit windows ("no job ... time limit ending after 17:45Z, except a D0 read").
5. "trinity_read.py has 14 versions": INVENTORY.md line 25 "14 | 14 | incl. test roots; 3 live builds". trinity_read.py runs on a Trinity card (build_t6/README.md), so no Orchard queue applies to it.
6. Frame guard: lesson 11-11 (3-13 points) is real; PROTOCOL.json already pins "layout": "duplicate" per family; the new part is the export-vs-read comparison.
7. Executability: parity predictions exist at events/evalx27/prod_a8acc277397/{B2048,B4096,ON16k}.json (1.1 MB each, above REF's 512 KB cap) and prod_a348bc58686, but the brief's allowed sources (REF, review_a0d, a0_design) hold none; parity test would prove nothing unless the brief names them.
8. IO/legality/provenance: no weakening found (no ssh, no streams, pinned official scorer, branch only).
