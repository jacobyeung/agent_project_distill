Selection semantics are unchanged by the seven H1 closure changes; production equality is still BLOCKED by 13 missing local gzip files (95,354,406 bytes).
Entry: build/tree/student_pilot/s1_pool.py:268 -> prepare:125; implementation:93 uses the static local import closure in p3_provenance.py:58, including nested imports.
Policy: tools/selection_check.py:58 exactly reproduces D0's direct-to-VQA projection (92,607 -> 83,184); raw and projected content must both match.
Changed functions: carrier_c1.py:506; carrier_c1_routing.py:442,477; carrier_c1_run.py:448,645,659; h1.py:18; h1_faithful.py:83,197; h1_r0.py:105; materialize.py:494 (all under build/tree).
None executes in pool selection; reserve filtering can change downstream training membership. Full hashes and definition diffs: evidence/fix7_selection/changes.json.
Tool: tools/selection_check.py:112 invokes native prepare and compares every content field plus ordered index bytes; only implementation is excepted, never relabeled.
Inputs: all pins/paths/sizes in evidence/fix7_selection/INPUTS.md; Orchard x_07ca49df k/ and u/eb3429c5 per catalog; 25 pin occurrences have local bytes, 13 gzip files do not.
Login package: build/q.sh, 114179 bytes; private opaque names, self-checking payload/archive, bwrap logical roots, offline network namespace, nice 19, CPU PY_GATE.
Local tool: exit 2 / BLOCKED; no production replacement emitted. Native synthetic equality and changed-content refusal PASS.
| Audit past 215 | Result | Limit |
|---|---|---|
| Test-only copied selection, native build through 219 | REFUSED missing r16 receipt | Relocation/model descriptor supplied only for this isolated audit |
| Native synthetic s1_routing.build through 456 | PASS, 2 rows | Empty legacy DB, character processor, no RGB byte reads |
| Scene blocker/division/count/suffix budget | Refusals reproduced | Production populations untested |
| Census totals/source seal/reserve prepare+recheck | PASS; corruption refused | Synthetic rows, actual reserve pin |
| Faithful preparation gate | Refuses zero camera rows | Real >=95% identity gate untested |
| Full preparation/effective/RGB/CPU-first-batch/GPU checks | NOT RUN | Missing production models/streams/frames; detailed list in REPORT.md |
Deriver: tools/derive_kit_h1.py:581,639 and payload/d.py require matching candidate + SHA-pinned report, store report in add_k, reject stale READY/PREPARATION_ONLY.
Tests: 19 deriver checks including full FIXTURE derivation; native equality/mutation, routing audit, package/bootstrap/7 patch cases and existing gate binding PASS. No production proof manufactured.
Operator: regenerate -> verify -> re-derive -> patch -> o.sh -> g.sh -> review.json -> z.sh derive -> certify -> go.json -> s.sh; current patch is blocked inspection only.
q.sh SHA256 e98ee52f4af1c29018c7e7a1a611febdb0bd4c1f201f113ea0f1e327a5bd9de6; deriver SHA256 30259ffdf1b1392e375719e722f69dc36f2d5dcafab18653a7de0f36121271bf.
Tool SHA256 12781e6e0f8b11e86d8bd2c27814aabf56899c0724a4dcb343077bfaf9cf80ee; payload sums SHA256 2ebf1fea93ce0f397d08831617a6341c0dce0fed0c0af80f9e11a5aa7abe5780.
Patch SHA256 cab79c47159750462acfa2f9aca88e7dba499c69be880c849c55b01ce38401b2; upload SHA256 157810fe3209b0d5b0c5177552030cbef2240acbb7a597c54c252801709fd2fc.
Identity remains 40d8d70da5f9de29a722a6146612475c224ce735370a2fea1868b351688880a4; final selection identity and final deployment patch await production equality. Exact delivery hashes: evidence/fix7_selection/delivery.json.
Scope: trinity-1-3, local CPU only; no SSH/network/Orchard/GPU/Git/deletion or external-root search. TEST_ONLY evidence never ships.
