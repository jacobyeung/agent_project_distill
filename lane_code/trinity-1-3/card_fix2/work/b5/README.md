# card_fix2 evidence for R1 card v3 (conditional simulation estimates; 2026-11-17)
Inputs, read-only: step 544 `cont_ops/work/d0/readk/evidence/A544.jsonl` (sha256 8347cd84...) and D0 m200 `.../kit/build/a4cadd8934b/fetched/x/ITEMS.jsonl` (c1c99e4d...), job 170320; step 544's own-arm distance read `items.jsonl` 826385c6 (job 170706) with `devs1_routed.json` 2849206e; `rows_r1/out/vsti_rel_dev_r0/items.jsonl` b5853845.
- `b5_sim.py harm {size,toward,relsize}` -> `B5_harm_*.json`: chance that the interval lies wholly below zero at H1's levels, under no change (arms exchanged per room) and under losses (item flips; constant shift on the exchange null). 4,000 pseudo-reads x 10,000 draws.
- `b5_sim.py gate away` -> `B5_gate_away_*.json`: facing gate, minimum detectable improvement, without back-flips and with D0's rate (5 of 32). 4,000 x 4,000.
- `b5_units.py` -> `B5_UNITS_RECOVERY_OWN_ARM.json`: exact own-arm unit baseline (22 of 107) and the unit and recovery gates' minimum detectable improvements on that read. 4,000 x 4,000.
- `b5_vsti.py` -> `B5_VSTI_PLANNING.json`: planning value for the VSTI gate on the dev set's rooms with an assumed baseline. 2,000 x 2,000.
- `b8_room.py` -> `B8_ROOM_CALL_BOUND.json`: one-sided 95% upper bound of the room call rate by bootstrap over the 107 physical rooms.
`B5_gate_away_1_r0.json` and `B5_harm_size_1.json` in the lane folder are smoke runs of 40 pseudo-reads; they are not evidence and are left out of the tar. run_*.out hold the full runs' printed JSON.
