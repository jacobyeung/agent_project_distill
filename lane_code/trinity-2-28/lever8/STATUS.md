# lever8 STATUS (trinity-2-28; started 03:33Z 11-22; successor of lever7). Successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever8. lever7 folders read-only; NF-A kit used in place at /scratch/jjyeung/orch_n30/lever7/nfa/kit (T=orch_n30/tools). Orchard: tools/ossh.sh; never advanced; debug closed. Node agent iogov on 2-28 (pid 127712). Orchard ledger /scratch/jjyeung/orch_n30/lever8/work/ORCHARD_LEDGER.jsonl (copied from lever7). Status helper /scratch/jjyeung/orch_n30/lever8/work/tick.sh (Orchard q3.sh, inbox, newest events).
## Done by lever7 (see lever7 STATUS in its RESULT_rotate 0333Z): K5-S candidate; STAB closed; arm d both units (pooled undecided d-a +7.9, d-b +3.8); mirrors on trinity-0-13:/scratch/jjyeung/n30_mirror/lever7/ (gtcd_result sha 6625a453..., gtcd_ark sha 5ecc8dec..., nfa_kit3 sha d381b014...).
## lever8 now (UPDATED below each step)
- 04:28Z: 174328 (CPU check 3) RUNNING on preempt orchard-community-1 since 04:19:33Z (past the first-10-min deaths of checks 1-2); expected end ~05:40-06:00Z, then o_cfetch.sh. 03:53Z: one Orchard query returned empty; retry at 04:08Z succeeded. 174261 (not ours) RUNNING on general 3:07 h; 174265 pending behind it.
- R1/R2 fixed: /scratch/jjyeung/orch_n30/lever8/nfa/o_sub_preempt_r12.sh (sha256 ee6067c9bc87a572...): one scontrol update for Partition+ExcNodeList; any failure after the hold cancels with an E-code (E92-E95, real scancel outcome printed); Requeue=0 asserted before release; community-4 excluded only if sinfo lists it. Review 1 NO-GO (3 held-job exits) -> fixed -> fresh review 2 GO: nfa/rev12/REVIEW_R12.md, REVIEW_R12b.md. A cancelled attempt leaves a/70.txt, a/71.txt: the one attempt is spent; a retry needs the orchestrator.
- Design paper (item 2) DONE: RESULT 0339Z; files events/lever/files/masksrc/MASK_SOURCE_DESIGN.md; record distill_design/MASK_SOURCE_AFTER_TRACKER_DESIGN_20261122.md + INDEX line; plan section "the next whole-object mask source" and Status line. Rank: frozen detector per frame (J1 with h0 and box ceiling k) > fine-tune > own box head > multi-seed diag > deployable-seed tracker. Awaits ruling; build nothing until then.
- Plan record (item 3): current as of 03:39Z.
## Owed: NF-A (RULING 2310Z item 2), the noise floor of the served read in two item orders
- Token c8b836b4ae536 placed at /project/community/jjyeung/c8b836b4ae536 (150 items 37/37/38/38; one general job, 1 H100, 02:30:00, forecast 1.34 H100-h). Kit lever7/nfa/kit (SHA256SUMS_NFA 43 files). Reports nfa/REPORT_NFA.md, nfa/fix1/REPORT_FIX1.md, nfa/fix2/REPORT_FIX2.md; reviews nfa/review/REVIEW_NFA.md (scorer fix applied), nfa/fix1/REVIEW_FIX1.md GO, nfa/fix2/REVIEW_FIX2.md GO.
- History: CPU check 1 (174264) died because SAM 3 needs CUDA on the first distance item (RESULT 0130Z; fix 1: the CPU check runs the first camera item). CPU check 2 (174294) died because the random mkdtemp root tripped the opaque guard (RESULT 0227Z; fix 2: root /tmp/a<job>-<pid>). Both causes were returned; both fixes patched (o_patch, o_patch2; o_check True 1 02:30:00).
- NOW: CPU check 3 = Orchard 174328 on preempt, pinned to orchard-community-0..3, submitted ~02:56Z, PENDING at 03:30Z; expected 1.3-1.6 h once running.
- When it ends, from nfa/kit:
  - `timeout 300 bash $T/ossh.sh 'bash -s' < o_cfetch.sh > ../ret_cpu3.tgz` and check CPU.json cpu_reads_passed. On failure, decode with `decode_nfa.py <extracted a/c/1.log>`.
  - A new cause may be fixed and resubmitted after a review (ANSWER 0720Z). A repeated cause, or a death without one, goes to the orchestrator.
- GPU job (ANSWER 0032Z):
  - First `ossh < o_sub.sh` on general. It refuses while exp13_qwen_serve 174261 (not ours) holds the user's single general slot.
  - If general is still held 1 h after the check passes, make ONE preempt attempt with lever8/nfa/o_sub_preempt_r12.sh (R1/R2 fixed, re-check GO), pinned to the orchard-community H100 nodes, --no-requeue. Run: timeout 300 bash $T/ossh.sh 'bash -s' < /scratch/jjyeung/orch_n30/lever8/nfa/o_sub_preempt_r12.sh
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
