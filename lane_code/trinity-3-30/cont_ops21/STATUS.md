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
