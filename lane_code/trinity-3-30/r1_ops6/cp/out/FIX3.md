Fix 3 review delta against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_1ec4a936/` (config `1ec4a936d86d0f93237a704e276a8b1b54dd6a7e465990d9ba6f4089ae559feb`).

The bound config is `841f06376f20f7a446592f9af2daea2458e8b61ebf6967d37822f615be446948`. The operator archive is `p_0a4d6fc3.tar` with SHA256 `db2a80b7832647aef89276a794fa585c9733c6180027eaa63e128938abe942c0`.

Admission-input changes for review: the optional unit path adds `U_Faithful` to the pool manifest and adds exact ordered indices and a compressed transport to staging. It does not regenerate an answer, event or row payload. The caller supplies packed JSONL with full events and 32 frame pins. The binder rejects any row that sealed source admission removes or refuses; it never repairs or silently filters the file. The input SHA and exact decompressed bytes are bound.

Orchard stages `u.gz`, `m.json` and `i.json` from the private bundle into the routing catalog. The augmented manifest retains the inherited exclusion authorities. Native selection regeneration replays the parent and optional unit source, verifies ordered indices and the final selection SHA, and passes the resulting selection to unchanged `s1_routing.build`. The complete RGB map/plan and frame store must already cover the supplied pins. Native materialization applies frame, division, scene, QID and token checks; the loader proof sees only its final admitted rows. No frame bytes are bundled or fetched by this lane.

The selector fingerprints its full import closure, which includes sampler modules. Its recorded implementation now matches the bound trainer tree. The projection tool checks this closure against the code record and permits changes only in the sampler modules; admission-predicate hashes stay equal to the parent. This fixes a fingerprint mismatch without editing admission predicates.

The current packet has no bound unit file. Its units cell is zero. A bound file is capped at 4 × eligible / 1,000 rows per step, rounded down to hundredths; any cm, ft or in population below 100 is named missing and fails the required-family check. Production recomputes those counts after filtering.

The local required-family gate checks real VQA populations and source-selected absolute distance. It does not invent counts for the unavailable legacy camera database: those three counts remain NOT_RUN. The production gate uses final staged populations; an observed missing required family fails. Recovery, room and size are named under absent_on_P and do not fail the gate.

File changes:

- `tools/derive_deployment.py`: Stage optional unit source/manifest/indices as pinned read-only inputs and require native unit-regeneration evidence before production derivation.
- `tools/finalize.py`: Render the ruled family set, scoped gates, unit staging/regeneration instructions, and full resource-bearing sbatch line; checksum the delta artifacts.
- `tools/make_proof.py`: Parameterize advanced/general, keep explicit CPU resources, reject GPU allocation and partition mismatch, and record partition/node plus absent_on_P in the receipt.
- `tools/package_operator.py`: Include the unit helper and optional opaque unit artifacts in the deterministic operator archive.
- `tools/rebind.py`: Bind optional unit rows and exact SHA; cap the unit dose and refill routing; bind advanced/general proof partition; rebind the selector import closure to the actual trainer tree; refresh all identity-bound outputs.
- `tools/run_local_checks.py`: Include the vehicle-family module in the trainer review patch and refresh the snapshot delta before finalizing the packet.
- `tools/seal_proof.py`: Bind the requested proof partition and require native unit-regeneration evidence for a unit-bound packet.
- `tools/selection_check.py`: Verify native parent selection, authenticate the updated implementation closure against the code record, preserve predicate hashes, and optionally regenerate the bound unit source.
- `tools/unit_binding.py`: Add a pinned packed unit source via sealed native pool admission, deterministic byte-preserving gzip, a new manifest entry and native ordered indices. Regenerate and compare the unit selection on staged inputs.
- `tools/write_fix3.py`: Generate this file and the unified source/config/trainer delta directly from the frozen snapshot without Git.
- `tests/test_packet.py`: Test zero-dose absences, exact 32.89 direction, missing required families, unbound-unit refusal, native unit binding/regeneration, immutable payloads, four-repeat cap, the 100-row threshold and both CPU partitions.
- `configs/diff_against_deployed.json`: Regenerate the final identity-bound configuration and its field-level comparison from the current mix and sealed tree.
- `configs/diff_against_h1_1.json`: Regenerate the final identity-bound configuration and its field-level comparison from the current mix and sealed tree.
- `configs/mix.json`: Set the vehicle-P policy, direction to 32.89, and size/room/recovery/unbound units to zero. Redistribute the 3.87 routing rows proportionally across its four native cells; preserve stream totals.
- `configs/r1p.json`: Regenerate the final identity-bound configuration and its field-level comparison from the current mix and sealed tree.
- `work/tree/student_pilot/loader_audit.py`: Use the common family gate; count bound units by unit and dataset after preparation; print absences. Preserve staged-file traces and the full 1,000-step sampler audit.
- `work/tree/student_pilot/type_mix.py`: Validate the vehicle-P policy and reject unbound unit doses/refills. When units are bound, reject unit rows outside that source. Preserve the four-repeat cap.
- `work/tree/student_pilot/vehicle_p.py`: Define required families and named absences once for local and production gates. Report missing cm/ft/in below 100; fail observed missing required populations. Keep unavailable local legacy-camera counts NOT_RUN.

Generated outputs:

- `out/config.json`, `out/BINDING.json`, `out/records/{c,d,j,r,v}.json`, and the pinned producer receipt: bind the current config, tree, selector implementation, store receipt, routing policy and pending independent review.
- `out/ADMISSION_BY_TYPE.json`, `out/ROUTING_DIAGNOSIS.json`, `out/MIX.md`: retain the v6 row census and distinct diagnostic refusals; report the current capped mix, bound-unit state and named absences.
- `out/proof/{inputs,loader_audit,local_prepared,local_config,OFF_IDENTITY,FIRST_BATCH,DERIVATION,GATES}.json`, `out/proof/{off_candidate,off_sealed}.json`, `out/proof/traces.jsonl`, `out/proof/selection/{r,q}.json`: regenerate evidence against the bound identity, with local/production scope explicit.
- `out/proof/p.py`, `out/proof/p_29c71287.sh`, `out/r1p_code.tar`, `out/p_0a4d6fc3.tar`: regenerate the CPU proof and deterministic code/operator archives.
- `out/operator/`: refresh exactly the current files listed in `out/operator/sums.txt`; the archive contains that inventory only. Unreferenced files from other identities remain on disk under the no-deletion rule.
- `out/OPERATOR.json`, `out/REVIEW_REQUEST.json`, `out/SAMPLER_REVIEW.patch`, `out/DEPLOYMENT_REVIEW.patch`, `out/REPORT.md`, `out/R1P_PACKET.md`, `out/SHA256SUMS`, `STATUS.md`: publish the current bindings, review deltas, operator instructions and local validation status.
- `out/FIX3.md`, `out/FIX3.diff`: give the frozen-snapshot reviewer this change inventory and a unified diff of tools, tests, configs and trainer sources.
- `out/logs/`: preserve CPU-only rebind, unit-fixture and local-check command output. New `work/audit_*`, `work/derive_*` and `work/test_*` directories hold generated audit files and isolated fixtures; they are not production inputs.

Fixture scope: the diagnostic slice supplies faithful admitted ft/in examples. Because it contains no admitted cm example, the fixture uses a synthetic cm metadata variant solely to test counting and the 100-row rule. This does not certify real cm conversion fidelity. Production binding never packs rows or changes metadata. A separate fixture checks actual sealed label refusal and incomplete-event/frame refusal.

Validation: `tools/rebind.py --reuse-census` and `tools/run_local_checks.py` run locally with CUDA disabled. `out/logs/tests.log`, `out/proof/GATES.json` and `out/SHA256SUMS` are the current validation records. No SSH, Orchard, Git, deletion or edit outside this lane occurs.

The report uses current-state prose. This requested snapshot delta is the sole historical comparison retained for review.
