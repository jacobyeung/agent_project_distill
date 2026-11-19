# Cross-run preparation store — design, not an enabled feature

Patch 01 cannot avoid a rebuild in the production topology and must stay OFF. The builder maps a logical run to one node-local path. On that node, a complete journal already supports native reuse; on another node, the producer path is absent. A different logical run changes the current key and its seals. A shared index cannot repair those constraints.

Build a run-independent, content-addressed preparation store readable by every Orchard node. The store holds immutable prepared data, canonical receipts and frame manifests under their SHA256 identities. Nodes fetch verified objects into local scratch. A published root names the entire dependency graph; incomplete uploads never become roots. Keep telemetry outside the content identity. Storage ownership, publication rights, retention and atomic publication need an explicit operator contract.

## Native key and portable receipts

The native preparation computes the key over exactly the inputs it reads. Pass its config through a field recorder that refuses unkeyed fields, including nested access, `.get()`, membership tests and iteration. Record all conditional reads. Remove direct access to the original config. Route file reads through content pins and record their transitive dependencies; bind environment values, seeds, source code and runtime inputs that affect preparation through the same mechanism. Tests must introduce an unkeyed read and require refusal, rather than merely comparing a manually maintained list with itself.

A native planning pass computes the lookup key through the same dependency and branch logic. Execution receives the recorded view, refuses any new field or file dependency, and checks that its read set equals the keyed set. If native code cannot discover the exact dependencies before expensive work, take the cold path; do not substitute a hand-maintained key or silently broaden it.

Exclude `output`, `run_key` and `preparation_output` from preparation identity. The native preparation must not consult those fields when selecting or producing reusable content; the adopter assigns run destinations. Changing an excluded field must leave the portable content unchanged. Changing any consumed value, file content or code identity must change the key. The independent audit must verify this separation at every native reader.

Prepared receipts contain content identities and relative object names, without absolute run paths. SQLite inventories also need portable frame references. Canonical stores must exclude UUID directories, host names, timestamps and resource counters from content receipts; retain those as separate build telemetry. Resolve and verify every referenced object before use. Refuse traversal, symlinks, missing objects, partial graphs and changed bytes. Store membership alone never grants training authorization.

## Native adoption and checkpoint bindings

A native adopt step verifies a store root, materializes it into a private directory, and regenerates `request.json`, `config.json`, the source seal and `data_receipt.json` for the new run and configuration pin. It reconstructs phase markers and their output pins through native code. It must not copy another run's admission or assert that a foreign configuration passed review. Publication into the destination occurs only after verification. A miss preserves partial journals for native resume and foreign-config journals for native refusal.

Checkpoint bindings must remain valid across nodes. Bind immutable preparation content and the authorized run/config identity, and resolve portable content references through a node-local mapping. Verify the checkpoint's exact binding against the durable mirror and newest verified slot on both nodes. A new logical run requires a fresh adopted config and authorization; it cannot silently relabel an old checkpoint. Any migration of existing path-bound checkpoints needs a separately reviewed format transition. Keep full first-use checkpoint hashing and actual all-rank first-step admission.

## Build cost and acceptance

These are implementation-effort estimates in person-days, assuming one engineer familiar with the native readers. They include unit and integration tests. They exclude storage procurement, queue delays and a production training proof.

| Piece | Estimated effort | Build work and operating cost |
|---|---:|---|
| Shared content store | 1–2 days | Immutable object/root format, uploader, verified fetch, ownership and publication checks. Pays one upload and per-node fetch/verification; retention consumes durable storage. |
| Native key and field recorder | 2–4 days | Audit every config/environment/file reader, pin dependency closure, reject unkeyed fields, test conditional access and exclusions. Adds recording and initial input hashing. |
| Receipts without run paths | 2–3 days | Portable receipt graph, frame references and deterministic database serialization. Requires a versioned native reader and writer. |
| Native adoption | 2–3 days | Regenerate run/config/source bindings and admission receipts, verify before rename, preserve refusal/resume behavior. Pays local materialization and SHA verification. |
| Cross-node checkpoint bindings | 1–2 days | Portable preparation identity and resolver, mirror/slot checks, refusal of foreign or older state. Existing formats may increase this estimate. |
| Two-node determinism gate | 1–2 days | Independently cold-build the same pinned inputs on two nodes; compare canonical data and receipt digests, then adopt and restore across nodes. Budget two measured mode-p envelopes, about 4.7–4.8 node-hours before staging. Shared inputs must be staged once and distributed appropriately. |
| Independent admission review | 1–2 reviewer-days | Audit key completeness, portable receipts, native adoption, cross-node restore and refusal cases; bind the review to source/config artifacts before enabling. This implements the required independent admission review. |

Total estimate: 9–16 engineering days plus 1–2 reviewer-days. The two-node cold-build determinism check must fail on any unexplained content difference; do not normalize away differences after observing them. Require additional tests for corrupt/purged objects, every consumed key input, new unkeyed fields, partial/foreign destinations, interruption, concurrent adoption, and checkpoint restore on the second node. This design has not passed that admission review.

## Expected launch saving

Measured mode p costs **140.57 minutes** in job 172660 and **145.27 minutes** in job 171377. For a compatible store hit, saving equals that cold envelope minus fetch, full SHA verification, adoption and remaining frame work. A sizing estimate of **110–135 minutes saved per launch** assumes those combined costs take 10–30 minutes and required RGB is already present or included within that allowance. The allowance is an estimate, not a benchmark; cold frame transfer or slow storage can erase the saving. Measure object sizes and end-to-end adoption on both Orchard nodes before using a planning number. A miss saves no preparation time and adds lookup/key costs. Patch 01's estimated production saving remains zero or worse.
