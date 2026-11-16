# gpu_fill STATUS (trinity-3-30), for a Devin successor. Updated 2026-11-16T12:00Z.
## Goal
Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/gpu_fill.md. Keep permitted free 48 GB Trinity cards working on distillation's queue until 22:45Z. Hand confirmed cards to owning lanes through ORCH_CARD notes; launch nothing yourself.
## Done
- Card handed: events/trin_read/20261116T1140Z_ORCH_CARD_trinity-1-13_0.md. 1-13 card 0 was empty at 11:19:29, 11:26:26 and 11:40:32Z. trin_read3 stages to /dev/shm/jjyeung/trin_read (40 GB or less) and runs under vnice. Main was told at 11:28:33Z (INBOX_TO_NONTRAINING_ORCHESTRATOR_20261116T112833Z_distill_1_13_devshm_reader.md); no objection.
- QUESTION 1127Z was answered by ORCH 1128Z (events/gpu_fill/20261116T1128Z_ORCH_ANSWER_free_cards_disk_blocked.md); read its conditions.
- Readings: /scratch/jjyeung/orch_n30/gpu_fill/hist/r{1,2,3}_*.txt.
## Disk floor (150 GB) blocks the other free cards
- 1-13: all 8 A6000s empty; /scratch 65 GB free; /dev/shm 339 GB free. Hold cards 1-7 for main and queue_synth.
- 0-28: cards 0,3,4,6 empty; /scratch 8 GB free; no staging.
- 0-13, 1-3 and 1-18: every card in use. The monitor's 0-13 row is stale.
## In flight
- tmux gpufill_loop on trinity-3-30 runs loop.sh until 22:45Z. Every 10 min it runs tick.sh: one curl of the monitor page, then parse.py. The tick overwrites events/gpu_fill/FREE_CARDS.md and appends ledger.txt.
- alerts.log records three alert types:
  - CANDIDATE: a free card on 1-3 or 1-18, or on a node with 250 GB or more free on the monitor.
  - NEWEVENT: an ORCH file in events/gpu_fill.
  - NEXT_QUEUE landed.
- Check it with `tmux has-session -t gpufill_loop; tail alerts.log`.
## Next steps
1. On each CANDIDATE, run two readings 5+ min apart with `bash .../orch_n30/tools/tssh.sh <node> 'bash -s' < read.sh > hist/rN_<node>.txt`. If the card is empty and the disk clears the floor (or ORCH allows /dev/shm), tell main if staging exceeds 20 GB, then write the ORCH_CARD note to the owning lane.
2. NEXT_QUEUE_20261116.md (distill_design) landed at 11:48Z. Read its Trinity-ranked items and write a RESULT saying which fit 1-13 cards 1-7 (via /dev/shm, under vnice). ORCH assigns owners.
3. Write an hourly RESULT with card-hours used vs available. Per-tick free counts are in ledger.txt; trin_read3 is using one card from about 11:40Z.
4. Watch events/trin_read for whether trin_read3 actually launched on 1-13 card 0.
5. At 22:45Z, write the final STATUS and a RESULT.
## Open questions
None.
