# gpu_fill STATUS (trinity-3-30), lane gpu_fill2. Updated 2026-11-16T17:30Z by the Devin lane (session 12:23Z-17:30Z, rotated).
## Goal
Briefs: orch_n30/briefs/gpu_fill.md (GPU rules), gpu_fill2.md (duties), gpu_fill2_d.md (Devin successor). Keep permitted free 48 GB Trinity cards working on distillation's queue until 22:30Z: confirm cards with two readings 5+ min apart, hand them with <UTC>_ORCH_CARD_<node>_<cards>.md notes into the owner's events folder; launch nothing; no Git, no deletion. Events only for questions, blockers, final results and rotate (ORCH 1228Z).
## Rules in force
- Main has GPU priority (USER 16:37Z, ORCH 1638Z ruling): before handing ANY card, read the newest B/INBOX_TO_DISTILL_ORCH_* (B=/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918); main's requests win at once; offer idle cards to main first while main asked in the last 24 h (pattern: B/INBOX_TO_NONTRAINING_ORCHESTRATOR_20261116T171913Z_distill_offer_1_13_cards45.md, 10-12 min deadline).
- trinity-1-13: /scratch 64 GB avail (below floor): nothing >1 GB there. Distillation /dev/shm/jjyeung cap 85 GB (ORCH 1504Z), ~84 used, only grows (no deletion): new 1-13 work must be zero-stage. Older /dev/shm dirs (~94 GB) do not count (REMOVAL_CANDIDATES.md).
- 0-28: no staging (/scratch 8 GB). trin_read needs a node with >=250 GB /scratch avail (1-3 floor 300). 3-30 /scratch at floor: lane adds <100 MB.
## Current holders (17:25Z)
- 1-13 cards 0,1: MAIN (r3178/r3179, 16:38Z); 6,7: MAIN (r3176/r3177, 16:30Z); 6-12 h, off every distillation assignment until main says free.
- 1-13 card 2: b05 pilot 2 (ORCH_CARD 1625Z, launched 16:40Z, <=4 A6000-h; if it fails fast branch O stops).
- 1-13 cards 3,4,5: b04 parity read (my note 1647Z card 3; ORCH notes 1651Z, 1724Z cards 4,5): own_depth partitions then scale_head, ~3 h per arm per card.
- Done today: b11 (cards 1,5, ended 16:31Z), b05 teacher (cards 2,3, 13:12-14:35Z), b14 towers (card 4, to 15:46Z).
## Card wants (order of need)
(a) trin_read: 1 card on a >=250 GB node (root staged on 1-3 and 1-18); lane trin_read3 rotated 14:52Z, check for its successor before handing. (b) H1-0 on step 544, up to 3 cards, through b04's reader once parity passes (ORCH 1612Z). (c) b14 MapAnything train-only arm, 1 card on 1-18 (no stage). (d) b05 full training only if pilot 2 passes. b09 dry run: not now.
## In flight (mine)
- tmux gpufill_loop on trinity-3-30 (loop.sh until 22:45Z). Each 10-min tick: tick.sh curls the monitor, parse.py, one tssh reading of 1-13 (read_shm.sh -> hist/s113_<T>.txt; shm_line.py line), cardhours.py line; writes events/gpu_fill/FREE_CARDS.md (+ notes.txt) and ledger.txt; alert.py appends CANDIDATE (free card on 1-3/1-18, or node with est. df Avail >=250 GB) and NEWEVENT (ORCH files) to alerts.log. Check: `tmux has-session -t gpufill_loop; tail alerts.log`.
- Helpers: chk.sh (compact view), waitchg.sh <sec> (blocks until a watched event/inbox/CANDIDATE change), read.sh (any node), read_shm.sh (adds /dev/shm du). Backups alert.py.v1, tick.sh.v1.
## Card-hours (cardhours.py, 11:20-17:23Z)
Distillation used 10.3 of 74.2 available card-hours on permitted 48 GB cards; idle mostly 1-13 (disk floor, /dev/shm cap) and 0-28 (disk). Since 17:25Z 1-13 is full.
## Next steps
1. Every 10 min: chk.sh or waitchg.sh; read new ORCH files in events/gpu_fill and new B/INBOX_TO_DISTILL_ORCH_*.
2. On a CANDIDATE: reading 1 (`bash B/orch_n30/tools/tssh.sh <node> 'bash -s' < read.sh > hist/rN_<node>.txt`), offer to main first, reading 2 after 5+ min; on 1-18 lnayak refills cards within minutes, so only agreeing readings count. Then ORCH_CARD to the owner in (a)-(d) order.
3. When b04 or b05 releases 1-13 cards: offer to main first, then H1-0 (after parity passes) per ORCH 1612Z; zero-stage only.
4. Watch handed cards: idle 20 min after a note -> QUESTION to owner; 20 min more -> withdraw.
5. 22:30Z: final STATUS and a RESULT (at most 15 lines).
## Open questions
None.
