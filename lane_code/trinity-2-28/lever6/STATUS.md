# lever6 STATUS (trinity-2-28; started 19:53Z 11-21; successor of lever5). Successor resumes from this file alone.
Lane dir /scratch/jjyeung/orch_n30/lever6. Ledger lever6/work/ORCHARD_LEDGER.jsonl (older: lever5/work/). Orchard: tools/ossh.sh; general one job of ours at most; never advanced; /project floor 5 GiB (179 GiB free 21:13Z).
## Done
- R0 pair 2: different rooms; R0-dev keeps 98 rooms (RESULT 1959Z). Item 4 closed.
- K5 first kit died in its CPU check (174236; missing bwrap bind dirs). Rebuilt as token adba6b82bdb9d (lever6/k5b/kit, FIX_NOTES.md); review GO (lever6/k5brev/REVIEW_K5B.md). Placed and verified at 21:13Z (6,748,442 B; the ossh call hung, rc 124, but every file matches).
- NF replay harness built (lever6/nf/kit/REPORT_NF.md); camera types only. Distance and room are UNMEASURED.
- GTC: registered in the plan record ('Rank 1 follow-up (GTC)'). Review 1 NO-GO (subset code missing), fixed (lever6/gtcfix/FIX_NOTES.md). Tracker ran on trinity-0-13 card 0, 21:02-21:08Z, exit 0, 92 units. Outputs are on 2-28 in lever6/gtc/out/track (also on 0-13, same path).
## Running
- K5b: CPU check 174244 PASSED (lever6/k5b/ret/cpu/4.json). GPU job 0 174247 submitted 21:53Z (PENDING at 21:54Z); poller in background (lever6/work/o_stat_g0.sh).
  - Next: fetch with `timeout 300 bash T/ossh.sh 'bash -s' < k5b/kit/o_fetch0.sh > k5b/ret_g0.tgz`, extract to k5b/ret/g0.
  - Then o_sub1.sh (pins to job 0's node; needs job 0 COMPLETED), then o_fetch1.sh > ret_g1.tgz -> ret/g1.
  - Then `p1cpu python -I -B k5b/kit/score_k5.py --returned ret/g0 ret/g1 --reference kit/REFERENCE_K5.json --out ret/scored`, and a RESULT per dataset, leading with A1 vs A2 (default orders).
  - Then the NF replay (lever6/nf/kit/REPORT_NF.md) with --k5 k5b/ret/g0 k5b/ret/g1, and a RESULT with the ANSWER 1902Z rule.
- GTC-B (t_big): registered in the plan ('Rank 1 follow-up (GTC-B)'); ORCH ANSWER 2137Z says yes.
  - Build running (lever6/gtcb/BRIEF_BUILD.md -> lever6/gtcb/kit/REPORT_GTCB.md).
  - Then a fresh review; copy the new files to 0-13; a fresh nvidia-smi reading; launch in tmux on 0-13; copy back; relift; RESULT.
  - The RESULT must carry: b-a, share of e-a, seed median and count under 200 px, P/R, per dataset, and what a deployable seed needs, with the held measurements (lever6/gtcb/HELD_MEASUREMENTS.md).
- GTC DONE: review 2 GO; reading run 21:2xZ -> undecided (t-a +2.7 [-9.5,+13.6]); seed-200 subset +14.0 [+3.8,+24.5]; s-a -4.8. RESULT 2131Z; plan record 'Rank 1 follow-up (GTC): result'; files events/lever/files/gtc/. QUESTION in that RESULT: t_big arm (GT seed on largest anchor, both directions), default yes, start after K5 GPU jobs move.
- Mirror: lever6/work/mirror_lever6.tar (nf, k5b, gtc kits + RELIFT_GTC.json) sha 3d397e16...965a at trinity-0-13:/scratch/jjyeung/n30_mirror/lever6/ (sha matches). GTC inputs and tracks also on 0-13 under the same paths.
## Removal candidates: lever6/REMOVAL_CANDIDATES.md; lever6/nf/REMOVAL_CANDIDATES_NF.txt; Orchard /project/community/jjyeung/a51f1ee88f0c9.
