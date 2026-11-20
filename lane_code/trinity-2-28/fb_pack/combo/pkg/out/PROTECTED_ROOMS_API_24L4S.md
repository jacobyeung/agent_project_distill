`student_pilot.r1_rooms.check_protected_rooms(cfg, stream, source_rows, admitted_rows)` checks the complete source and admitted populations of one stream. It consumes each iterable once, returns counts, and never filters or edits rows.

The kit must call it for `pose`, `vqa`, `routing`, and `pointing`, including streams without a protected list. Call it after the kit has applied removals and formed the final admitted selection. Both iterables yield native decoded row dictionaries, without `(row, target)` wrappers. Preserve provenance, canonical fields, QIDs, nested row keys, and label-row keys. Supply every source row before removals and every row actually admitted afterward; use separate iterators. For pose mixtures, include every contributing source and follow the final mixture order for admitted rows. For indexed stores, follow the admitted indices. Do not substitute a sample, a room-count summary, or an already filtered source population.

```python
from student_pilot.r1_rooms import check_protected_rooms

result = check_protected_rooms(cfg, "pointing", source_rows, admitted_rows)
```

For two materialized SQLite stores, the exact adapter is:

```python
import json
import sqlite3
from student_pilot.p3_provenance import pinned
from student_pilot.r1_rooms import check_protected_rooms

# source_database_pin and admitted_database_pin are authenticated database pins.
# Their receipts and counts must bind the complete pre-removal and final populations.
a = sqlite3.connect(pinned(source_database_pin).as_uri() + "?mode=ro", uri=True)
b = sqlite3.connect(pinned(admitted_database_pin).as_uri() + "?mode=ro", uri=True)
try:
    source_rows = (json.loads(raw) for raw, in a.execute("SELECT row FROM rows ORDER BY i"))
    admitted_rows = (json.loads(raw) for raw, in b.execute("SELECT row FROM rows ORDER BY i"))
    result = check_protected_rooms(cfg, stream, source_rows, admitted_rows)
finally:
    a.close()
    b.close()
```

A successful return has this shape; counts describe the supplied iterables:

```json
{"stream":"pointing","source_rows":400,"admitted_rows":80,"protected_lists":1,"listed_keys":320,"checked_keys":320,"protected_rows":0}
```

`listed_keys` counts distinct keys across this stream's role lists. Every listed key must match a source row through native `row_removals.row_keys`; every matching source row must be protected, including rows that share a key. A foreign-stream list contributes no keys or removals. The function stores only the listed/matched key sets, not the source population. Empty admitted populations are allowed; the caller must bind their completeness and count. The function cannot authenticate the origin or completeness of arbitrary Python iterables.

The check loads `Rooms(cfg['r1_training']['room_authority'])`, retaining its five exact authority pins, K1 split `27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390`, teacher pin, and authority counts. Protected rooms comprise K1 held-out rooms and the existing R0 union, including the reserve. Each stream uses the tree's native room authority:

| Stream | Room authority |
| --- | --- |
| `pose` | `Rooms.canonical(row)` followed by `Rooms.room(canonical)`, the resolution used by `Rooms.status` and the shared room census. |
| `routing` | `Rooms.canonical(row)` followed by `Rooms.room(canonical)`, exactly as the routing-source census calls `Rooms.status`. |
| `vqa` | `r1_direction_twins.Binding(cfg).room(row)` when `r1_training.direction_twins` is enabled, exactly as the VQA census does. Binding uses strict `Rooms.status` first, then its authenticated tiered aliases for unresolved rows. Without direction twins, both census and post-condition use strict `Rooms`. |
| `pointing` | Both `provenance.canonical_scene` through `Rooms.room` and the ordinary `Rooms.canonical` / `Rooms.room` resolution. The ordinary resolution retains the tree's field precedence, including row canonical, provenance canonical and dataset/scene aliases. A protected result from either resolution wins. |

These are the tree's census authorities, with pointing's required `canonical_scene` resolution included alongside the shared `Rooms` resolver. `r1_rooms.census` enumerates routing slices and the VQA store; it does not enumerate separate pose or pointing stores. The kit supplies those complete populations to this function.

All four streams also use native `r2_withheld.Withheld`, which authenticates the bundled withheld-80 file (`634820b4...`). Its `touches` check receives row fields, resolved canonical names and physical rooms, including rooms resolved through VQA's tiered aliases. A withheld hit is protected even when it is an opaque alias. The same protection predicate validates listed source rows and checks admitted rows. Thus a clean pointing `canonical_scene` cannot conceal K1/R0 or withheld protection found through another native resolution, and a list cannot remove a row that has no protected resolution.

VQA initializes the same full `Binding` that the census uses, including pinned twin files, aliases, union and source database checks; constructor/authority failures propagate unchanged. Binding reads its authenticated source database once during construction. The function still consumes each supplied source/admitted iterable once. Rows with no resolvable native room or withheld match refuse `R1_PROTECTED_ROOM_UNRESOLVED:<stream>`. Tests exercise native Binding construction and tiered resolution on synthetic pinned SQLite/JSONL files; they do not census the production store's 119,375 strict-unresolved rows.

A config entry is exactly:

```json
{"path":"/absolute/staged/path/pointing_protected.jsonl","sha256":"d21e374f39048c0e142680e0d3b26e5b2b774138747610c1fc4a00da0ec580e1","role":"protected_rooms","stream":"pointing"}
```

Each nonblank JSONL line supplies a nonempty string `row_key`, for example `{"row_key":"native-row-key"}`. The entry has no `defects` option. The known pointing SHA is accepted through this role contract; the tree does not hard-code it. Pose, routing, and VQA lists use the same shape with their own content SHA256. Any number of lists, including multiple lists for one stream, may appear after the first 11 sealed entries and before the unchanged final `NAMING_REMOVE`. Every added SHA must differ from all pinned and added SHAs. The two identical empty-list pins already in the sealed prefix remain valid. Empty extra lists therefore collide with the pinned empty-list SHA and refuse; omit them.

Set `cfg['r1_training']['launch22']['removal_order']` to `[p['sha256'] for p in cfg['remove_files']]`. Config identity already digests the complete entries, including `role` and `stream`; its implementation is unchanged. Regenerate the kit's config identity, source/code seals, dependent receipts, room audit and staging pins for the new inputs. Preserve role metadata when localizing paths. The separate kit owns this work and must bind the census results to the same config and store pins it launches.

| Refusal | Meaning |
| --- | --- |
| `R1_NAMING_REMOVAL_ORDER` | Invalid role, stream, placement, extra shape, SHA duplication, pinned sequence, or spec order. |
| `R1_PROTECTED_LIST_KEY_NOT_PROTECTED:<stream>` | A listed key is absent from that stream's source, or matches a nonprotected source row. |
| `R1_PROTECTED_ROOM_ROWS:<stream>` | An admitted row touches a protected room. |
| `R1_PROTECTED_ROOM_UNRESOLVED:<stream>` | A listed source row or admitted row has no resolvable room or withheld alias. |
| `R1_PROTECTED_REMOVAL_STREAM_REQUIRED` | A role-aware matcher/check lacks a recognized stream. |

Existing authority, naming-content and pinned-byte failures propagate unchanged. `validate_removals` authenticates the final naming list and every added list; native `Removals` authenticates all lists it loads.

`Removals(cfg['remove_files'], stream=stream)` filters only that stream's role lists while retaining global matching for the 12 legacy lists. Alternatively pass `stream` to `keep`, `match`, or `assert_clean`. `files` and reports retain the ordered entries and role metadata. A matcher containing role lists refuses if no stream is supplied. `filter_jsonl(..., stream=stream)` supports the same contract; its filename-only CLI remains a legacy global-list interface.

Native prepare/rank 0 does **not** call `check_protected_rooms`. Both can import and call it with the same inputs, but assembling complete pre-removal sources and final selected rows across ordinary, indexed, prefix and mixed pose stores requires additional reader plumbing. A single call at one existing location cannot cover these paths. Their existing removal assertions now carry stream context; they still refuse listed rows rather than silently remove them. The kit must materialize/select the cleaned stores and call the post-condition before launch.

| Consumer checked | Final behavior and necessary change | Evidence in `tests/test_host24l4r.py` |
| --- | --- | --- |
| `r1_launch22.validate_removals`, `remove_files[-1]`, `naming_rows` | Validator accepts role entries in the designated gap. Last-element naming lookup, its 109 unique keys, and the 12 constants remain unchanged. | `RemovalOrder`; `test_naming_rows_still_requires_exact_109_keys` |
| `row_removals.Removals`, counters, reports, `verify_streams`, `filter_jsonl` | Matcher accepts role metadata and explicit stream context; selected-store verification uses the enclosing stream even for pose mixture parts. Counts remain dynamic. | Same-key collisions, legacy global lists, report counts, selected SQLite stores and pose mixtures, JSONL filtering. |
| `carrier_c1_data.build_stream` | Supplies the stream for VQA; pointing delegates to its target filter. | `test_native_vqa_builder_retains_pointing_key_collision` |
| `ground_target_filter.TargetFilter` | Supplies pointing context; settings retain all pins. | `test_target_filter_is_pointing_scoped_and_retains_metadata` |
| `grounding_targets`, `grounding_train`, `stageb_mdg` | Unchanged; delegate their pointing targets and settings to `TargetFilter`. | Target-filter tests exercise their shared predicate/settings. |
| `carrier_c1_run.prepare`, `prepared` | Existing row assertions pass the actual stream; validation-store assertions pass pose. Receipt equality and `identity` remain unchanged. | `test_prepare_and_rank0_removal_calls_carry_stream` executes native call expressions; identity mutation test; existing 44 host tests. |
| `r1_routing.Filters.reason` | Passes its explicit stream to matching. Composition policy and receipt structure stay unchanged. | `test_routing_filters_use_the_explicit_stream` |
| `scene_division_gate.check_rows` | Passes its declared stream. | `test_scene_gate_and_jsonl_filter_keep_foreign_keys` |
| `r1_rooms.census` | Uses routing for source slices and VQA for the VQA store. Audit reports retain complete entries. | `test_room_census_keeps_routing_slices_and_vqa_store_separate` |
| `r1_rooms.verify_audit` | Unchanged; compares complete entry metadata except paths and uses SHA-based counts/order. | `test_room_audit_binds_role_metadata_and_relocated_pins` |
| `r1_coverage.validate_binding`, `verify_union` | Unchanged; delegates launch validation, locates union pins by SHA rather than total list length. A separately requested legacy union still must satisfy its own order and launch order. | `test_union_checks_use_hash_positions_not_total_length`; validator tests. |
| `s1_pool.prepare`, `selected_rows` | Shared intake feeds both VQA and routing, so it postpones protected-role filtering until final stream materialization. Global lists still apply; receipt retains all role entries. | `test_shared_pool_preserves_rows_and_s1_routing_filters_only_routing` executes native constructor expressions. |
| `s1_routing._build` | Supplies routing context at final materialization. | Same constructor-expression test, plus native `Filters` and selection tests. |
| `s1_admission`, `r2_scene_bindings` | Unchanged; forward lists to the shared pool/stream builders and retain their reports. | Shared downstream predicate and receipt tests. |
| `launch_s1.build` | Preserves all non-path/SHA entry metadata during staging, including role and stream. | `test_launch_s1_preserves_role_stream_and_defects` executes the native config assignment. |
| `s1_pool_relocate`, `launch_r1.build`, `launch_r2.build.relocate` | Unchanged; preserve entry fields and project exact path/SHA pins for byte authentication. | Read-through audit; relocation preserves nested role metadata. |
| `r1_handover` | Unchanged; `remove_files` is an explicitly permitted handover delta. | Existing 24n handover tests. |

The fixtures use real pinned synthetic lists and SQLite rows. Room tests replace authority hash constants with hashes of synthetic authority files; `Rooms` parsing/count checks and the real withheld-80 bytes run natively. `tests/test_host24l4s.py` also substitutes the twin binding count and hash constants for a small complete fixture; the native Binding constructor, pin validation, strict/tiered resolver and census execute unchanged. Production naming bytes are stubbed only where unavailable, with separate wrong-byte and naming-content tests. Consumer-expression tests isolate production integration sites from unrelated model/archived-fixture setup; they do not establish a full production launch. The suite does not census the actual 320 pointing rows or production pose/routing stores.
