# r1_ops6 STATUS (Devin Opus high, trinity-3-30; started 20:52Z 2026-11-18; rotate by 02:20Z 11-19)
Lane folder /scratch/jjyeung/orch_n30/r1_ops6. Events .../orch_n30/events/r1_ops/. Ledger work/ORCHARD_LEDGER.jsonl.
## Recovered (20:52-21:10Z)
- rec/: lane_code copy (trinity-1-3 as of 11:07Z) of r1_ops (shared work dir of r1_ops..r1_ops5), r1_pkt, r1_ops2-5; 89,480 dedup'd files restored from DEDUP_trinity-1-3.tsv.gz (work/restore_dups.py). Not recoverable from lane_code: tars, sqlite, json >64 KB, files >512 KB, *.tpl (drv_c1 templates canary_c3/canary_submit/mon/pass_submit/yieldchk.tpl, u1.sh), PROOF_JOB.txt, anything after 11:07Z.
- snapm/snap_08f3a7b2 (C4 frozen, from n30_mirror tar b74ca3e5): p_08f3a7b2.tar 08f3a7b2... verified. snapm/snap_9dd2fbb7 (A frozen, from r1ops4 mirror tar 65d8279c): p_9dd2fbb7.tar 9dd2fbb7... verified.
- store/a2_vqa_v7: store v7 copied by IB tar pipe from trinity-1-18 n30_mirror/rows_r1/out; vqa/rows.sqlite 210b2534 verified.
- cf/final_evidence: COUNT_FIX_EVIDENCE_FINAL (9b0b68aa); B1 25c3db82, 17,879 lines.
- cp/: C' build root = snap_08f3a7b2 + rec/r1_pkt/work. work/view.sh runs a command in a bwrap view that maps cp -> /scratch/jjyeung/orch_n30/r1_pkt, rec/r1_ops -> .../r1_ops (with both snaps bound), store -> .../rows_r1/out/a2_vqa_v7 (ro).
- Ledger: r1_ops5's 21 lines + 172481 submit (reconstructed) + cancel.
## Orchard (20:54Z)
- 171377 COMPLETED 13:22:56Z. A end slot okh7/r/673bc60f/A.json: step 200, verified true, archive 76bed248..., manifest c11b603f..., checkpoint_000200_a09ca55b...; m200 artifact.json present.
- 172481 (held C proof) had been released (EligibleTime 19:49:03Z, same minute main's held jjy_* jobs ran and FAILED on advanced) and RUNNING on general 1h05m; I scancelled it 20:54:04Z (ORDER 1108Z item 3: moot; it blocked general for the step-200 read).
- squeue empty after cancel; advanced free.
## Next
- Codex Astra high C' build (brief work/brief_cprime.md), then review (devin_bg), chain, launch on ORDER 1108Z (sha 1f3dff81).
