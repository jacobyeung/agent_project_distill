# gpu_fill STATUS (trinity-3-30), lane gpu_fill2 (Devin). Updated 2026-11-16T14:20Z. Session started 12:23Z; rotate by 18:15Z.
## Goal
Briefs: orch_n30/briefs/gpu_fill.md (GPU rules) and gpu_fill2.md (duties). Keep permitted free 48 GB Trinity cards working on distillation's queue until 22:30Z. Hand confirmed cards to owning lanes with ORCH_CARD notes; launch nothing; no Git, no deletion.
## Done
- 1-13 card 0 handed to trin_read at 11:40Z; trin_read3 declined (1151Z QUESTION, needs 86-122 GB). ORCH 1221Z: option B, wait for a node with >=250 GB /scratch avail; no /dev/shm root.
- K1 own phase goes to Orchard (k1_ops3 ORCH 1221Z GO d1553118); no Trinity card owed.
- 12:28Z RESULT queue_fit_and_hour1 (NEXT_QUEUE fit on 1-13; ~12 card-hours free, 0 used) and QUESTION devshm_small_stages (default: no /dev/shm staging; hold 1-13 for main).
- alert.py: CANDIDATE now uses scratch_avail ~ total-used-5%*total >= 250 GB, or any free card on 1-3/1-18 (backup alert.py.v1).
- ORCH 1229Z: /dev/shm/jjyeung on 1-13 allowed up to 60 GB total; b11 first, then b05 teacher pass (up to 4 cards) after CPU tests; reuse one export; stages listed in each lane's REMOVAL_CANDIDATES.md; vnice; main told first. ORCH 1228Z: no checkpoint events.
- 12:38:25Z told main: B/INBOX_TO_NONTRAINING_ORCHESTRATOR_20261116T123825Z_distill_1_13_devshm_probe_teacher.md (objection deadline 12:48Z). Reading 1 of 1-13 at 12:38:32Z: all 8 empty (hist/r4_trinity-1-13.txt).
- 12:49Z handed 1-13 card 1 to b11: events/b11_presence/20261116T1249Z_ORCH_CARD_trinity-1-13_1.md (readings 12:38:32Z, 12:48:47Z hist/r4,r5; no main objection). b11 kit ready (1244Z RESULT), stages export+env+frames to /dev/shm/jjyeung/b11_presence over IB from 1-18.
- 12:59:00Z reading (hist/r6): b11 running on 1-13 card 1 (35.7 GB, 66%); /dev/shm 166->186 GB used.
- 12:59Z handed 1-13 cards 2,3 to b05 (ORCH 1255Z): events/b05_owngrd/20261116T1259Z_ORCH_CARD_trinity-1-13_2_3.md; K1 teacher pass shards 0/2,1/2, ~20 GB /dev/shm/jjyeung/b05, 5-7 card-hours.
- 13:10:05Z reading (hist/r7, script read_shm.sh adds du of /dev/shm/jjyeung/*): card 1 b11 100% util; cards 2,3 not yet used (b05 staging, /dev/shm/jjyeung/b05 13G); exports 18G; b11 2.5G. Older dirs ~94 GB (g13 74G etc.) listed in REMOVAL_CANDIDATES.md.
- 13:11Z handed 1-13 cards 4,5 to b14 (ORCH 1258Z note), conditional on fitting ~21 GB left of 60 GB: events/b14_k1towers/20261116T1311Z_ORCH_CARD_trinity-1-13_4_5.md. QUESTION 1311Z old_devshm_1_13 (default: older dirs do not count).
- ORCH 1312Z: older /dev/shm dirs do not count; keep RAM total visible in FREE_CARDS.md (notes.txt is appended each tick; refresh it after each reading). b05 launched 13:12Z on cards 2,3 (13 GB staged, ~75 min for 286 captures).
- ORCH handed 1-13 card 4 to b14 directly (1318Z); b14 MoGe-2 on card 4 to ~14:00Z, then DA3 (ORCH 1327Z allows 20.8 GB peak). Card 5 not b14's. Distillation /dev/shm ~54/60 GB at peak.
- Hour 13:30Z card-hours: 11:20-13:30Z ~25 card-hours free on permitted nodes (12 per tick until 12:50Z, then 1-13 use); distillation used ~2.3 (b11 card 1 from ~12:55Z, b05 cards 2,3 from 13:12Z, b14 card 4 from ~13:20Z). Blockers: disk floor (0-28 8 GB, 1-13 65 GB), /dev/shm cap 60 GB, kits awaiting ORCH GO/reviews (b09 dry run, b04 parity read on AWS, b03 EAT-1 on H100).
- 13:51Z handed 1-13 card 5 to b11 for direct.py (ORCH 1349Z): events/b11_presence/20261116T1351Z_ORCH_CARD_trinity-1-13_5.md (readings r7 13:10:05Z, r8 13:51:19Z). b11 scorer on card 1 ends ~17:10Z.
- 14:05-14:09Z: b11 review GO; b11 direct.py relaunched on card 5 at 14:03:38Z (first start died: ninja missing). b14 runs Pi3X next on card 4 (distillation /dev/shm ~59 GB); MapAnything waits for 1-18. b04 fetches step-544 heads (<=2 GB) into /dev/shm/jjyeung/exports/m544_heads (cap 62 GB for this alone); parity read needs its review GO.
- 14:17:26Z reading (hist/r9): cards 1-5 in use (card 5 42.8 GB loaded, 0% util); distillation /dev/shm 56 GB. Free 0,6,7.
## Card wants (order of need)
(a) trin_read: 1 card, node with >=250 GB /scratch avail (1-3 floor 300 + stage). (b) b05_owngrd: SAM 3 teacher pass, up to 4 cards, once its runner exists (CPU stage). (d) b04_e2ehook parity read (ORCH 1334Z): one free 1-13 card after its review GO, if extra /dev/shm stage <=6 GB (reuses /dev/shm/jjyeung/exports); write ORCH_CARD with fresh readings when the GO lands. (c) b11_presence: 1 card 1-2 h, best on 1-18 (export, vLLM env, K1 frames local there); default waits for ORCH_CARD in events/b11_presence.
## In flight
- tmux gpufill_loop on trinity-3-30 (loop.sh until 22:45Z): every 10 min tick.sh curls the monitor, writes events/gpu_fill/FREE_CARDS.md, appends ledger.txt; alerts.log gets CANDIDATE / NEWEVENT (ORCH files) lines. Check: `tmux has-session -t gpufill_loop; tail alerts.log`.
## Next steps
0. 1-13: card 1 b11 scorer (~17:10Z), 5 b11 direct (13:52Z; idle check 14:12Z, withdraw 14:32Z), 2,3 b05 (ETA ~14:30Z), 4 b14. Free 0,6,7 (<=6 GB new stage; b04 after review GO). Check each 10 min via chk.sh; reading via read_shm.sh at most every 30 min; refresh notes.txt after each reading.
1. Every 10 min: read alerts.log, inbox/, new ORCH files. On a CANDIDATE: reading 1 now and reading 2 after 5+ min, `bash orch_n30/tools/tssh.sh <node> 'bash -s' < read.sh > hist/rN_<node>.txt`; if empty and df Avail clears the floor, write <UTC>_ORCH_CARD_<node>_<card>.md to the owner (a, b, c order), naming both readings and vnice (normal priority only on 0-13). Tell main first if staging >20 GB.
2. Watch handed cards: idle 20 min after hand-off -> QUESTION to owner; 20 min more -> withdraw.
3. Hourly: card-hours used vs available into STATUS.md only (ORCH 1228Z: events only for questions, blockers, final results, rotate); scan newest RESULT in each events/b*/ for card requests.
4. If ORCH answers the /dev/shm QUESTION yes: re-read 1-13 twice and hand cards to b11 (1) / b05 (up to 4) with the /dev/shm condition and main told.
5. 22:30Z: final STATUS and RESULT.
## Open questions
None (1228Z answered by ORCH 1229Z).
