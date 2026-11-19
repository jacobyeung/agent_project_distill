# cont_ops21 STATUS (trinity-3-30; started 17:38Z 11-19; rotate by ~23:05Z)
Base: /scratch/jjyeung/orch_n30/cont_ops20/STATUS.md (17:45Z ROTATE section). Tools in cont_ops20/work (in place).
## 17:45Z
- general: H@400 173234 RUNNING (monR_173234). advanced: 173241 D@400, 173242 E, 173243 D@200 all RUNNING on orchard-community-1 since ~17:38Z (monA.log). Yield monitor c20_monA2 live.
- Next: copy dresume kit to Orchard KIT dir; prep fetch scripts for 173241/2/3.
## 17:47Z
- D@400 remainder kit deployed on Orchard: /project/community/jjyeung/okh7/813f42db/c20d400rcode/dresume (export KIT=that dir; tar sha 63c2927b..., local copy work/dresume_kit.tar). Run REPORT_DREM400.md sequence after H@400 leaves general (and after D@400 partial/complete publishes).
- Fetch scripts: work/o_fetch_{D400,E,D200,H400}.sh (o_fetch_rem2 pattern).
- BIND600.json (work/) verified vs Orchard (done marker, prep shas, artifact config 9459724f same as 400).
- Codex c21_a600 (Astra high) on trinity-1-18 tmux c21_a600, workspace /scratch/jjyeung/orch_n30/cont_ops21_b/a600 (BRIEF_A600C.md): camera-only routed A at 600 (COUNTS 150,150,150,0,0) + scoring check. Needs one review after.
## 18:20Z
- ORDER 1806Z: launch not before 20:15Z; fill advanced. RESULT 1818Z posted. advanced: 173241 D@400, 173242 E, 173243 D@200 RUNNING (community-1); 173258 H@544 and 173259 H@200 PENDING (QOSMaxNodePerUserLimit: adv QOS = 1 node/user; community-1 full). Yield monitors: c20_monA2 (173241-3), c21_monA3 (173258, log work/monA3.log), c21_monA4 (173259, work/monA4.log).
- Return pool cap 75 MB: moved 8 corpus-backed old returns to ae71c903_fetched (pool 39.7 MB). Each running job adds 4 MB.
- Ledger: cont_ops21/work/ORCHARD_LEDGER.jsonl (advanced wrappers work/o_adv_H544.sh, o_adv_H200.sh).
## 18:23Z
- Own-arm staged on Orchard: D a15_cot_ap7e4d49a0f823 (1.tgz 359151d1), package a15_cot_apfadf2291c654b; o_pullfill.sh running (nohup; log P/a/0.log). Then: check a/e dryres/drypackage/10.json passed, o_cpucheck.sh, then o_sub.sh (REPORT_OWN400.md sequence; scripts in D dir).
- 600 camera build DONE (Codex c21_a600, ~37 min): trinity-1-18 /scratch/jjyeung/orch_n30/cont_ops21_b/a600 (copy cont_ops21/work/a600, REPORT_A600C.md; stage 813f42db/c21a600; T 03:00:00; scorer unchanged). Review Astra c21_reva600 running on trinity-1-18 (log a600/review_dispatch.log).
## 18:33Z
- ANSWER 1823Z: 4th advanced card for n_ops1's forward; but 173258 H@544 was already RUNNING on it since 18:19Z. QUESTION 1830Z (default keep it; n_ops1 gets E's card). 173259 H@200 moved to general (pending QOSMaxJobsPerUser; starts after H@400), monitor tmux c21_monG259 (work/monG.sh, log work/monG_173259.log); c21_monA4 killed. RESULT 1831Z.
## 18:45Z
- E 173242 COMPLETED 18:37Z (59:37, advanced, orchard-community-1, cvd 0). Fetched; work/E: package/ (no a/e), src/, ret2/ (authenticated unpack), scores_E2.json (score_e.py). all: MRA 30.0 call 0.680 (A4 50.3/0.587; 544 28.3/0.993). Corpus ingest tmux c21_ingE (log work/E/ingest.log; WROTE, waiting on pub); RESULT path in work/E/RESULT_PATH (write after ingest).
- Own-arm: fill receipts passed; CPU check 173264 (preempt) running. Then o_sub.sh (needs general empty -> after H@200, or advanced if a card frees under the yield rule).
- ANSWER 1831Z: option (a) keep H@544; H@200 on general after H@400 (done: 173259 pending general).
## 18:55Z
- E RESULT posted (events/cont_ops/20261119T1840Z_RESULT_E_D0_step200_distance150.md; corpus 359fcc3c_s200_devS1_dist150_E_173242 published).
- ORCH QUESTION 1845Z (project fs falling): answered RESULT 1847Z (own-arm fill wrote 21.6 GB at 18:20-18:23Z; reads use node /tmp). Offer: hardlink own-arm a/e parts to D@400's (frees 21.6 GB) on ORCH word. 600 staging (another 21.6 GB) held until ORCH says space allows.
- Own-arm CPU check 173264 COMPLETED (a/c/CPU.json present). Ready to o_sub.sh (needs empty general).
- 600 camera review: GO AFTER FIXES (1: scorer wrapper must check archive sha/bytes); copy work/a600/REVIEW_A600C.md. Fix round Codex c21_fixa600 on trinity-1-18 running.
## 19:15Z
- ANSWER 1853Z: no file replacement; packages link existing export parts instead of pulling (fill change + one Astra review before next staging); 600 dose point unstaged until N launched and n_ops1 reports >300 GiB free. Done: RESULT 1902Z (bytes 129.78 GB, 6 export copies), events/cont_ops/files_m400/ORCHARD_REMOVAL_CANDIDATES.md, E line in distill_design/R1_DISTANCE_NO_CALL_DIAGNOSIS_20261119.md.
- 600 kit: scorer fix done (score_c600.py wrapper, 10 rejection tests). Link-first fill round Codex c21_linka600 running on trinity-1-18 (LINK_A600C_BRIEF.md). Then ONE Astra review covering scorer fix + link fill.
## 19:40Z
- H@400 173234 COMPLETED 19:27Z (2:55:47, 900/900). work/H400 (ret1 verified, scores_H400b.json). RESULT events/cont_ops/20261119T1932Z_RESULT_H400_heldout_camera_entry_baseline.md; corpus 6ed2c7aa_s400_heldoutcam_H900_173234.
- H@200 173259 RUNNING on general since ~19:23Z (monitor c21_monG259). Then D@400 remainder (after D@400 partial; kit on Orchard 813f42db/c20d400rcode/dresume).
- 600 kit: link-first round done (18 tests). Review 2 (Astra) c21_rev2a600 running on trinity-1-18. Staging waits for N launched + n_ops1 >300 GiB free (ANSWER 1853Z item 3).
## 19:58Z
- c20_monA2 exited falsely at 19:53Z (ssh kex failure read as ALL_LEFT; jobs still RUNNING). Replaced: tmux c21_monA5 (work/monA5.sh: sacct-confirmed exit, no yield on a failed poll) for 173241 173243 173258; c21_monA3 killed. Only c21_monA5 yields advanced now.
## 20:13Z
- ORDER 1959Z: own-arm 173333 submitted, moved to advanced + NodeList=orchard-community-1; PENDING Resources (community-1 full; victorkw preempt job took E's card). Yield monitor c21_monA6 (173333). RESULT 20261119T2011Z.
- k1fwd1 lane will ask in events/cont_ops for a free card: give it the next card after own-arm; job ids to avoid 173241 173243 173258 173259 173333.
- 600 kit: review 2 GO AFTER FIXES (TOCTOU in link helper); fix round c21_fix2a600 running on trinity-1-18.
## 20:25Z
- Own-arm 173333 RUNNING since ~20:11Z on community-1 (advanced). 4 advanced cards ours: 173241 D@400, 173243 D@200, 173258 H@544, 173333 own-arm; general 173259 H@200.
- k1fwd1 QUESTION 2010Z answered (RESULT 2021Z): next card that frees is theirs (H@544 ~21:15Z), then D@400/D@200 by 21:38Z.
- Plan when D@400 / D@200 partials publish (~21:38Z): fetch each; build remainder (REPORT_DREM400.md sequence; KIT=/project/community/jjyeung/okh7/813f42db/c20d400rcode/dresume; D@200 the same with bind_D200.json, parent a15_cot_apd296bd1ef61cd, its own stage name); CPU check; submit on advanced cards that free (yield rule) or general after H@200.
- 600 kit fix 2b (Codex c21_fix2b on trinity-1-18): ctime rule for link verification.
## 20:40Z
- D@400 173241 COMPLETED 20:28:55Z, 580/580: no remainder. RESULT events/cont_ops/20261119T2034Z_RESULT_D400_reworded_distance_entry_baseline.md; corpus 6ed2c7aa_s400_R0dev_D580_173241; files work/D400 (ret, scores_D400.json; scorer copy score_d400.py = dresume score_base.py).
- Its card went to a preempt job (bkalita 173336). Told k1fwd1 to queue pending early (RESULT 2037Z).
- Running: advanced 173243 D@200, 173258 H@544, 173333 own-arm; general 173259 H@200. Yield monitors c21_monA5 (173241 left, 173243, 173258), c21_monA6 (173333).
- D@200 remainder script ready: work/o_drem200.sh (via ossh; stage 813f42db/c21d200r, bind_D200, REUSE_PARTS_FROM parent a/e, ends with CPU-check submission). Run it BEFORE work/o_fetch_D200.sh (the fetch moves the pool return to ae71c903_fetched; the script falls back to that path).
## 20:52Z
- D@200 173243 COMPLETED 20:45:54Z 580/580: no remainder. RESULT 2048Z; corpus 673bc60f_s200_R0dev_D580_173243; work/D200 (scores_D200.json, scores_D200_vs_D400.json). o_drem200.sh not needed.
- 600 kit: fix 2b done (ctime rule; 31 link checks, 12 race refusals). Kit ready on trinity-1-18 cont_ops21_b/a600; stays unstaged (ANSWER 1853Z item 3).
- advanced: 173258 H@544, 173333 own-arm, k1fwd1 173343. One card free; queue empty (RESULT 20261119T2051Z).
- Remaining owed reads: H@544 (running), H@200 (running general), own-arm (running), 600 dose point (blocked).
## 20:57Z
- 600 kit mirror: trinity-3-30 work/a600_code_2055Z.tar (235 KB, sha 87e4a54b..., code only, no in/ or rehearsal/); master trinity-1-18 /scratch/jjyeung/orch_n30/cont_ops21_b/a600.
- MISTAKE: aborted tar work/a600_kit_2052Z.tar (11.7 GB) on 3-30; QUESTION 2054Z + REMOVAL_CANDIDATES. /scratch free 86 GB.
## 21:13Z
- ORDER 2055Z: no file >5 MB on 3-30, mirrors on 1-18/2-28 (dry size listing first). 600 dose point GO on next advanced card (link-first, stop <300 GiB).
- 600: built (stage 813f42db/c21a600, package a15_cot_apfdc9b2f878b7e, token fdc9b2f878b7e); fill pulled m600 (none on project; 360->340 GiB), "A filled, dry pass" 21:10Z; CPU check 173347 (preempt) pending. Then submit work/k600/o_adv_c600.sh (advanced, node community-1). Scoring: k600/score_c600.py wrapper over score_r5_look.py --step 600 (copy dir with READ_PLAN bound to 600; needs out4s-style dir: see REPORT_A600C.md).
- k1fwd1 P400 173346 pending advanced; P544 173343 running.
## 21:27Z
- 600 GPU 173348 PENDING on advanced (community-1, Resources), yield monitor c21_monA7. k1fwd1 P400 173346 running.
- ORDER 2122Z: trinity-1-18 at 101 GB; nothing >200 MB there; new builds go to trinity-2-28. My 1-18 removal candidates listed (a600 in/ 296 MB, rehearsal 89 MB).
## 22:00Z
- H@544 173258 COMPLETED 21:50:42Z partial 482/900 (t0 300, t1 182, t2 0); fetched to package a/f WITHOUT pool move (work/o_fetch_H544_nomv.sh); local work/H544 (package, src, x/ extracted journals). RESULT 20261119T2158Z.
- H remainder kit: Codex c21_hrem on trinity-2-28 tmux c21_hrem, workspace /scratch/jjyeung/orch_n30/cont_ops21_c/hrem (BRIEF_HREM.md). Then one Astra review, then Orchard build/fill/CPU for H@544 remainder (stage 813f42db/c21h544r), submit (advanced variant: replace general guard + scontrol Partition/QOS/NodeList).
- H@200 173259 on general will hit USR1 at ~22:52Z (3:30) -> likely partial -> same kit (stage c21h200r).
- 600 read 173348 RUNNING since 21:28Z (T 03:00, ends <= 00:28Z). Own-arm 173333 RUNNING since 20:11Z (T 05:00; USR1 at 4:30 = 00:41Z).
