import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
s=J.load(D/'SEALS.json');up=J.load(L/'out/UPLOADS_24M4H.json');policy=J.load(D/'OFFLINE.json')['policy_statuses']
usage='''Run this helper after an independent review passes. Use the exact selection, published native receipt, database metadata and RESULT from that review. The RESULT must contain the selection file SHA256, the generated database SHA256 and the word PASS.

```bash
L=/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24h
: "${SELECTION_FILE:?Set the local path to routing_selection.json}"
: "${RECEIPT_FILE:?Set the local path to the published receipt.json}"
: "${DB_METADATA_FILE:?Set the local path to db_bytes.json}"
: "${REVIEWED_SELECTION_SHA256:?Set the independently reviewed selection file SHA256}"
: "${REVIEWED_REGENERATED_SHA256:?Set the independently reviewed generated database SHA256}"
: "${REVIEW_VERDICT:?Set the local path to the independent RESULT file}"
nice -n 10 bash "$L/work/build24m4h/run.sh" "$L/out/arm_routing.py" \\
  "$SELECTION_FILE" "$DB_METADATA_FILE" \\
  --regenerated-receipt "$RECEIPT_FILE" \\
  --reviewed-selection-sha256 "$REVIEWED_SELECTION_SHA256" \\
  --reviewed-regenerated-sha256 "$REVIEWED_REGENERATED_SHA256" \\
  --review-verdict "$REVIEW_VERDICT" \\
  --output "$L/out/routing_armed"
```

The output directory must be new and lie within L. The runner uses isolated Python, limits CPU threads and memory, and exposes only L as writable. Copy the evidence into L before running it. If the selected routing-base receipt differs from the bundled receipt, add `--routing-base /absolute/local/path/to/receipt.json`.

For a native selection, `regenerated_sha256` is the canonical digest of the generated receipt because tree C compares that digest during admission. It is not a database hash. The helper authenticates the supplied receipt against `selection.regenerated_receipt.sha256`, recomputes its canonical digest, checks its stream and row count, and requires its database SHA256 to equal the independently reviewed generated database hash. The database metadata must contain a positive, consistent size for that generated database and for the input routing-base database. The input and generated databases may differ. The selected base receipt must authenticate the input database and already belong to the staging inventory.

The helper retains both independent review hashes and the RESULT hash. It rejects changed receipt bytes, fabricated receipt digests, mismatched database hashes, missing metadata and changed row counts. Selections without a native receipt retain the strict database-hash check used by the compact legacy fixtures. No helper check substitutes for the independent review of production rows.

Apply `UPLOADS_24M4H.json` and the verified P-tree copy in `ORCHARD_COPIES_24M4H.json` before any armed delta. `UPLOADS_24M4H.list` includes every delta name; `UPLOADS_24M4H_LOCAL.list` includes only local upload files. The remote-copy row has no local payload and names its exact P-kit source, SHA256 and size.

The helper creates `kits/{q,n,n_go}` with GO=false, scans and reseals them, and writes `UPLOADS_ROUTING_ARMED.json/.list`. It prints all three seals and the decoded-payload and capsule-file hashes of armed n_go `k/c.json`. The generated database is rebuilt during mode q; the input database must already be staged. Neither database nor the n_go copy enters the ordinary armed upload stream. Runtime checks still authenticate staged bytes and sizes.

The kit publishes the selected build's raw `materialization.json`, `receipt.json` and `refresh.json` under `o/<job>/`, including on a failing shell exit when those files exist. `a6.json` maps the additional neutral filenames to their source paths and SHA256 values; those include P's base/comparison receipts and both refresh paths. A build that fails before producing a receipt cannot publish that nonexistent receipt.

`work/build24m4h/NATIVE_ARM_TESTS.json` records a real helper run, decoded scans and tree C's unchanged receipt-digest check with synthetic materialization. `ARM_TESTS.json`, `REVIEW_AUTH_TESTS.json`, `ARM_COVERAGE.json` and `ARM_MISSING_DB_TEST.json` record the other fixtures. These checks do not constitute a production review, upload, launch or full routing reconstruction.
'''
replace(L/'out/ARM_ROUTING_USAGE.md',usage)
card=f'''N uses tree C `0c7614c8eff74201db275489af9c3fa11f3b418693a0239b793e6322685298de`.
The kit seals are q `{s['q']}`, n `{s['n']}`, n_go `{s['n_go']}` and qd `{s['qd']}`.

| Card row | Kit behavior | Evidence and remaining measurement |
|---|---|---|
| Routing | N prepares the nine sources eligible in P's selection under tree C, with all 13 N removal entries. ROUTE_direct, SCENE_room, T0_room and T1H1_room remain deferred; SCENE_room_sppK remains unauthorized; U_Faithful remains eligible. Every build checks all 14 source statuses against P. | P's 47,898 rows describe P's database. N's final row count is unmeasured and must come from N's materialization receipt. Matching source statuses does not establish identical rows, order or count. |
| Reconstruction | The kit runs P's sealed tree in an isolated child and checks the reconstructed database against the complete `4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84` hash. P's selection is relocated without preparation. | Both P implementation guards pass offline. Full production reconstruction remains untested because the production inputs are absent. |
| Configuration identity | Both routing-input capsules bind a new manifest and preparation seed, plus P's tree pin. The final identity therefore changes. | `work/build24m4h/INVARIANTS.json` records both capsule identities and hashes. The runtime review must bind the prepared identity. |

The manifest sets the four deferred sources' `status` to `deferred`; tree C's existing `Pool.deferred` treats every non-final source as deferred. It keeps every source entry and exclusion membership, so the census can still read complete source populations. P's augmented manifest includes U_Faithful, and P's room-set authorization keeps SCENE_room_sppK deferred. The seed retains P's producer identity and is explicitly marked as requiring native preparation; the kit never relabels it as a C receipt.

The native policy check matches all 14 statuses. Full preparation cannot run with this fixture: the authenticated room-release list is absent, and row bodies and other production inputs remain unavailable. The removal lists, initialization, opener rows, step-544 lineage, census semantics, admission checks and checkpoint publication order remain unchanged.

The ordinary delta contains {up['local_upload_files']} local files ({up['local_upload_bytes']} bytes) and one P-tree copy ({up['orchard_copy_bytes']} bytes) against the supplied 24m4e state. GO is false except in the unuploaded `out/kit_n_go` template. Arming produces GO=false copies and requires the independently reviewed selection, published native receipt and database metadata described in `ARM_ROUTING_USAGE.md`.
'''
(L/'out/N_CARD_KIT_ROWS_24M4H.md').write_text(card)
detail='''P's launch and run binding identify tree b83a8a35d420815b9d6396e1fc1178e94c20d47ad459aa6da964e85bdec0f87b. Its source seal 0bc9414250b2ce082a5a1a74fb9421da991f0b794b6ed6c362ab96e92c11dea6 and pin map identify archive e5be8157d855b4c9f611876b7fde5d0c7d8bd11def319e15c00e37daef2c3536, 9,963,520 bytes. The supplied Orchard listing lacks that archive in the destination u/ directory. ORCHARD_COPIES_24M4H.json names the exact P-kit source. Runtime code checks both the complete archive hash and its sealed file inventory before extraction.

The offline tree contains all 799 exact sealed files, assembled from the named local snapshots by per-file SHA256. Its 204-entry s1_pool implementation equals selection 5db993b1 exactly. The real selected_rows reader passes its implementation check and stops at the unavailable production manifest; the exact native build guard also passes. The locally generated test tar has different archive bytes and is never an upload source. The original P archive itself was not available locally.

P's builder embeds source and frame-authority paths in rows. rb.py binds authenticated staged inputs at P's logical paths inside a private filesystem view, then imports only P's extracted tree through isolated Python. This preserves those row strings while relocating physical reads to staged bytes. It runs P's own relocate and build; it does not call prepare. Both the original and relocated selection must match the recipe's source set and the presence/value of status, reason, retained and per_type. The full database-hash gate remains mandatory. rg.py uses the same reconstruction function for its P comparison. The /project namespace smoke test and native guards pass; production row bytes, processor inputs and final database reproduction are not exercised.

N uses a new preparation seed whose 14-source manifest changes only the four specified source statuses. Tree C's existing non-final-source rule supplies the deferral. The complete source catalog and room-set authorization remain available, including U_Faithful. The resolver preserves N's routing inputs instead of substituting P's input specification. The native refresh still applies N's exact 13 removal entries. The kit compares all prepared statuses against P before modes r and q build. Native source-policy evaluation matches all 14 sources; complete Pool construction and prepare stop at missing authenticated EXCLUDE_ROOM_RELEASE.tsv. OFFLINE.json names the absent pins. No final N count is claimed; C's preparation, removals and routing contracts must determine it.

The source-policy statuses are:

| Source | Expected status | Native manifest-policy reason |
|---|---|---|
'''
for name,v in sorted(policy.items()):detail+=f"| {name} | {v['status']} | {v['reason'] or '—'} |\n"
detail+='''
The kit publishes each build artifact independently, so a partial failure does not suppress a sibling receipt. The publication tests simulate a producer that writes diagnostics and raises, then compare published bytes for modes r and q. INTEGRATION.json verifies that each mode's source-status refusal runs before build. No production build was stubbed into a claimed success.

The arming helper authenticates the native receipt file and its canonical digest separately from the generated database SHA256. The review still binds the exact selection file and generated database hashes. The helper checks database metadata for both generated and input databases, and leaves tree C's native receipt-digest comparison unchanged. NATIVE_ARM_TESTS.json distinguishes its real helper/scanner/native-check execution from its synthetic materialization.

An inherited resolver600 test imported an external builder that rewrote three files under w24/work/build21 before raising. WRITE_BOUNDARY_INCIDENT.json names every file and its resulting hash; the rewritten k/s.json still matches its existing seal. The two input configs were not snapshotted before that import, so their prior bytes are not asserted. No external restoration was attempted. All subsequent tests run with the host read-only and only w24h writable. Exact failure output is retained under attic/build24m4h/ and indexed in FAILURES.json.
'''
(L/'out/BUILD24M4H_EVIDENCE.md').write_text(detail)
print('Usage, corrected card and detailed evidence written')
