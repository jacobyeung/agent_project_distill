# cont_ops19 STATUS (trinity-3-30; started 09:09Z 11-19; rotate by ~14:30Z)
Base state: /scratch/jjyeung/orch_n30/cont_ops18/STATUS.md (09:10Z section). Brief: orch_n30/briefs/cont_ops19_d.md.
## 09:15Z
- chain400 (tmux) alive, polling for m400 .done every 3 min (log cont_ops/work/h1read7/autosub400_a59a7bff4c4.log); not landed at 09:07Z.
- Plan when .done lands: direct auto-submits; I fill BIND400.json and build routed A/B (CPU, Orchard) while direct runs; post400.sh when direct ends.
- 09:26Z m400 ETA ~09:40-10:00Z per r1_ops8 STATUS (receipt may wait for checkpoint ~09:56Z). gov_fetch.py ready in work/ for a >=20 MB return (step-200 return was 11 MB).
## 09:45Z
- m400 export landed 09:31Z (RESULT r1_ops 0933Z; config 9459724f OK). Direct 173038 (a59a7bff4c4) submitted 09:34Z, PENDING Resources; tmux mon400_a59a7bff4c4.
- Routed 400: cont_ops17/work/BIND400.json filled; gen400b -> g400/; o_build10 on Orchard stage 813f42db/r10: A pkg a15_cot_apc9399fd2d1158, B pkg a15_cot_apcb2b4d58630bc (build10.out). o_place_pull_fill10 started (Orchard nohup pid 1390699, log 813f42db/r10/fill.log): pulls 4 parts, fills A then B, dry checks + 3.py check. GPU A/B wait until the facing+VSTI chain ends.
## 09:52Z
- Direct 173038 RUNNING on community-2 since 09:36Z (expect ~10:35Z end).
- Routed A, B filled + dry pass (fill.log 09:44Z, 09:47Z). CPU checks submitted on preempt: A 173039 (a15_cot_apc9399fd2d1158), B 173040 (a15_cot_apcb2b4d58630bc); scripts cont_ops19/work/o_cpu_A10.sh, o_cpu_B10.sh. 173041 = trap test of B's BATCH (copied tail of o_cpu_B5.sh), wrote only B/a/x173041.
- GPU submit: adapt cont_ops17/work/o_sub_A4.sh / o_sub_B5.sh with new P (and r10 fill.log) after the facing + VSTI jobs leave general.
## 10:00Z
- CPU checks PASS: A 173039, B 173040 (CPU.json passed, guard, entry sequence; B full_reader). GPU scripts ready: cont_ops19/work/o_sub_A10.sh (T 05:00), o_sub_B10.sh (T 02:30).
- ORCH ORDER 0949Z: general order = direct -> facing -> VSTI -> vehicle N proof (tree_rebuild12) -> routed A, B (only after tree_rebuild12 posts in events/cont_ops that the proof runs elsewhere or released the slot) -> D@200 -> D@544 rem -> E -> H@544, H@200 -> own-arm. Direct verdict RESULT right after post400 (corpus ingest first).
## 10:15Z
- DIRECT 400 DONE: RESULT events/cont_ops/*_RESULT_r1_m400_direct_decision_SILENT_repair_PASS.md (SILENT; runaways 0/150, 0/287; counting pooled +11.25 [+5.52,+16.31]; relsize -4.00). Corpus read 6ed2c7aa_s400_devS1R0_direct_a59a7bff4c4. Files events/cont_ops/files_m400/.
- Facing 173044 (afdfd5caac6) submitted 10:06Z by chain400; then VSTI a4525db2f6a.
- Before routed GPU submit: Orchard pool ae71c903 was 78.4 MB (>75 MB check in o_sub_*10.sh); move fetched step-200 routed returns (b635a315de01e0002a33a, d60a20ec012960002a2c8) to ae71c903_fetched like o_mvpool112.sh.
## 10:30Z
- ORCH RULING 1018Z: direct accepted; owed facing + VSTI rereads, then (after vehicle N proof) routed with H3 + call rates (dist_gate.py, sb_callrate_v3). Step 600: print relative size again on the same items; print counting split by true count (2,3,4,5+) on both sets.
- FACING 400 DONE: RESULT *_RESULT_facing_gate_m400_PASS_toward_holds_not.md (gate PASS +68.0; toward -3.33 not holding; toward-hard -10.0 H1 wholly below zero, mark). Corpus 6ed2c7aa_s400_facing_direct_afdfd5caac6. Files files_m400/FACE_m400.*.
- VSTI 173046 (a4525db2f6a) running since ~10:20Z.
