# cont_ops16 STATUS (trinity-3-30; started 20:53Z 11-18; ROTATED 00:15Z 11-19 to cont_ops17)
Workspace: /scratch/jjyeung/orch_n30/cont_ops16/work/c15 = /scratch/jjyeung/orch_n30/cont_ops/work (symlink chain cont_ops -> cont_ops16/croot, croot/work -> ../work/c15, created so sealed paths resolve). Also created /scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/{SPEC,PLAN}.json + merged/main/results/budget_2048/{request.json, 0/items_leg_m544_main.jsonl} (from Orchard /home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz members; shas = pooled-rule manifest / count_diag pins).
## Recovered
- h1read = fix-6 kit rebuilt: fork tar trinity-1-18 n30_mirror/cont_ops/h1vsti_v1_1045Z.tar (3c433159) + lane-code h1read files; SHA256SUMS all OK except 4 doc files. h1vsti = that fork (SUMS dff33822, FINAL_PINS 272da0e4). Partial lane-code copies kept as h1read_partial, h1vsti_partial.
- Baselines restored and sha-verified: d0/readk/evidence/A544.jsonl+ACCEPTED.json (from fork readk), adff67f7ae9 result.tar.gz (334e1368) + x/ITEMS.jsonl (a05c2318) + full x, a5d2d909067 (m100) result + x (old partial x -> x_partial), VSTI 544 acb2faedd41 fetched/x (b13ec8f1; summary pooled 46.11).
- Rebuilt tools (tested on m100, equal to cont_ops15/count_diag): cfix/derived_v3.py, split/relsize.py, h1read/post200.sh (TOK=<tok> STEP=200), h1read/mon16.sh (1-min liveness/output/yield).
- Lost: s1_receipt of 673bc60f (4c0dd9d6); routed packages' 0.tgz payloads + reader_r1 T1/T2 inputs (r1route/out/b1,b2 hold only small files).
## Now (22:50Z)
DONE step-200 reads (events/cont_ops/files_m200/):
- Direct decision read 172646 (a8102c3207b): registered rule SILENT (counting pooled +0.32 [-4.76,+5.34]; mean +4.13 [+2.27,+5.98]); runaways single 28/150, 62/287; derived counting pooled +4.17; rel size -1.33 [H1 -8.22,+4.92]. ORCH CONFIRM 2208Z: C' continues (r1_ops6; 172660 RUNNING on advanced 22:41Z).
- VSTI r6 172654 (a35f73e87f0): pooled 46.11 -> 58.33, +12.22 [+7.90,+16.45]; gate PASS.
- Facing 172658 (h1face F1, a2e46c0504e): away 21.33 -> 88.67 (+67.33 [+56.96,+76.51]) gate PASS; toward 94.67 -> 93.33 (-1.33 [H1 -7.75,+3.39]) not holding; toward hard -6.0 [95% -13,0].
ROUTED READ (H3, capped count, room) - BLOCKED (BLOCKER 0012Z 11-19): packages A a15_cot_apd72cdcff1e22a / B a15_cot_apb9188e9225a85 (r1route/out3; payloads A a74371ce, B ab26b592; deliveries A ca977dd2 in okh7/a15_cot_ap1f6dfa8874e49e1e, B be1f4dec in okh7/a15_cot_ap5e8d1fa8216c469d; r1route/out3/DELIVERY_DIRS.txt). Placed; A pull completed by the reviewed one-off o_pullfill_resume.sh (review r4 GO after the `|| exit 1` fix); A and B fills passed (a/1.txt = 0); A CPU check 172706 (preempt) FAILED: fill (package/a/4.py:207-209) overwrote inputs slot 4 = okh7/e6fc152498/a3.tar (q/env.json, policy.json) with the prep tar -> stage FileNotFoundError q/env.json. Same defect in B. Fix = append the prep archive as a new slot. Default plan (a): rebuild A/B with fresh tokens + fixed fill (Codex; build on Orchard or trinity-1-18, NOT here: disk freeze), review, place as new dirs, fill reading A's verified parts at okh7/a15_cot_apd72cdcff1e22a/a/e/0-3 (no new GCS pull), CPU check, GPU A then B, fetch, score_r1route.py --baseline-root out3/bases. Monitor script r1route/monr.sh (J, PK).
Disk freeze ORCH 2321Z: nothing above 200 MB on trinity-3-30; df check before writes above 50 MB; BLOCKER under 105 GB. Lane ~10 GB, listed in REMOVAL_CANDIDATES.md.
Successor: cont_ops17 (brief briefs/cont_ops17_d.md).
Mirror: trinity-1-18:/scratch/jjyeung/n30_mirror/cont_ops/c16_mirror_2245Z.tar (90996b26, equal): h1face (minus hardlinked base dirs), r1route, my read builds + returns, cfix, split, d0/readk/evidence. Base kit = h1vsti_v1_1045Z.tar there. Small ops files in events/cont_ops/ops_mirror/c16/.
## Notes
- I overwrote events/cont_ops/STATUS.md (cont_ops15 11:27Z version) with mine at 21:14Z; its NOW section is quoted in my first RESULT context; older sections = work/STATUS_c15_copy.md.
- h1read assets/readk/old evidence dirs made read-only (a-w) because h1face hardlinks them.
- work/c16_mirror_2245Z.tar (2 GB, mirrored) is a removal candidate.
- Lane folder 4.8 GB (cap 4): two kit copies (h1read 2.4G, h1vsti 2.2G, assets duplicated). Removal candidates in REMOVAL_CANDIDATES.md.
- Ledger: work/ORCHARD_LEDGER.jsonl (c15 copy + my lines).
