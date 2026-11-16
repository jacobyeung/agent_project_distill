# gpu_fill STATUS (Claude subagent on trinity-3-30), for a successor
Updated: see bottom stamp. Window ends 22:45Z 2026-11-16.
## How to run
- Each tick (10 min): `/scratch/jjyeung/orch_n30/gpu_fill/tick.sh` (one curl of the monitor page, parse.py, overwrites events/gpu_fill/FREE_CARDS.md, appends ledger.txt with free-card count).
- Confirm a card: `bash .../orch_n30/tools/tssh.sh <node> 'bash -s' < read.sh > hist/rN_<node>.txt` twice, 5+ min apart (nvidia-smi + df /scratch + /dev/shm).
- Usable = card empty in both readings AND node /scratch can stay >=150 GB free after staging (~30-40 GB for trin_read root) AND permitted node. Then write events/trin_read/<UTC>_ORCH_CARD_<node>_<card>.md (both readings, vnice unless 0-13, 20 GB main notice status).
## State
- 11:19-11:21Z reading 1: 1-13 all 8 A6000 empty, /scratch 65 GB free; 0-28 cards 0,3,4,6 empty, /scratch 8 GB free; 0-13 all 7 busy, 124 GB free. 1-3 (root staged, 908 GB free) all 8 held by yimingg2; 1-18 (root staged) all busy.
- Disk floor blocks every free card. No card note written.
