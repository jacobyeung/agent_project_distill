Host-side routing package delivered; production remains blocked. Four of six slices pass native intake with only sealed exclusion refusals. Recovery and camera require owner changes.

Tree seal: `57a1f14df5ab60e5783a4baa76e714476770d2bd29f5d98c514a14be6412c6f7`. `TREE_IMPORTS.json` records and rechecks every tree dependency captured by the executed stages. No tree file was edited.

| Slice | Final rows | Native admitted | Native refused | Result |
|---|---:|---:|---:|---|
| recovery | 973 | 760 | 213 | BLOCKED |
| absolute_distance | 8,315 | 7,805 | 510 | PASS with exclusions |
| units | 8,315 | 7,805 | 510 | PASS with exclusions |
| coverage_distance | 1,500 | 1,500 | 0 | PASS with exclusions |
| coverage_units | 4,500 | 4,500 | 0 | PASS with exclusions |
| camera_wording | 5,979 | 1,722 | 4,257 | BLOCKED |
| camera_B | 5,829 | 1,707 | 4,122 | BLOCKED |

The six primary slices contain 29,582 rows; all were covered by disjoint shards of at most 2,000 rows. Full envelopes were also called with `limit=2000`. Camera B is an alternative, not an extra training family.
Native refusal reasons: recovery—61 `excluded:eval_rooms`, 152 `R2 fallback calls again after a failed response`; absolute_distance—510 `excluded:eval_rooms`; units—510 `excluded:eval_rooms`; both coverage slices—none.
Camera A refuses 280 `excluded:eval_rooms`, 1,993 `Shared grammar: unit_quantity`, and 1,984 `Shared grammar: number_not_allowed,unit_quantity`. Camera B refuses 248, 1,936, and 1,938 respectively.
Upstream receipts run the actual seven-pin Exclusions.check, withheld-room check, merged-dev check, and native removal predicates over every final row. Their counts describe exclusion eligibility before grammar checks; native first-failure counts differ. No prefiltered flag skips a check.

Radiator: the change affects 112/806/818/149/476 rows in recovery/absolute_distance/units/coverage_distance/coverage_units; camera changes zero. Every changed row fails the sealed extent-content comparison. Production keeps the original call text. Variant R changes only the obj phrase in ground-call strings; it is diagnostic and needs repacked spans and new independent extent/raw membership/source/coverage pins before use.
The independent extent-audit owner and tree_rebuild must regenerate the affected extent entries and config pin, plus V2H source constants/derivations and downstream bindings. No extent receipt was invented and no radiator REMOVE list is active.
Camera A removes the 21 unproven d2/vfc2c241f2978 rows. Camera B also removes 150 citing rows: 150 differing frame-reference occurrences across 7 unique keys and 7 kr9c/k6tk hash pairs. CAMERA_KR9C_DIFF.json lists every key, both pins, and citing QIDs. No PNG bytes were read or substituted.
K1: 21 recovery and 262 units rows were physically removed with existing native removal matches. The other final slices have zero K1 matches.

All 37 checker runs pass, with zero R0 bdb5d402, dev-S1 969cdb56, BENCH v2 3119aa4a, withheld-80 634820b4, and placeholder-object remove hits. The only K1 hits are 21/262 in diagnostic recovery/units variant R; every hit matches an existing removal list. Unselected intermediate row files were audited too.

Recovery blocker: student_pilot/r2_contract.py:248 refuses the second distinct operand probe after the first reports failure in 152 sealed rows. The recovery contract owner must reconcile that guard with the authenticated event sequence; this lane did not weaken it.
Camera blocker: student_pilot/r2_grammar.py:183 invokes pinned trace_grammar.py, whose rules at :502/:509 reject unsupported signed arithmetic values and the +180-degree convention in canonical camera prose. The tree/camera owner must reconcile rendering/adaptation with a41ba191 or regenerate authenticated rows and bindings. BLOCKER_DIAGNOSTICS.json records exact examples.
Composition: the supplied deferred N config raises KeyError recovery at r1_routing.py:171. The concrete six-family first-boundary candidate refuses R1_CAMERA_SOURCE_PIN at r1_coverage.py:190. This w24 tree already includes camera_wording in source_names; its EXTRA_PINS still binds the old 6,000-row file and must be updated/resealed for the selected source.
Composition therefore stops before the host veto. A separate unmodified intake(limit=None) call refuses `Local slices must contain at most 2000 rows per family` at r2_intake.py:42 on trinity-1-18. No hostname, environment, or function was spoofed.

Pin paths: portable envelopes carry u/<sha256>. Dry shard intake resolves them through the existing r1_persisted.scope map; withheld_rooms reads u/<sha256> relative to the workspace. out/localized envelopes instead carry absolute active pins and were checked without a scope. ENVELOPE_INDEX.json, STAGED_INPUTS_FINAL.json, and LOCALIZED_INDEX.json enumerate both forms.
Production must stage identical bytes under its root/u/<sha256> and run work/localize.py --tree <production-tree>; then bind the resulting envelope hashes and exact equal rows/extent pins. Its coverage and upstream exclusion paths are regenerated together. Inline kit localization alone does not rewrite nested envelope files.
CONFIG_HANDOFF.json supplies routing_inputs in config and request, row_slice_inputs, row_sources, source_membership, extent_receipt, and both routing-base fields. Exit deferred_first_boundary by omitting routing_slices at the first boundary. Preserve the fixed removal order.
Q_E4 must map /data2/k6tk and /data2/kr9c to verified absolute node-local roots. Those destinations and N raster/staging receipts are MISSING. Set Q_E7=1 only after the separate alias patch and reseal; preserve the local-node and non-Trinity vetoes. The named map/plan/FPS hashes were verified; raster/store readiness is not claimed.
The registered phrase document was read once; its file-byte SHA256 is MISSING because the initial bounded read did not capture it. The same rewrite policy is explicit in the task prompt. Its exact path is recorded in ROUTE_MANIFEST.json.

Commands for all numbers (run from this workspace): prefix each Python command with `nice -n 10 env OMP_NUM_THREADS=8 MKL_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8 PYTHONDONTWRITEBYTECODE=1 /scratch/jjyeung/envs/p1cpu/bin/python -B`.
`work/route.py 1` produces radiator counts/pin checks; `2` produces camera counts/diffs; `3` produces final row/removal/accounting counts; `4` binds envelopes.
`work/intake.py` produces all native counts and composition refusals; `work/localize.py` checks absolute pins; `work/diagnose.py` attributes refusal types/examples; `work/audit.py` produces all checker and placeholder counts.
`work/finalize.py` computes the reference-occurrence total, verifies the recorded tree hashes, and writes this manifest/report. `work/package.py` computes package bytes and SHA256 and verifies archive members.

Delivery: ROUTE_MANIFEST.json, fbp_route.tar, fbp_route.tar.sha256, and PACKAGE.json. The tar contains code, envelopes, coverage, receipts, audits, and reports. Row files exceed the 300 MB inclusion cap and are excluded; their exact paths/hashes remain in the manifest. The 1.7 GB store was not copied.
