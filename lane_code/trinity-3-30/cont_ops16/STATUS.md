# cont_ops16 STATUS (trinity-3-30; started 20:53Z 11-18; rotate by 02:20Z 11-19)
Workspace: /scratch/jjyeung/orch_n30/cont_ops16/work/c15 = /scratch/jjyeung/orch_n30/cont_ops/work (symlink chain cont_ops -> cont_ops16/croot, croot/work -> ../work/c15, created so sealed paths resolve). Also created /scratch/jjyeung/orch_n30/evalx27/work/pull/x27/res/e193/{SPEC,PLAN}.json + merged/main/results/budget_2048/{request.json, 0/items_leg_m544_main.jsonl} (from Orchard /home/jjyeung/okit/evalx_results/e193c2a3c/result.tar.gz members; shas = pooled-rule manifest / count_diag pins).
## Recovered
- h1read = fix-6 kit rebuilt: fork tar trinity-1-18 n30_mirror/cont_ops/h1vsti_v1_1045Z.tar (3c433159) + lane-code h1read files; SHA256SUMS all OK except 4 doc files. h1vsti = that fork (SUMS dff33822, FINAL_PINS 272da0e4). Partial lane-code copies kept as h1read_partial, h1vsti_partial.
- Baselines restored and sha-verified: d0/readk/evidence/A544.jsonl+ACCEPTED.json (from fork readk), adff67f7ae9 result.tar.gz (334e1368) + x/ITEMS.jsonl (a05c2318) + full x, a5d2d909067 (m100) result + x (old partial x -> x_partial), VSTI 544 acb2faedd41 fetched/x (b13ec8f1; summary pooled 46.11).
- Rebuilt tools (tested on m100, equal to cont_ops15/count_diag): cfix/derived_v3.py, split/relsize.py, h1read/post200.sh (TOK=<tok> STEP=200), h1read/mon16.sh (1-min liveness/output/yield).
- Lost: s1_receipt of 673bc60f (4c0dd9d6); routed packages' 0.tgz payloads + reader_r1 T1/T2 inputs (r1route/out/b1,b2 hold only small files).
## Now
1. m200 DECISION read: token a8102c3207b (rebuilt bit-identical: BATCH cb40b5c7, CONFIG ed30d4f4, plan 9fc9d1f6) = Orchard 172646 on general, RUNNING since 21:00:33Z; tmux c16_mon200 (log h1read/mon16_a8102c3207b.log). On LEFT_QUEUE: `TOK=a8102c3207b STEP=200 bash h1read/post200.sh` then ONE verdict RESULT (+copy to events/r1_ops).
2. Then VSTI r6 m200: `TOK=a35f73e87f0 bash h1vsti/subv.sh` (refuses if any general job of ours), monitor, fetch+unpack per FIXV1.md, `vsti_summary.py --read <200 x> --base kit/build/acb2faedd41/fetched/x`; gate vs 46.11.
3. Facing families: fix-6 refuses away/forward for R1. Fork h1face (hardlinked assets/readk/evidence dirs, made read-only in h1read) under Codex Astra build F1 (tmux c16_codex_f1, brief h1face/FIX_BRIEF_F1.md, log codex_f1b.log, deliverable FIXF1.md); then ask ORCH for review in a RESULT; baseline = e193 (job 169526) merged/away+forward B2048 (Orchard okit/evalx_results/e193c2a3c).
4. Routed read: needs s1_receipt regenerated (CPU preparation of config fac07052; s1_admission.py checks cross-attempt determinism) and packages d72cdcff1e22a/b9188e9225a85 payloads rebuilt. Not urgent (ORCH 2105Z).
## Notes
- Lane folder 4.8 GB (cap 4): two kit copies (h1read 2.4G, h1vsti 2.2G, assets duplicated). Removal candidates in REMOVAL_CANDIDATES.md.
- Ledger: work/ORCHARD_LEDGER.jsonl (c15 copy + my lines).
