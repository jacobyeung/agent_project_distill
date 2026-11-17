# tower_redecide STATUS (Devin Opus lane on trinity-1-3) — DONE 20261117T1745Z, lane exits
Brief: which frozen geometry tower serves distance (and camera) calls after the K1 label correction.
## Verdict
Keep G3T as the only tower (distance + camera) for R1; reader_r1 runs e09e45fda45db as built (no extra arm, no wait). DA3 is the single-tower challenger after (1) reviewed-guard K1 pricing + DA3 x own-scale arm and (2) a dev-S1 camera read with DA3 poses.
## Deliverables
- Record /data2/jjyeung/agent_project_data/distill_design/TOWER_REDECISION_20261117.md (sha256 67134e24...), INDEX.md line appended, GEO_TOWERS_K1_PRICING_20261116.md Status line updated (backups work/INDEX_before_tower_redecide.md, work/GEO_TOWERS_K1_PRICING_before_tower_redecide.md).
- RESULT event events/tower_redecide/*_RESULT_tower_redecision.md.
## Findings (detail in the record)
1. Second reader: 1,253/1,253 corrected labels reproduced by independent code (30/30 sample), 0 box conflicts; 56 of 88 undecided ScanNet++ boxes -> half, 0 full; 18 held-out + 109 train rows rest on doubly undecided boxes (GT-arm/corrected median 1.015).
2. Registered decide.py on corrected labels: Pi3X distance (held-out +6.44 [+3.42,+10.06] vs S4+G1), DA3 room; vs GD_reviewed (deployed, 75.05): Pi3X -1.67 [-6.08,+2.13] as priced / +1.32 [-1.22,+4.29] both answer; DA3 -4.03 / +1.46. GD-reference C-rule: distance G3T, room DA3.
3. K1 poses: Pi3X turn proxy -2.29 [-4.09,-0.67] (ARKitScenes tails), DA3 turn +1.02, move +3.26 vs G3T.
## Files (trinity-1-3 /scratch/jjyeung/orch_n30/tower_redecide/work)
second_reader.py, second_reader_all2.py, second_reader_summary.py -> second_reader/; reprice.py, reprice2.py -> reprice/ (caps_stored, caps_corrected, decide_*.json, REPRICE_TABLES.json, GD_REFERENCE_SENSITIVITY.json, REPRICE_EXCL_UNDECIDED.json); pose_k1.py -> pose_k1/POSE_K1.json; remote/r118.sh, r118b.sh (read-only scripts run on trinity-1-18), remote/poses_118.npz (sha256 ff2930e0).
## Mirror
trinity-1-18 /scratch/jjyeung/n30_mirror/tower_redecide/mirror_tower_redecide_1738Z.tar sha256 7ef59cd010d5f3e39e9f336d6d8cdca8568ad065490fc3bb12aac7e575b8e9b6 (equal both ends; extracted there). The record's final version is on /data2 (the mirror holds an earlier draft of work/TOWER_REDECISION_20261117.md).
## Notes
- rm_guard queued one of my commands (a heredoc script that removed its own /tmp file) in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md; it never ran and needs no running.
- Nothing running. Nothing owed.
