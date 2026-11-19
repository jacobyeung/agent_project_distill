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
## 10:50Z
- VSTI 400 DONE: RESULT *_1034Z_RESULT_vsti_gate_m400_PASS.md (pooled +15.33). Corpus read file published by hand after my timeout killed add_read's verify wait (sha checked); index/orphans/INDEX publish in tmux c19pub (log work/pub_vsti400.log) - check it ended.
- Step-400 chain finished; general holds no job of mine. Waiting for tree_rebuild12's post in events/cont_ops (vehicle N proof elsewhere or released slot) before routed A/B (ORDER 0949Z).
- Pool ae71c903: moved a4525db2f6a, afdfd5caac6, d00c03dcc685e0002a39d to ae71c903_fetched; pool now 66.4 MB (<75 MB submit check).
- ORCH RULING 1041Z item 4: print relative count (dev-S1, 139 items, with count of numeric answers to letter questions) at step 600 and at every vehicle-N read.
## 10:55Z
- ORCH ANSWER 1047Z: fill general shortest first with graceful yield to the proof: routed B (submitted 173052, tmux monR_173052, monitor work/monR.sh, log work/monR_173052.log), then D@544 remainder. Routed A waits for the proof unless tree_rebuild12 posts it runs on preempt. Report B room (MRA, split dev-S1/R0-dev, call rate) as soon as scored.
- Corpus VSTI: c19pub publishes index/orphans (governor waiting); NOT rerunning add_read.sh (read file exists -> its pub step would fail FileExistsError and skip the index).
## 11:25Z
- ROUTED B 400 DONE: RESULT *_RESULT_r1_m400_routed_B_room.md (MRA 66.42, +59.85; R0-dev 67.04, dev-S1 64.72; 0/134 calls). Workspace r1route/out3/B10 (package, src, ret), scoring r1route/out4s (score_r5_400.py, room134_400.py, A/src temporarily -> out3/A4/src for imports; replace with A10's src when A lands). Corpus 6ed2c7aa_s400_room134_routed_B10 publishing (add_B400.log).
- D@544 remainder 173053 submitted 11:17Z on general; tmux monR_173053 (log work/monR_173053.log). After: fetch (dresume RESUME_D.md / o_fetch), merge-score dresume/score_d.py --spec, corpus.
- Corpus VSTI index published (pub_vsti400.log done).
## 11:35Z
- ORCH ORDER 1125Z: proof runs on preempt (173050/173051); D@544 remainder 173053 stopped gracefully (USR1 11:30Z, COMPLETED 0:0 after 11.6 min, partial: fetch + make a second remainder later). Routed A 173054 RUNNING on general since 11:33Z (tmux monR_173054).
- After A: D@544 remainder (partial of 173053 + rest), D@200, E, H@544, H@200, own-arm. A's RESULT: H3 per camera type + call counts; distance call rate by unit and wording group (dist_gate.py sets a, c; sb_callrate_v3); capped; distance MRA split calling/non-calling; vs 544 and 200.
- Corpus B published (add_B400.log rc=0).
## 11:36Z
- D@544 remainder 173053 partial: 3 of 102 done (return d09f959256d870002a3fd f5033bbf, fetched to Orchard pkg a/f; pool entry moved; local copy cont_ops19/work/drem1/pkg.tar excl a/e).
- Second remainder BUILT: a15_cot_apd5b7ea08426cd (99 items = 580 - 478 (172957) - 3 (173053); items REM544_2.json 37180266 via cont_ops19/work/drem2/make_rem2.py; code upload 813f42db/r544ccode (dresume with fixed build_d.py); stage 813f42db/r544c; DIFF vs r544b only token/count/hash lines). place_fill running on Orchard (nohup, log r544c/pf.log, REUSE_PARTS_FROM d09f959256d87/a/e). Next: CPU check (P=... T=01:30:00 bash r544c/o_cpu_D.sh), then GPU after A.
- Merge score later: dresume/score_d.py --spec with three segments (d544ret, 173053 partial, rem2 return).
- Routed A 173054 running (monR_173054).
## 11:45Z
- Rem2 a15_cot_apd5b7ea08426cd filled + dry pass (r544c/pf.log); CPU check 173055 on preempt (submitted 11:44Z). GPU submit after A: P=/project/community/jjyeung/okh7/a15_cot_apd5b7ea08426cd T=01:30:00 bash /project/community/jjyeung/okh7/813f42db/r544c/o_sub_D.sh, then monR (J, P, LB=D544rem2).
