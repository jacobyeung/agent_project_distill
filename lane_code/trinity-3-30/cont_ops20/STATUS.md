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
