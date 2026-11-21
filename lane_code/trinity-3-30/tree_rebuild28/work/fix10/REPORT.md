STATUS: 16:42Z DONE. Diff 94d941e6 written and tested; Trinity PASS; held node: tree coverage_report PASSES with exact equality on all 3 call paths (apply :621, prepare verify :657, admit prepared :790); all 4 controls REFUSE; prepare phase completed; admit then stops at the known frame-audit refusal (fix6 third refusal, not this change). Not installed.
# fix10 REPORT: kit-side scene-census diff
## Design (16:12Z)
- Hook: kit b/sc.py main(), which runs the tree's r2_scene_bindings.rebuild at staging inside its bwrap. Right after rebuild, new kit module b/cn.py recounts every census source from raw rows of the admitted population with the tree's own counters (Exclusions.expect = independent Census.count, Exclusions.keep = filter, totals() reconciles both), and writes sc/a.json (census over the admitted population; same schema, withhold_file, benchmark_file as 0.json; exact_rebuilt_population true), sc/o.json (per source: whole-store census = admitted + outside, asserted; row keys of every listed row outside), sc/3.json (the tree's 2.json with scene_coverage.reference -> a.json). cfg['r2_scene_rebuild'] -> sc/3.json. pl.py publishes s0=3.json, s1=a.json, s4=o.json to live/.
- Admitted populations: pose sources = rows c1_pose_mix._row_selected(row, target, frame_prefix) selects (the mix's own predicate); routing base (census 'camera') = s1_routing._build census_rows(): COMPATIBLE type (s1_routing.compatibility, same pool_types, same contract epoch), train scene of the pointing receipt's division, not held out; pool = rows of the ELIGIBLE sources of the staged pool selection; pointing, vqa = whole store (their builds read every row; outside = 0).
- The tree's coverage_report (s1_exclusions.py:319) runs unchanged and still demands exact equality on all four groups; nothing is skipped.
- Unchanged: every tree byte (k/t_*.tar 5f2d77c4), s1_pool.implementation() (b/ is outside the closure), the pool selection and routing receipt (they do not read the census), mode r products, reviewed selection a49f117f/522a3be3, k/y.json, k/*.json pins. Changed: b/cn.py (new), b/sc.py, b/pl.py, SHA256SUMS.txt, BUILD.json kit_sha256/seal.
## Trinity test (a), trinity-1-18, 16:15Z (script s/t1.py, output rd/t1.out, W/w31cen/TEST_T1.json)
- No Trinity mirror of the pose stores, routing base or pool sources exists (fix9 rd/e2-e4), so (a) runs the kit tree's own functions on a synthetic 3,000-row store with the real dev list a1869ae2 and test list 3119aa4a.
- Build: W/w31cen/n_go = W/w30f1/n_go (seal 489f7f0f checked) + b/cn.py, b/sc.py, b/pl.py; support.reseal test seal 5a86c766... (NOT for install); launch_r1.build.verify(kit) == seal: True. Changed members: BUILD.json, SHA256SUMS.txt, b/cn.py 90b3ca6c, b/pl.py f8f42955, b/sc.py 43d4cc26. Tree tar unchanged.
- T1 view() keeps exactly what Exclusions.identifiers and Census.identities read: True on all rows.
- T2 whole (1,200/600) = admitted (800/400) + outside (400/200).
- T3 tree coverage_report, filter over the admitted rows, census over the admitted rows: PASS, observed = census = 800/400.
- T4 control, whole-store census: REFUSE "Filter differs from independent scene census: pose".
- T5 leak control, one dev-listed row moved into the admitted census but unseen by the filter: census 801/400, REFUSE (same message).
- T6 pool path of _count (per-source expect/keep) = plain count: 360/180 both.
## Held-node test (b), node of 174134 (orchard-community-3), srun --overlap, /tmp/a15_f10_174134, CPU only, nice 10 (s/o1.sh, s/o2.sh; driver node/h10.py e670836b; cn.py 90b3ca6c = the diff's bytes)
- Step 1, 16:12:51-16:19:39Z (408 s): cn.admitted on the job's own staged scene rebuild p/q/sc/2.json and config. Every source: whole-store census (tree 0.json) = admitted + outside, dev and test (rd/node_census.out):
  | source | admitted rows | dev / test admitted | outside dev / test | whole dev / test |
  |---|---|---|---|---|
  | pose_a2v3 | 27,604 of 66,934 | 3,777 / 4,880 | 1,841 / 159 | 5,618 / 5,039 |
  | pose_a3v2 | 203,520 (all) | 13,440 / 22,160 | 0 / 0 | 13,440 / 22,160 |
  | camera (routing base) | 35,423 of 47,898 | 3,985 / 0 | 783 / 0 | 4,768 / 0 |
  | pool | 92,217 of 103,758 (9 ELIGIBLE sources) | 8,424 / 5,617 | 1,122 / 566 | 9,546 / 6,183 |
  | pointing | 25,020 (all) | 3,640 / 2,944 | 0 / 0 | same |
  | vqa | 204,413 (all) | 0 / 0 | 0 / 0 | same |
- Admitted census per group = the filter counts the walk observed: pose 17,217 / 27,040; routing 12,409 / 5,617; pointing 3,640 / 2,944; vqa 0 / 0. The outside listed rows are 2,000 (pose) and 783 + 1,688 (routing), the same sets fix9 found by row keys.
- 16:21Z: ORCH note (verify path) handled: the driver now also calls carrier_c1_run.prepared on the prepared config (falls back to s1_exclusions.verify directly), logging every coverage_report call with its caller. In the design both paths read cfg['scene_coverage'], which the kit binds once at staging, so apply and verify compare against the same admitted census.
- Step 2 (prepare, started 16:26:34Z; rd/node_prepare1.out): the config differs from the job's only in r2_scene_rebuild (-> cen/3.json 8f3ac9ca) and scene_coverage (reference -> cen/a.json 30b45209); r2_scene_bindings.verify passes on it; the closure check passed; pointing, vqa and routing were reused, and the pose mix selection came from fix6's n2 (229,924 rows). WARNING at 16:29:33Z: the F1 vqa division pin path, admitted on content hash (the F1 kit fixes this separately).
- 16:32:04Z, apply path (carrier_c1_run.py:621 -> s1_exclusions.py:346 apply -> coverage_report with the kit census a.json): the tree's comparison is unchanged and PASSES with exact equality: pointing 3,640/2,944 = 3,640/2,944; pose 17,217/27,040 = 17,217/27,040; routing 12,409/5,617 = 12,409/5,617; vqa 0/0 = 0/0.
- Step plant (16:19:41-16:26:32Z): cn.admitted with one dev-listed outside row moved into the admitted population (pose_a2v3 row i=5; camera row i=3209): census pose_a2v3 3,778, camera 3,986; whole = admitted + outside still holds, so the move goes undetected by that identity. Only the exact comparison can catch it (controls below).
- Every call path into coverage_report used the kit census a.json, and each PASSED with exact equality on all four groups (the same numbers as above; rd/node_ev_prepare.jsonl):
  1. 16:32:04Z carrier_c1_run.py:621 prepare -> s1_exclusions.py:346 apply.
  2. 16:33:57Z carrier_c1_run.py:657 prepare -> s1_exclusions.py:375 verify.
  3. 16:36:58Z s1_admission.py:250 admit -> carrier_c1_run.py:790 prepared -> s1_exclusions.py:375 verify (the path in the ORCH note of 16:16Z).
- The prepare phase ran to its end with the real rows. Admit's next phase then refused at 16:37:50Z, in the frame audit: "Retained RGB is absent or outside its frame store" (s1_admission.py:261 -> :255 -> :99). This is the walk's known third refusal (fix6 REPORT, class (a), kit frame mapping), not this change. The driver's explicit prepared() call was therefore not reached, but the tree's own admit made the same call (path 3).
- Controls, run with the tree's coverage_report on the real filter rule that prepare built (call 1's arguments):
  - whole-store census (the tree's 0.json, as 174134 ran it): REFUSE "Filter differs from independent scene census: pose";
  - admitted census for pose with the whole-store census for routing: REFUSE "...: routing";
  - leak, pose (dev-listed a2v3 row i=5 moved into the admitted census, unseen by the filter): REFUSE "...: pose";
  - leak, routing (dev-listed base row i=3209 moved likewise): REFUSE "...: routing".
- Node outputs copied (small files): nodeout/cen/a.json 30b45209 (exact_rebuilt_population true, population admitted), o.json 069ccde5, 3.json 8f3ac9ca, lk/a.json, ev_*.jsonl. Nothing was written outside /tmp/a15_f10_174134; X/n, X/o/174134 and fix6's folder were read only. Orchard calls: 16:12:50, 16:15:20, 16:20:59, 16:23:2x, 16:28:32, 16:33:05, 16:38:02, 16:40:1x (each at least 2 min apart; the 16:15:20 call came 2 min 14 s after the first one ended).
## Files (work/fix10/)
DIFF.patch (94d941e6135336c7dfac1e3bc0cebe88dc937287837687a73e151618f0716166), QUESTION_DRAFT.md, REPORT.md, k1/n_go (local patched copy), node/h10.py, s/*.sh, s/t1.py, rd/*, nodeout/*. Trinity build: trinity-1-18:/scratch/jjyeung/orch_n30/tree_rebuild10_w/w31cen/n_go (test seal 5a86c766, not for install), TEST_T1.json. Design record: /data2/jjyeung/agent_project_data/distill_design/N_KIT_ADMITTED_CENSUS_20261121.md (+ INDEX line).
