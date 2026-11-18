# STATUS lane pooled_rule (Devin Fable xhigh, trinity-1-3) — started 2026-11-18T02:19Z, finished 02:51Z; all deliverables written, lane exits after the RESULT event
Recommendation: ADOPT the pooled harm rule (eight types; six shared types pooled with item-count weights; rooms drawn inside each set; seed 20261118). It binds only if the orchestrator registers it before the first R1 export is read. Until then the card's dev-S1 rule binds.

## Deliverables
- Registration text: `events/pooled_rule/POOLED_RULE_REGISTRATION.md` (sha256 cc96a00e5c6a70a542f455c4874d0450ca5d64de73f822056d4bb117f4182ea0); lane copy `out/POOLED_RULE_REGISTRATION.md`.
- Reference implementation: `events/pooled_rule/pooled_harm_rule.py` (a144e2cc093bbbfd4137b79dedc2be40ac29f3efcb910654d4125e77dc6cfc1b); lane copy `work/pooled_harm_rule.py`.
- Evidence: `events/pooled_rule/pooled_rule_evidence.tgz` (bc97a1feae40925dbe64ecb5cb48d186978117b8e63db69ab1dfc3b44d7d0fd8, 249,528 B): scripts, results, item lists, room list, both step-544 baselines, the registration and the record. The 64 simulation arrays stay in `work/` (sha256 in `work/SIMS_SHA256.txt`).
- Record: `/data2/jjyeung/agent_project_data/distill_design/POOLED_HARM_RULE_R1_20261118.md` (78f2f18e) and one line appended to `INDEX.md` (line 233).
- RESULT event: `events/pooled_rule/20261118T0250Z_RESULT_pooled_rule_adopt.md`.
- Mirror: trinity-1-3:`/scratch/jjyeung/orch_n30/pooled_rule/out/pooled_rule_lane_20261118.tar` and trinity-1-18:`/scratch/jjyeung/n30_mirror/pooled_rule/pooled_rule_lane_20261118.tar`, both sha256 f41836225c085ef3df00199d0b610045ef16dba4e8c96ac63a708f22be8c60b0 (271,861,760 B, copied over InfiniBand, one ssh call).

## What was run (all CPU, trinity-1-3, `work/`)
- `pr_data.py`: loads the eight reads (step 544, D0 m200, D0 m100, H1-1 m100 on dev-S1 and R0-dev), checks keys and metadata, writes `PAIRS.npz`, `PAIRS_META.json`, `ROOM_LIST.txt`.
- `pr_sim.py SEED 500 10000 ARM` for seeds 101-116 and ARM in D0m200, H1m100, D0m100; `pr_merge.py`; `pr_table.py` -> `POOLED_POWER_<ARM>.json`, `POOLED_TABLES.md`. Environment: OMP_NUM_THREADS=1 and MALLOC_MMAP_MAX_=0 (without them the node spends the time in the kernel).
- `pr_looks.py` seeds 201-216, `pr_looks_merge.py` -> `LOOKS.json`. `pr_observed.py` -> `OBSERVED_READS.json`. `pooled_harm_rule.py --calibration` on the three real reads -> `obs/`.
- `r0_exposure.py`, `r0_unresolved.py`, `r0_units.py` -> `R0_EXPOSURE_V7.json`, `R0_EXPOSURE_UNITS_P.json`. `pr_lists.py` -> `ITEMS_DEV_S1.tsv`, `ITEMS_R0_DEV.tsv`, `REGISTERED_PINS.json`.

## Open, for the orchestrator
- Register the text, or keep the dev-S1 rule. The cost of adopting is the dilution of a loss confined to dev-S1 (0.17 to 0.24 against 0.41 to 0.65).
- Order one independent review of `pooled_harm_rule.py` and `pr_sim.py`; none has been done.
- H3 has no estimate (no paired tower-arm read). The read noise of an unchanged model is unmeasured (step 544 has one read per set). The R0 audit rests on the census for 52 ScanNet++ scene tokens (2,433 VQA rows) and for the Orchard routing, pose and pointing streams.
- `work/token_probe.py` is a failed attempt to derive the scene tokens by hashing; it found nothing and no result depends on it.

## Note on the rm_guard hook
The hook queued one command of this lane in `/home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md` as "unparsable" (two heredocs writing STATUS.md and work/pr_sim.py, then a 6-draw timing run). It deletes nothing. Do NOT run it: it would overwrite STATUS.md and pr_sim.py with old text. I wrote those files with the file tool instead.
