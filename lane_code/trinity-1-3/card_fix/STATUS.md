# card_fix STATUS (Devin Fable xhigh, trinity-1-3; lane folder /scratch/jjyeung/orch_n30/card_fix)
DONE 20261117T1503Z (started 14:29Z 2026-11-17). Design lane: no GPU, Orchard call, ssh, Git, deletion or dispatch. The lane has exited; nothing is owed by it.

## Deliverables
- Record rewritten in place: /data2/jjyeung/agent_project_data/distill_design/NEXT_LEG_DECISION_20261117.md (sha256 16ed4a7107d1...; lane copy out/NEXT_LEG_DECISION_20261117.md; earlier bytes work/RECORD_orig.md 936ea4a5 and work/RECORD_before_write_1788.md, which holds r1_ops's 14:39Z edit). INDEX.md line 226 updated (earlier file work/INDEX_before_card_fix.md).
- Registration card: events/next_leg/R1_CARD_v2.md (lane copy out/R1_CARD_v2.md); r1_ops fills the [r1_ops: ...] fields.
- A3 computation: work/a3/ (a3_power.py pass 1, a3_power2.py + a3_merge.py pass 2 with 8,000 pseudo-reads, a3_shift.py, a3_d0check.py; outputs A3_POWER.json, A3_POWER_PASS2.json, A3_SHIFT_ON_EXCHANGE_NULL.json, D0_M200_UNDER_R1_RULE.json); evidence tar events/next_leg/card_fix_a3_evidence.tgz = out/card_fix_a3_evidence.tgz (sha256 47b1b97f...).
- out/unit_none.py: exact unit baseline on unperturbed reads; runs where the scored items.jsonl is (Orchard okh7/e6fc152498/r2/sj/h10sub3_b01ec87a6f29b00029ad2/).
- RESULT: events/next_leg/20261117T1503Z_RESULT_card_fix_r1_card_v2.md (lane copy out/RESULT.md).

## What a successor needs to know
- Open slots in the card: SIZE-V (size_diag, due about 17:30Z); exact unit baseline (unit_none.py); tower-arm read of step 544 (H3 and claimed-arm marks); the read tools' interval level and joint mean of seven (cont_ops); the VSTI dev set and its step-544 read; the loader audit's counts.
- The unit baseline is bounded, not counted: 13 to 30 of 107 unperturbed non-metre items (results/170706 holds aggregates over three modes only).
- Pass 1 of the A3 computation centred the item differences, which inflates false stops on sparse types; the record cites pass 2 (arms exchanged per room) for "no change" and both models for power.
- Mirror: none needed; every deliverable is on /data2. Lane folder about 10 MB (work/a3/*.npz are the stored bootstrap bounds).
