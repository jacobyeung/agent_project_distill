E='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/tree_rebuild/'
p=E+'N_REVIEW_INPUTS.md'; L=open(p).read().split('\n')
L[0]='# Inputs for n_review1c (tree_rebuild18, 2026-11-20T03:00Z; W = trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w; read-only)'
new={
'2.':"2. Launch kit 24m4e = 24m4f (W/w24e/out/tree_rebuild_b24m4f_26fb868d.tar 3cc9b8e7; reports W/w24e/out/BUILD24M4E_REPORT.md, BUILD24M4F_REPORT.md): kit q 510d248b and kit n 240f8c17 (GO=false) in W/w24e/work/build24/kits/{q,n}; GO variant W/w24e/out/kit_n_go c992c930 (not uploaded); kit qd e7f32394 (W/w24e/out/kit_qd). On Orchard x_22c714e1/{q,n,qd} since 02:33Z. Census: tree's existing room functions on the native admitted selections, q/n refuse R1_CENSUS_PROTECTED_ADMITTED:<stream>; census receipt in live/c0..c4.json, pinned by h.py/rv.py. Configs are base64-json (k/c.json pre-preparation config). Arming: W/w24e/out/arm_routing.py 4023ffd6, usage W/w24e/out/ARM_ROUTING_USAGE.md (takes your task-A RESULT: selection sha256, regenerated_sha256, the word PASS).",
'6.':"6. Routing selection: discovery job 173567 (advanced; 173568 preempt is the spare, cancelled past staging), kit qd e7f32394 (24m4e), writes x_22c714e1/o/173567/routing_selection.json, receipt.json, materialization.json, db_bytes.json (+dbb.log; regenerated DB copied to x_22c714e1/u/<sha>), live/ census c0..c4.json + protected row keys. You check it against ca0616db/4e8e6c04 (47,898 rows, 4 program types; ORCH 2336Z cases a/b/c); the lane binds u/<its sha256> only after your PASS.",
'7.':"7. Reviews: Cursor tree reviews (copies events/tree_rebuild/cursor_verdicts/); tree C GO tr17_rev24l4c. Astra kit reviews: codex_runs/20261120T012257Z_tree_rebuild_rev24mC (24m4c), 20261120T020130Z_tree_rebuild_rev24m4d (24m4d), 20261120T024308Z_tree_rebuild_rev24m4f (24m4f GO, no verified problems) under /home/jjyeung/agent_project_distill/agent/scratch/codex_runs/ (final_message.md).",
'8.':"8. Rehearsal: 24k6 capacity decision W/w24/work/build24k/rehearsal_k6/CAPACITY_DECISION.md; loop rehearsals 24f run4/run5 (W/w24/work/build24f); hash table W/work/hash24h1/. Per-file grounds (ORCH 0239Z): Codex cov24c1 output W/work/cov24c1/COVERAGE.md/.json; copier shutdown test Codex cps24t1 output W/work/cps24t1/REPORT.md, RESULT.json.",
'9.':"9. Build reports: W/w24e/out/BUILD24M4{C,D,E,F}_REPORT.md; card rows W/w24e/out/N_CARD_KIT_ROWS_24M4E.md; card events/tree_rebuild/N_LAUNCH_CARD.md.",
}
for i,l in enumerate(L):
    for k,v in new.items():
        if l.startswith(k+' '): L[i]=v
open(p,'w').write('\n'.join(L))
p=E+'N_OPERATOR_POINTERS.md'; L=open(p).read().split('\n')
L[0]='# N operator pointers (tree_rebuild18, 2026-11-20T03:00Z; launch kit 24m4e/24m4f on tree C 0c7614c8: kit n 240f8c17 (GO=false) and qd e7f32394 on Orchard x_22c714e1 since 02:33Z; GO variant c992c930 not uploaded; armed seals follow arm_routing after n_review1c task A; discovery 173567 on advanced. Census refusals before the wait: R1_CENSUS_PROTECTED_ADMITTED:<stream>; census files live/c0..c4.json)'
open(p,'w').write('\n'.join(L))
