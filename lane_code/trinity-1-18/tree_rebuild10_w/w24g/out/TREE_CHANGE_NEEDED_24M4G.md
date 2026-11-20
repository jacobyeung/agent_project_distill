TREE_CHANGE_NEEDED: tree C rejects P’s authenticated historical selection.

P’s recipe consumes selection `5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af`. Its exact local copy is `work/build24m4g/inputs/5db993b148c7aa1ace685f7c29b0e20daa6ac4e3e5b3613e4c3fc2b24bdde2af`, copied after hash verification from `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/build24m4/hidden/inputs/`. Recipe `0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a` and P config `b08fe50cdc374c82a36ddb01d6492fed1361b1b2e3308a8e0d9b32af675b4fad` both bind that selection. P’s catalog `eac5f9f01587803b2402f80cc310b75ec1f960270a6bc059416b1e1407b1e7c9` also defers ROUTE_direct as moved_to_vqa_store.

Both refresh conditions differ. P’s selection has 204 implementation entries, tree C has 274, and 143 entries differ across their union. The s1_pool.py hashes are P `7b8859d629dc30be0b3b6749e7539d324cd2d0595cba4de67a16454ef0660ee7` and C `80af9b8f3817fc3cfa5c85ac99afef37c97ca95f5181e5aa63d71bde4b3b2323`. After path normalization, the selection has six removal entries and P’s config has eight: P adds `02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411` and `caba6a5695781491036de5b3acdb20db2d42ab581e5775fec3fe07fbd2114aad`. This is not merely a path difference.

In kit b/i.py, either mismatch triggers relocate followed by prepare. Because removals differ, `if key=='implementation' or changed:continue` skips every before/after comparison. Tree C therefore chooses a new population instead of preserving P’s source statuses and indices. Job 173567’s r.log confirms ROUTE_direct ELIGIBLE with 9,423 retained in base_refresh/s, versus P’s DEFERRED status. The 9,091 figure belongs to the separate planner pool at p/i/pool/s. SCENE_room becomes ELIGIBLE with 384 rows in both paths. P’s recipe reports native_rows=47,898, source_denominator=180,035, and direct_rule_audit={}.

Relocation alone cannot repair this within the native interfaces. s1_pool_relocate.relocate deep-copies the original implementation. student_pilot/s1_routing.py:224 rejects any selection whose implementation differs from s1_pool.implementation(), and student_pilot/s1_pool.py:226 repeats that check in selected_rows. A real call to selected_rows on the authenticated P receipt raises `Pool selection implementation differs` before reading any row body. Evaluating the exact routing-build guard against that receipt raises `Routing selection belongs to another implementation`; this second probe isolates the guard and does not run build(). Relabeling the historical receipt as produced by C or monkeypatching these guards would bypass the compatibility check, not establish compatibility.

The minimal native change is an explicit, narrowly authenticated historical-selection reader path shared by build() and selected_rows(). It must bind P’s exact original selection and recipe hashes, preserve the original producer implementation and every source/row-index pin, permit only authenticated relocation, and retain current row, exclusion, schema, scene-census and hash checks. The default implementation-equality rule must remain strict. The authorization must survive relocation without accepting arbitrary foreign receipts. No producer re-preparation is needed. This requires changing the two native compatibility gates; no tree or kit code was changed here.

With that native path available, the kit should pass P’s pinned selection through relocation, compare the exact source set and presence/value of status, reason, retained and per_type against recipe.pool_selection_counts before build(), and emit `R1_RECONSTRUCTION_SELECTION_DIFFERS:<source>` on any mismatch. rb.py must retain its exact database hash check against `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84`. Production row-byte compatibility and that database hash still need verification with the missing inputs.

The offline comparison checks every field present in all 14 recipe summaries, including counts and per-type counts. All match. Each eligible source’s pinned index file also matches its SHA256, retained count and sorted unique nonnegative index contract:

| Source | Status | Reason | Retained | Recipe match |
|---|---|---|---:|---|
| ARKIT_gaps | ELIGIBLE | — | 6560 | PASS |
| ARKIT_gen_r2 | ELIGIBLE | — | 11321 | PASS |
| ROUTE_direct | DEFERRED | moved_to_vqa_store | — | PASS |
| SCENE_room | DEFERRED | moved_to_vqa_store | — | PASS |
| SCENE_room_sppK | DEFERRED | room_set_not_authorized | — | PASS |
| T0_gaps | ELIGIBLE | — | 11052 | PASS |
| T0_gen_r2 | ELIGIBLE | — | 22290 | PASS |
| T0_room | DEFERRED | moved_to_vqa_store | — | PASS |
| T1H1_gaps | ELIGIBLE | — | 5919 | PASS |
| T1H1_gen_r2 | ELIGIBLE | — | 11012 | PASS |
| T1H1_room | DEFERRED | moved_to_vqa_store | — | PASS |
| T1H2_gaps | ELIGIBLE | — | 5130 | PASS |
| T1H2_gen_r2 | ELIGIBLE | — | 9314 | PASS |
| U_Faithful | ELIGIBLE | — | 747 | PASS |

The proposed preflight in work/build24m4g/diagnose.py rejects a mutation that flips ROUTE_direct to ELIGIBLE with `R1_RECONSTRUCTION_SELECTION_DIFFERS:ROUTE_direct`. This is a tested diagnostic proposal, not an installed runtime fix. EVIDENCE.json records each actual/expected summary, all index-file hashes, implementation differences, removal lists, native refusal output, and timings.

The other consumers also need attention. pl.py:182 calls refresh unconditionally for modes r and q. N’s pinned selection `d1e6715a19b5d9a15f647e3495815c63329afbc9b69cd81bbef8fcd086025c64` differs from P before refresh: it has 13 sources, already enables ROUTE_direct/SCENE_room/T0_room/T1H1_room, and omits U_Faithful. N’s selection has six removal entries while N’s config has thirteen; its implementation also differs from C. The job’s planner refresh emits fourteen sources, including U_Faithful=718 and ROUTE_direct=9,091. Thus fixing only rb.py would leave N’s regenerated routing population different from P’s pinned selection. Mode q’s native launch_r1/entry.py:273 subsequently calls build with this prepared configuration; the card’s “trains on P’s own routing stream” is not established by this path. No successful training population is claimed because launch and admission were not run.

rg.py:39 repeats P’s refresh before its comparison build and has the same incompatibility. Its first build uses the incoming planner configuration. cs.py does not call refresh: sources() reads every available source population from the configured selection for the pre-admission census, regardless of status. The census is not the training selection and should not be narrowed to eligible rows. Preserve that census contract while binding the actual routing selection to P’s recipe. These consumers remain unchanged under the stop instruction.

All nine eligible pool row bodies, the frame map `17aa3e9eb8f5757b6121b60e753e42b0b80e73b18c03ca678859349e25d51ec3`, and frame plan `7cc01f3655130e9d7ef2c1fd597c5cd7c1ddbcb49314a4dce7aecc040ec88cba` are absent at the named production paths and supplied input locations checked in EVIDENCE.json. No cluster-wide search was performed. Production relocation, preparation, build, frame resolution, direct audit and full database reconstruction were not exercised. The inherited STILL_MISSING_24M4E.md separately identifies T0_gen_r2’s row body as a fixture boundary.

The input archive hash, tree C seal and all four kit seals reproduce. Tree C, every kit, arm_routing.py and ARM_ROUTING_USAGE.md remain unchanged. GO remains false for the active q, n and qd kits and true only for the active out/kit_n_go template. Historical fixture copies remain as supplied. No reseal, new upload delta, GO delta or release archive was produced. Naming/resolver/guard suites and decoded scans were not run because this is the requested tree-change stop branch.

Diagnostic failure retained: attic/build24m4g/diagnostic_attempt1/diagnose.log records `KeyError: U_Faithful` from a comparison that assumed equal source sets. The completed diagnostic handles the union explicitly; its output is work/build24m4g/diagnose.log. This failure was a Python exception, not a cluster kill. The script and its input copies are preserved in attic. A report-generation script also failed at parse time with `SyntaxError: invalid character '—' (U+2014)` after shell quoting removed Python string quotes; its script and output are preserved in attic/build24m4g/report_attempt1/. The corrected report script runs successfully. No deletion, network, SSH, GPU, Git, scheduler or other-agent operation ran.
