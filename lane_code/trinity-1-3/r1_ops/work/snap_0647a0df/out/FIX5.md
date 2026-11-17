Fix 5 delta against `/scratch/jjyeung/orch_n30/r1_ops/work/snap_a6b70ef2` (frozen config a6b70ef2).

Config identity: `782f303d81e300b1b24094863d6ce7d984690529f0e414474c3e693df87e19da`. Archive: `p_1130b378.tar`. SHA256: `21e1ec609e9b965c10db21cb7309f0623095b7d87f67ac40cebccaf6b44e7401`.

The full census checks 204,413 unchanged v7 rows. All 431 traced room rows are eligible. The room cell draws 1,720 rows over 1,000 steps (1.72/step), below the four-repeat cap of 1,724 draws. All one-line room rows and out-of-range-frame, missing-relation and numeric-think mutants are refused. See proof/ROOM_GRAMMAR.json and logs/tests.log.

The loader audit prints toward/away draw shares of facing, decoded back-answer share among away-hard draws (including back-left/back-right, with exact-back separately), cm/ft/in draws and eligible/drawn absolute-distance counts by scannetpp/, scannetppv2/, scannet and arkit prefix. Local routing counts are explicitly NOT_RUN/null; the production proof uses the same code on staged routing rows. Routing selection is unchanged.

Units remain unbound at zero dose and appear under absent_on_P. The local required-family check has no missing family; unavailable native camera populations remain NOT_RUN. Production CPU proof on Orchard, full RGB admission and independent review remain pending. All eight proof checks are exercised by the local proof fixture.

Draw breakdown: `{"away_hard": {"back_definition": "Decoded option contains the word back, including back-left and back-right; exact_back counts only back.", "back_draws": 2356, "back_share": 0.848397551314368, "draws": 2777, "exact_back_draws": 0, "exact_back_share": 0.0}, "facing": {"away": {"draws": 10838, "share_of_facing": 0.5964777105118327}, "toward": {"draws": 7332, "share_of_facing": 0.4035222894881673}}, "routing_absolute_distance": {"drawn": {"arkit": null, "scannet": null, "scannetpp/": null, "scannetppv2/": null, "unknown": null}, "eligible": {"arkit": null, "scannet": null, "scannetpp/": null, "scannetppv2/": null, "unknown": null}, "status": "NOT_RUN"}, "units": {"draws": {"cm": null, "ft": null, "in": null}, "status": "NOT_RUN"}}`.

Changed source/config files:

- `tools/admission_census.py`
- `tools/finalize.py`
- `tools/rebind.py`
- `tools/run_local_checks.py`
- `tools/selection_check.py`
- `tools/unit_binding.py`
- `tools/write_fix5.py`
- `tests/test_packet.py`
- `configs/diff_against_deployed.json`
- `configs/diff_against_h1_1.json`
- `configs/r1p.json`
- `work/tree/student_pilot/loader_audit.py`
- `work/tree/student_pilot/type_mix.py`
- `out/SAMPLER_REVIEW.patch`
- `out/DEPLOYMENT_REVIEW.patch`

The optional unit packing path is built and remains off. No unit source is bound; Proof 1 keeps units at zero and lists them under absent_on_P.

The read-only candidate is `/scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl`, SHA256 `5f9383fa3dabcc813676564c8533e0c7b110a7f1d0e9aff4c9ebde444355a0b3`. COUNTS.json declares 747 rows: 683 ft, 64 in, and 0 cm. All 747 pass sealed semantic validation when the native packer reconstructs the omitted event envelope; every supplied field stays unchanged. The packed source preserves the original source_qid. Inches remain below the 100-row sampling threshold.

`tools/rebind.py --pack-unit-slice` calls `tools/unit_binding.py:pack_slice`. The helper checks the slice SHA, reconstructs events with sealed `ground_rows.pack`, compares every overlapping payload field (the packer's duplicate source_qid is ignored and the supplied source_qid is retained), resolves the exact 32 frame indices with sealed `s1_routing.Frames`, then runs sealed `s1_pool.validate_source_row`. It rejects any changed target, answer, ground record, response or span. It never invokes generation or repairs a failed row. The source is added through the existing native selection/binding path, compressed into u.gz, catalogued as U_Faithful and staged in the private routing namespace. Native regeneration, routing materialization and production RGB admission still run before the loader samples it.

Orchard must provide the complete staged frame map, frame plan and FPS authority whose SHA256 values match `config.s1_routing.frame_map`, `frame_plan` and `fps_authority`, plus every mapped RGB file. The map must contain all requested (dataset, scene, frame index) entries; the plan must supply required full frame counts, and the FPS authority must resolve each scene without conflict. No frame hash or path may be invented. The manifest is JSON with exactly those three keys, each containing a path and sha256 pin. Resolving the pins alone does not verify RGB bytes; the sealed production preparation must hash and admit the actual staged images.

Run the following only in a complete rebind workspace where those Orchard-resolved authorities are available under the manifest's paths. This lane did not contact Orchard or stage real unit frames:

```bash
/scratch/jjyeung/envs/p1cpu/bin/python -B tools/rebind.py \
  --receipt /scratch/jjyeung/orch_n30/rows_r1/out/a2_vqa_v7/vqa/receipt.json \
  --receipt-sha256 8091154cd499c47404c2f3a6d288bff3b061fa71a1d22af5de68337fbbde56cd \
  --orchard-store /project/community/jjyeung/okh7/s_22b44165/d.db --reuse-census \
  --unit-rows /scratch/jjyeung/orch_n30/rows_r1/out/units_p_slice_v3/rows.jsonl \
  --unit-rows-sha256 5f9383fa3dabcc813676564c8533e0c7b110a7f1d0e9aff4c9ebde444355a0b3 \
  --pack-unit-slice --unit-frame-authority "$FRAME_AUTHORITY" \
  --unit-frame-authority-sha256 "$FRAME_AUTHORITY_SHA256" \
  --units-allowlist ft --unit-cents 100
```

The same pack_slice helper ships as u.py in the operator archive. An Orchard operator can use that helper with the authenticated trainer tree and staged authorities to produce the packed file there; the ordinary pinned `--unit-rows` path can then consume that file in the complete rebind workspace. Any transfer or execution requires the operator's own authorized workflow. The option does not fetch missing frames or redirect a local path to Orchard.

The reviewer must check the candidate and authority hashes, preserved payload and source joins, unchanged sealed module hashes, exact frame-index agreement, every frame pin against real RGB bytes, the native retained indices and scene/QID/label exclusions, and the final routing/source-selection hashes. The production audit must report post-filter ft/cm/in counts, the configured allowlist and cap, and no missing required family. The reviewer must also check the extent-audit evidence named by COUNTS.json; native admission alone does not establish that semantic review.

`proof/UNIT_PACKING_CHECK.json` records the all-row event reconstruction and a fixture that exercises native frame resolution, packed-source binding and regeneration. Its synthetic RGB pins certify only the code path. No admission predicate or supplied training payload changed. Real Orchard frame resolution and RGB admission remain NOT_RUN.


Generated outputs bind the current identity: R1P_PACKET.md, REPORT.md, GATES.json, BINDING.json, MIX.md, SHA256SUMS and the operator archive. No Git, SSH, Orchard, GPU, deletion, full lane copy or write outside this lane was used. The requested snapshot delta is retained for review; packet prose describes current state.
