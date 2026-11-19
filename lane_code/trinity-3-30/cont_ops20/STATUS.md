# cont_ops20 STATUS (trinity-3-30; started 14:17Z 11-19; rotate by ~19:45Z)
Base state: /scratch/jjyeung/orch_n30/cont_ops19/STATUS.md (14:17Z section). Brief: orch_n30/briefs/cont_ops20_d.md. Tools stay in cont_ops19/work (used in place).
## 14:20Z
- Routed A rerun 173060 RUNNING since 12:59Z (orchard-community-4); monitor tmux monR_173060 (cont_ops19/work/monR_173060.log). Expected end 15:00-15:20Z. Then J=173060 bash cont_ops19/work/post_A400.sh.
- chain600 armed (tmux chain600), waiting for m600 .done + free general.
- Queue after A: D@544 rem2, D@200, E, H@544, H@200, own-arm.
## 14:32Z
- D@544 three-segment scorer: work/score_d3.py (copy d3/; spec keys items,p0,a0,e0,r0,items1,p1,...,r2 + optional compare). Parent (d544ret: pkg, f/) + rem1 partial (/dev/shm/c19r/pkg2/a15_cot_apd09f959256d87 a/f; tar backup cont_ops19/work/drem1/pkg.tar) checks pass (d3/TEST_D3.txt). Items: d3/items/dist580.json (parent ff9795a8), d3/rem1_dist580.json (bbaa5527), d3/REM544_2.json (37180266).
- Review 1 (codex_runs/20261119T142032Z_c20_revd3; copy d3/REVIEW_D3.md) GO AFTER FIXES -> staged_inputs() added; confirm-review running tmux c20_revd3b.
- Rem2 GPU scripts: work/o_sub_rem2.sh (squeue + o_sub_D.sh), work/o_fetch_rem2.sh. Monitor monR6.sh (J P LB).
## 15:15Z
- ROUTED A 400 DONE: 173060 COMPLETED 636/636; RESULT events/cont_ops/20261119T1512Z_RESULT_r1_m400_routed_A_H3_STOP_camera_displacement.md (H3 STOP: displacement -0.73 [99.29% -1.51,-0.14]; distance calls 113/150; MRA 47.53). Corpus 6ed2c7aa_s400_devS1_routed_A10b. Post output work/post_A400_173060.out.
- Confirm-review of score_d3: GO (d3/REVIEW_D3_2.md).
- D@544 rem2 173202 submitted 15:11Z on general, RUNNING; tmux monR_173202 (monR6; log cont_ops19/work/monR_173202.log). T 01:30. After: fetch (work/o_fetch_rem2.sh), pull pkg (no a/e), score_d3 spec.
- Next on general: D@200 (a15_cot_apd296bd1ef61cd, T 04:00, cont_ops18/dbuild/o_sub_D.sh), E, H@544, H@200, own-arm. Note ORCH 1511Z to swarm_opt3: reads may move to trinity-2-28 cards (they hand me a command).
## 15:35Z
- ORCH ORDER 1520Z (H3 level): item 1+3 RESULT posted 1526Z (H3 STOP holds at 99.82%: displacement [-1.68,-0.07]; cause: all 26 differing items have identical calls, tower returns ~1.4% larger scale-head output at 400; files_m400/H3_A400_*).
- Item 2: out4s/score_r5_look.py (--step required; 99.29% at 200, 99.82% later; export-pin check for every step != 544) + out4s/test_score_r5_look.py (fails on score_r5_400, passes on new). Real 400 run: work/scoresAB_look400. Astra review running tmux c20_revlook (work/look_rev/BRIEF.md).
- Facing tool: h1face7/face.py used fixed 1-0.05/8 (99.375%) for every look; registered text says H1's level. Copy h1face7/face_look.py (--step required). At 400 with 99.82%: toward -3.33 [-10.78,+2.01]; toward-hard -10.00 [-26.32,+0.00] (no longer wholly below zero; the 1022Z mark was at 99.375%). VSTI tool: 95% only (no H1-level test). Direct: post_r1_c.sh (pooled tool, later-look levels).
- At 600 use: score_r5_look.py --step 600 (in an out6s copy dir with READ_PLAN export_binding = BIND600), face_look.py --step 600.
## 15:45Z
- RULING 1533Z: leg R1 ends at 400; chain600 tmux killed (disarmed); 600 only a camera dose point after N's entry baselines. ANSWER 1535Z: face_look needs one Astra review (low priority); correction filed files_m400/FACE_m400_CORRECTION_level_9982.txt.
- 173202 monitor now monR.sh (tmux monR_173202).
- Entry baselines H@400 then D@400: Codex c20_hd400 RUNNING on trinity-1-18 tmux c20_hd400, workspace /scratch/jjyeung/orch_n30/cont_ops20_b/hd400 (BRIEF_HD400.md; in/ has BIND400, A10b INPUTS parts shas, m400.done). 1-18 load was 78 at launch.
- Then: review, Orchard build (STEP=400), place/fill REUSE_PARTS_FROM A10b a/e, CPU check, GPU.
## 16:25Z
- D@544 rem2 173202 COMPLETED; merged 478+3+99 = 580 complete (work/d3/SCORES_D544_merged.json, post work/d3/post_rem2.out). Corpus ingest tmux c20_ingD (3 segments, log work/d3/ingest.log); RESULT after it (path in work/d3/RESULT_PATH).
- H@400 (entry baseline): Astra review GO (codex_runs/20261119T155538Z_c20_revh400). Orchard stage 813f42db/c20h400, package a15_cot_apd7a6db629db02 (filled, dry pass, CPU 173232 PASS). GPU 173234 submitted 16:2xZ on general; tmux monR_173234 (monR.sh). Scripts work/hd400/h400/. Fetch: P/3.py fetch (REPORT_HD400 sequence) or o_fetch pattern. Score: hd400 hcam/score_h.py (on trinity-1-18 /scratch/jjyeung/orch_n30/cont_ops20_b/hd400/hcam; local copy work/hd400/h400/score_h.py).
- D@400: Codex c20_d400f (finish validation with in/B5_1.tgz) running on trinity-1-18; then one review, Orchard build STEP=400, fill, CPU, GPU after H@400.
## 16:50Z
- D544 RESULT posted (events/cont_ops/20261119T1615Z_RESULT_D544_merged_580_complete.md). Corpus re-ingest tmux c20_ingD2 (seg0b, seg1b, seg2; timeout 5400; log work/d3/ingest2.log); first try's two 0-byte .copying stubs in REMOVAL_CANDIDATES.md.
- H@400 173234 RUNNING (budget ~3 h; end ~19:30Z), monitor monR_173234.
- D@400 package a15_cot_apda6f7936c1779 (stage 813f42db/c20d400): Astra GO, filled, CPU 173235 PASS. Submit after H@400: P=/project/community/jjyeung/okh7/a15_cot_apda6f7936c1779 T=04:00:00 with work/hd400/d400/o_sub_D.sh (wrap like h400/o_sub_h400.sh); partial expected (budget 19,595 s) -> remainder via dresume (make_items_remainder.py / build_remainder.py, as RESUME_D.md).
- face_look review tmux c20_revface (work/face_rev).
- Fetch H400: work/hd400/h400/o_fetch_h400.sh, then pull pkg (no a/e) and score with hcam/score_h.py (--return R --package BUILD.json) from trinity-1-18 copy.
## 17:07Z
- Corpus D@544 published: 469ddece_s544_R0dev_D580_seg0b_172957, _seg1b_173053, _seg2_173202 (ingest2.log rc 0/0/0).
- face_look.py: review GO AFTER FIXES, fix applied (RESULT 1656Z).
- m600 export exists (r1_ops10 1704Z: object 6ed2c7aa_m600.tar sha 673c147c..., parts 4x5395758080; artifact 0db794d9). Use only for the camera part of read A as a dose point, AFTER H@400 and D@400 (+remainder). Not built yet (needs BIND600.json + camera-only variant of gen400b A).
- Codex c20_drem400 (D remainder kit for step 400) running on trinity-1-18.
## 17:45Z ROTATE to cont_ops21 (exact state)
- general: H@400 173234 (a15_cot_apd7a6db629db02, stage 813f42db/c20h400) RUNNING since 16:26Z, expected end ~19:30Z; monitor tmux monR_173234 (cont_ops19/work/monR.sh, log cont_ops19/work/monR_173234.log). After: fetch with work/hd400/h400/o_fetch_h400.sh via ossh; pull package (no a/e) to work/hd400/h400ret/ like post_rem2.sh; score: cd work/hd400/hscore && /scratch/jjyeung/envs/p1cpu/bin/python -B score_h.py --return <unpacked ret or as score_h expects> --package <BUILD.json from Orchard 813f42db/c20h400/BUILD.json> --out ...; report per type and per set (reworded vs original) call rate + answer metric; corpus ingest (timeout 5400; the IO governor queue can take >30 min).
- advanced (ANSWER 1729Z; sealed argv general, moved by scontrol Partition=advanced + QOS=adv_4gpu_qos): 173241 D@400 (a15_cot_apda6f7936c1779) RUNNING since 17:37Z orchard-community-1, T 04:00 (partial expected; budget 19,595 s); 173242 E (a15_cot_apdd92e95963089, T 02:20) PENDING; 173243 D@200 (a15_cot_apd296bd1ef61cd, T 04:00) PENDING. Yield monitor tmux c20_monA2 (work/monA2.sh, log work/monA.log): on a launch GO/submitted file in events/cont_ops it USR1s running, scancels pending, posts one line. ORDER 1721Z item 2: launch never waits >5 min.
- D@400 remainder: kit on trinity-1-18 /scratch/jjyeung/orch_n30/cont_ops20_b/hd400/dresume (review GO, work/hd400/REVIEW_DREM400.md); Orchard sequence in work/hd400/REPORT_DREM400.md (stage 813f42db/c20d400r, T 04:00); kit files must be copied to Orchard (KIT dir) first. Remainder goes to general after H@400. Merge with dresume score_d.py --spec (two segments).
- Fetch scripts for E / D@200 / D@400: pattern work/o_fetch_rem2.sh (sed the package token). Scorers: D@400 trinity-1-18 hd400/dbuild/score_d.py (EXPORTS[400]); D@200 cont_ops18/dbuild/score_d.py; E cont_ops18/ebuild/score_e.py (REPORT_E.md line 45). Each read RESULT: sealed argv general, ran on advanced, node + card from the job log.
- Then: H@544 (a15_cot_apdc863c3e6b41d), H@200 (a15_cot_apdacd91c2f5c4b), own-arm (cont_ops19/work/ownarm); step-600 camera dose point (camera part of read A at 600: needs BIND600.json from r1_ops10 1704Z RESULT + a camera-only A build; may use a free advanced card under the yield rule).
- Done this session: routed A 400 (H3 STOP at 99.82%, RULING 1533Z: leg R1 ends at 400), score_r5_look.py (--step; GO), face_look.py (GO after fix), D@544 merged 580 (RESULT 1615Z; corpus seg0b/seg1b/seg2), H/D 400 builds (GO).
- Removal candidates: cont_ops20/REMOVAL_CANDIDATES.md. Orchard ledger: cont_ops20/work/ORCHARD_LEDGER.jsonl.
