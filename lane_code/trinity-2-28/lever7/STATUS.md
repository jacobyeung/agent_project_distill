# lever7 STATUS (trinity-2-28; started 23:19Z 11-21; successor of lever6; rotated ~03:35Z 11-22). Successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever7. lever6 folders read-only. Orchard: tools/ossh.sh; one job of ours on general; never advanced; debug closed. Node agent iogov on 2-28 is live (pid 127712). Orchard ledger lever7/work/ORCHARD_LEDGER.jsonl. Status helper: lever7/work/tick.sh (0-13 GPUs, Orchard job in work/q3.sh, governor lines, inbox).
## Done
1. K5-S: instability (default vs deterministic tower) separates gross from passing captures, AUC 1.000 on 10/6; candidate (RESULT 2335Z; ANSWER 2340Z accepted). Plan record sections K5-S and K5-S result; files events/lever/files/k5s.
2. STAB: priced on dev-S1 and closed (RESULT 0056Z; ANSWER 0058Z): no type passes; the tower's answer beats both swaps on camera types; R0-dev not spent. Plan record "STAB" and "STAB: result"; files events/lever/files/stab.
3. Arm d (GTC-D), both units, reviews GO before and after each:
   - ScanNet+ScanNet++ (84 items): d-a +10.5 [-1.4,+21.5], d-b +1.3 (RESULT 0217Z).
   - ARKit (33 items; frames re-decoded with k6's OpenCV 4.14.0, 576/576 anchors byte-equal; RESULT 0238Z): d-a +1.2, d-b +10.3 [+0.0,+30.9].
   - Pooled 117: undecided, d-a +7.9 [-1.7,+17.4], d-b +3.8 [-2.5,+10.0], share about 0.57 (RESULT 0328Z).
   - Plan record "GTC-D: result" (two sections). Files events/lever/files/gtcd. Next mask source: orchestrator's ruling (asked in RESULT 0328Z).
   - Mirrors on trinity-0-13:/scratch/jjyeung/n30_mirror/lever7/: mirror_gtcd_result.tar sha 6625a453dab8112e272dff1ba44b1e061eeec23377164b8210bf0831cbdc56c0; mirror_gtcd_ark.tar sha 5ecc8dec593cd96538ac7774baf6f403554e93eedf9bd717caea4818dbcacd01.
## Owed: NF-A (RULING 2310Z item 2), the noise floor of the served read in two item orders
- Token c8b836b4ae536 placed at /project/community/jjyeung/c8b836b4ae536 (150 items 37/37/38/38; one general job, 1 H100, 02:30:00, forecast 1.34 H100-h). Kit lever7/nfa/kit (SHA256SUMS_NFA 43 files). Reports nfa/REPORT_NFA.md, nfa/fix1/REPORT_FIX1.md, nfa/fix2/REPORT_FIX2.md; reviews nfa/review/REVIEW_NFA.md (scorer fix applied), nfa/fix1/REVIEW_FIX1.md GO, nfa/fix2/REVIEW_FIX2.md GO.
- History: CPU check 1 (174264) died because SAM 3 needs CUDA on the first distance item (RESULT 0130Z; fix 1: the CPU check runs the first camera item). CPU check 2 (174294) died because the random mkdtemp root tripped the opaque guard (RESULT 0227Z; fix 2: root /tmp/a<job>-<pid>). Both causes were returned; both fixes patched (o_patch, o_patch2; o_check True 1 02:30:00).
- NOW: CPU check 3 = Orchard 174328 on preempt, pinned to orchard-community-0..3, submitted ~02:56Z, PENDING at 03:30Z; expected 1.3-1.6 h once running.
- When it ends, from nfa/kit:
  - `timeout 300 bash $T/ossh.sh 'bash -s' < o_cfetch.sh > ../ret_cpu3.tgz` and check CPU.json cpu_reads_passed. On failure, decode with `decode_nfa.py <extracted a/c/1.log>`.
  - A new cause may be fixed and resubmitted after a review (ANSWER 0720Z). A repeated cause, or a death without one, goes to the orchestrator.
- GPU job (ANSWER 0032Z):
  - First `ossh < o_sub.sh` on general. It refuses while exp13_qwen_serve 174261 (not ours) holds the user's single general slot.
  - If general is still held 1 h after the check passes, make ONE preempt attempt with o_sub_preempt.sh, pinned to the orchard-community H100 nodes, --no-requeue. First fix review items R1 (partition and node exclusion in one scontrol update, or cancel on a partial failure) and R2 (verify Requeue=0 before release), and get a re-check.
  - If it is preempted, do not resubmit there; wait for general and post a RESULT.
- Then: o_mon.sh (at most once a minute), `o_fetch.sh > ../ret_g.tgz`, extract to ../ret/g, `/scratch/jjyeung/envs/p1cpu/bin/python -I -B score_nfa.py --returned ../ret/g --items ITEMS_NFA.json --out ../ret/scored`. RESULT per type: scores per order, paired difference with the room bootstrap, share of changed answers, and the ANSWER 1902Z rule (|diff| >= 0.5 points or > 5% of items changed). Record it in the plan record.
- Mirror: trinity-0-13:/scratch/jjyeung/n30_mirror/lever7/mirror_nfa_kit3.tar sha d381b014e7a16eebac8269cb52155a7ba3e0e6994c2413b4f288f842877002a4.
## Notes
- Do not run, from this lane, the commands that the builders' tools queued in /home/jjyeung/agent_project/agent/PENDING_USER_COMMANDS.md (a kit copy that would overwrite gtcd/kit, rehearsal reruns, small test-file cleanups). They are for the user to drop.
- Removal candidates (lane folder; nothing deleted):
  - gtcd/work/{test_dense,toy_tracks_d*,dense_try,rehearsal_cpu,test_dense_ark,toy_units,dry_launch_test_ark,kit_ark_tests}.
  - gtcd/arkit/frames (the cv2 4.10 decode, superseded by frames_k6); gtcd/dense_src (mp4s, 0.7 GB) once GTC-D closes.
  - nfa/review/tmp (53 MB); nfa/fix2/{t,x,pkg_new}; stab/work/npzchk; gtcd/kit/__pycache__; /tmp/rv2x.
  - trinity-0-13:/scratch/jjyeung/orch_n30/lever7/gtcd (dense frames, about 7 GB).
  - Orchard: c8b836b4ae536/*.pre1 and *.pre2, once NF-A is read.
## Open: the next mask source after arm d (RESULT 0328Z).
