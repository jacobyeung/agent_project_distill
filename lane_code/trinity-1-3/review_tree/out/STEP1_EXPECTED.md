# Step 1: what the tree must contain beyond base b01ce449 (written before opening builder reports)
Sources: NEXT_LEG_REBUILD_PLAN §1,2,4; TRACE_RULING 2.1-2.8; rs_tree BRIEF3-6B; tree_review 1-3 results; ORCH notes in events/tree_rebuild.

| # | Requirement / earlier finding | Code that would close it |
|---|---|---|
| R1 | Init bound to step-544 export artifact 1d6eeb28...; changed mix/code refuses exact resume | config field pinning artifact sha; prepare() compares sha; resume compares mix+code identity |
| R2 | Direct contract: shared grammar 49e814eb (15 rules), no call tag / <tool_response> in direct target, numbers only from allowed set, non-empty think | wrapper calling trace_grammar.validate_trace on every direct row at intake AND at trainer read |
| R3 | Program rows only via masked event path (carrier_c1_routing:467-468); allowlist = absolute distance + 3 camera types (room size direct, route planning direct) | route table constant; intake refuses program row whose type not in allowlist; direct row of program-only type? |
| R4 | Review1 #1 frame hashing via STUDENT_FRAME_ROOT_MAP, not raw logical paths | admission resolves through root map; test with unmapped root refuses |
| R5 | Review1 #2 / P3: materializer rows -> VQA/routing stores, membership manifest, geometry_dense | materializer module + production caller |
| R6 | Review1 #3: kit stages from empty; four-stream kit first-class (cont_ops: launch_s1/build.py always injects MDG) | kit builder w/o MDG; stage from empty test |
| R7 | Review1 #4 / mix: no empty cell, <=~4 repeats after filtering, repeat check from metadata BEFORE materialization (rev3 F1) | metadata gate; plan §4 table; pose 64 needs both pose sources else pose 60/pointing 36 |
| R8 | One connector, one dense-frame rule (rev1 #5,#6) | |
| R9 | Grammar holes: 120cm, number words, bare "Relate: The answer is A.", Step filler, "half a meter", "a dozen", "So the answer is A.", "Option A is correct." | wrapper/shared validator refusals |
| R10 | N1 dense clips keyed by content (hash+ordinal), per-row clock, same hash in two stores = one frame | |
| R11 | N2 pose frame_prefix; N3 route-planning id collisions: select by type, unfiltered build refuses | |
| R12 | N4 bounded frame-hash memo | |
| R13 | N5 selector role binds fitted selector; box policy role; evidence as hashed records; refuse deployed selector for ReVSI/VSTI use and for rendering training responses | |
| R14 | N6 exclusion accounting with upstream receipts; scene_coverage=None refuses; 1,172 lineage-less room rows excluded in tree | |
| R15 | P5 component policy: frozen external exempt+disclosed; init `overlap_outside_claim_scope`, claim scope VSI/VSTI/ReVSI (+without ARKit venue 381879); refuse STI-Bench/ReSTI/MindCube eval/export of lineage; eval-time program choices gated until freeze file except VSTI camera routing | |
| R16 | Withheld 80 rooms = rows_rebuild WITHHELD_ROOMS_80.json sha 634820b4 only; excluded from EVERY stream (VQA, routing pool, camera, pose, pointing) with the 3 sealed bindings (s1_exclusions totals 232-241, s1_routing 419-421, s1_exclusions 281-284) consistent; test a withheld-room row reaches no store | |
| R17 | Rev3 F2 frame-host per-file limit ~6 GiB; F6 time + no-progress limits | |
| R18 | Rev3 F3: records in kit under opaque names compared by sha256; no node path, no forbidden word in job-visible path/arg/env; site = Orchard (cluster of job 169097) | |
| R19 | Rev3 F4: eval scope gate keyed on bank actually read (item ids + reader hash), not caller label; venue 381879 read allowed with both scores | bank gateway on every evaluation entrypoint |
| R20 | P6: two configs (A0 no connector, A2 GF-1) from one source selected by one bound field; both stage from empty, step-zero parity | |
| R21 | Disk guard: no full store on local node; 200 MB temp cap | |
| R22 | ORCH 1915Z: config-bound switch keeping routing-opener embedding rows on same-lineage warm start (base resets at carrier_c1_run.py:781-783); test rows equal export after load | |
| R23 | Units rows as ground-form event rows; recovery rows: failures only in routed types at real call, simulated miss, end in direct answer with Locate, no operator-fault strings, no call after failed ground except one retry | |
| R24 | Facing pairs: both twins or neither | |
| R25 | Contract patches (rs_contracts R2) - known absent | |
| R26 | Run identity records GT-response fallback (no deployed cache), claim scope, open question date | |
