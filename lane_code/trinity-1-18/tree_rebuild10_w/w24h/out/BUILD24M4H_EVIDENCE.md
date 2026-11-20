P's launch and run binding identify tree b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b. Its source seal 0bc9414250b2ce082a5a1a74fb9421da991f0b794b6ed6c362ab96e92c11dea6 and pin map identify archive e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536, 9,963,520 bytes. The supplied Orchard listing lacks that archive in the destination u/ directory. ORCHARD_COPIES_24M4H.json names the exact P-kit source. Runtime code checks both the complete archive hash and its sealed file inventory before extraction.

The offline tree contains all 799 exact sealed files, assembled from the named local snapshots by per-file SHA256. Its 204-entry s1_pool implementation equals selection 5db993b1 exactly. The real selected_rows reader passes its implementation check and stops at the unavailable production manifest; the exact native build guard also passes. The locally generated test tar has different archive bytes and is never an upload source. The original P archive itself was not available locally.

P's builder embeds source and frame-authority paths in rows. rb.py binds authenticated staged inputs at P's logical paths inside a private filesystem view, then imports only P's extracted tree through isolated Python. This preserves those row strings while relocating physical reads to staged bytes. It runs P's own relocate and build; it does not call prepare. Both the original and relocated selection must match the recipe's source set and the presence/value of status, reason, retained and per_type. The full database-hash gate remains mandatory. rg.py uses the same reconstruction function for its P comparison. The /project namespace smoke test and native guards pass; production row bytes, processor inputs and final database reproduction are not exercised.

N uses a new preparation seed whose 14-source manifest changes only the four specified source statuses. Tree C's existing non-final-source rule supplies the deferral. The complete source catalog and room-set authorization remain available, including U_Faithful. The resolver preserves N's routing inputs instead of substituting P's input specification. The native refresh still applies N's exact 13 removal entries. The kit compares all prepared statuses against P before modes r and q build. Native source-policy evaluation matches all 14 sources; complete Pool construction and prepare stop at missing authenticated EXCLUDE_ROOM_RELEASE.tsv. OFFLINE.json names the absent pins. No final N count is claimed; C's preparation, removals and routing contracts must determine it.

The source-policy statuses are:

| Source | Expected status | Native manifest-policy reason |
|---|---|---|
| ARKIT_gaps | ELIGIBLE | — |
| ARKIT_gen_r2 | ELIGIBLE | — |
| ROUTE_direct | DEFERRED | source_not_final |
| SCENE_room | DEFERRED | source_not_final |
| SCENE_room_sppK | DEFERRED | room_set_not_authorized |
| T0_gaps | ELIGIBLE | — |
| T0_gen_r2 | ELIGIBLE | — |
| T0_room | DEFERRED | source_not_final |
| T1H1_gaps | ELIGIBLE | — |
| T1H1_gen_r2 | ELIGIBLE | — |
| T1H1_room | DEFERRED | source_not_final |
| T1H2_gaps | ELIGIBLE | — |
| T1H2_gen_r2 | ELIGIBLE | — |
| U_Faithful | ELIGIBLE | — |

The kit publishes each build artifact independently, so a partial failure does not suppress a sibling receipt. The publication tests simulate a producer that writes diagnostics and raises, then compare published bytes for modes r and q. INTEGRATION.json verifies that each mode's source-status refusal runs before build. No production build was stubbed into a claimed success.

The arming helper authenticates the native receipt file and its canonical digest separately from the generated database SHA256. The review still binds the exact selection file and generated database hashes. The helper checks database metadata for both generated and input databases, and leaves tree C's native receipt-digest comparison unchanged. NATIVE_ARM_TESTS.json distinguishes its real helper/scanner/native-check execution from its synthetic materialization.

An inherited resolver600 test imported an external builder that rewrote three files under w24/work/build21 before raising. WRITE_BOUNDARY_INCIDENT.json names every file and its resulting hash; the rewritten k/s.json still matches its existing seal. The two input configs were not snapshotted before that import, so their prior bytes are not asserted. No external restoration was attempted. All subsequent tests run with the host read-only and only w24h writable. Exact failure output is retained under attic/build24m4h/ and indexed in FAILURES.json.
