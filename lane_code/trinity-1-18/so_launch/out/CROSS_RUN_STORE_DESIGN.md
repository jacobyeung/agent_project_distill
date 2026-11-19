# Cross-run preparation store — design for so_xstore

**Patch 01 stays OFF.** It cannot avoid native work in the production topology: the builder fixes one node-local run path, another node lacks its source, and a new run changes its key. The separate so_xstore build implements this design; this package does not implement or approve that store.

## Orchard transport and publication

Build a run-independent, content-addressed preparation store readable by every Orchard node through the existing GCS-to-cache channel. Today `launch_s1/b/c.sh:4,11–13` reads inputs fetched on the login node into `/project/community/jjyeung/distill/okit/in`; jobs stage verified copies into node-local scratch. Preserve `project_community_write_bytes == 0` in both staging gates (`b/g.py:110–113,134–137`). Jobs never publish directly into `/project/community`.

A producer archives objects and a candidate root on local scratch, then uploads through narrowly scoped GCS resumable sessions minted outside the job. Existing sessions are tied to milestone names (`b/c.sh:404–435`); they do not authorize a preparation root. Extend the external session issuer with reserved, bounded preparation-attempt object names and separate root-candidate sessions. The job gets no bucket-wide credential. A candidate contains object digests, sizes, native key and producer provenance; upload it after all payload parts finish.

An external publisher verifies the candidate and complete object graph in GCS, then publishes the immutable root under its digest. A login-node fetcher downloads that root and its archives, verifies every digest, and atomically exposes `/project/community/jjyeung/distill/okit/in/xstore/sha256/<root-digest>` read-only. Fetching and publication use operator credentials outside jobs. Consumers copy verified objects to local scratch and verify again before adoption. Conflicting roots, partial uploads and expired sessions refuse publication. Define ownership, quotas, retention, concurrency and orphan handling before implementation; a published root cannot refer to an evicted dependency.

## Native identity and portable content

Native preparation computes its key over exactly the inputs it reads. A field recorder rejects unkeyed access, including nested access, `.get()`, membership and iteration. Record conditional config, environment, seed, code/runtime and transitive file dependencies. A native planning pass discovers dependencies through the same branch logic; execution accepts only that recorded view and checks equality of read sets. Undiscoverable dependencies take the cold path. Tests introduce a new unkeyed read and require refusal.

Exclude `output`, `run_key` and `preparation_output` only after native readers separate destination assignment from reusable content. Changing excluded fields must preserve portable content; changing a consumed value or pin must change the key. The independent audit checks every reader.

Receipts use relative object names and content identities; frame inventories use portable logical references. Use content-derived phase directory names for both prepare and frames. `first_batch_progress.py:40` currently chooses `uuid4` names. Derive names from canonical input/phase identities before writing files, with a schema/domain separator and collision refusal. Keep host names, timestamps, resource counters and other telemetry outside canonical receipts. Specify deterministic SQLite construction and reject unexplained digest differences; do not normalize them away after inspection. Refuse symlinks, traversal, missing objects and changed bytes.

## Adoption, frames and checkpoint bindings

Native adoption verifies the complete graph, materializes a private directory and regenerates `request.json`, `config.json`, the source seal and `data_receipt.json` for the authorized run. It reconstructs phase markers through native code and verifies before rename. A MISS preserves partial or foreign journals for native reuse or refusal. Store membership grants no training authorization.

Frame work is node-local. The current inventory stores physical paths, `verify_frames` rechecks retained frames, and the request binds resolved roots plus `STUDENT_FRAME_ROOT_MAP` (`s1_admission.py:103–117,170–173,249–259`). Portable references require a verified local resolver and a local audit/adoption proof. Do not assume another node's frame phase can be reused cheaply.

The checkpoint binds the **derived config identity** and **preparation pin**, as well as code and world size (`carrier_c1_run.py:2920`). For one logical run, content-derived directories plus a verified byte-identical copy can preserve these exact bindings across nodes. Prove that config, preparation receipt and all path-bearing references remain identical. A different logical run needs fresh adoption and authorization; it cannot silently relabel an old checkpoint. A portable binding format or migration requires separate review. Retain full first-use checkpoint hashing, durable mirror/slot checks and actual all-rank first-step admission.

## Effort and acceptance

Estimates below assume one engineer familiar with the native readers; they include unit/integration tests and exclude queue delays, storage procurement and a production training proof.

| Piece | Estimated person-days | Required work |
|---|---:|---|
| GCS export and login-node cache | 3–5 | External session issuer, candidate/root publisher, verified fetch, immutable visibility, rights, retention and failure recovery. |
| Native key and field recorder | 2–4 | Audit all readers, discover exact dependencies, reject unkeyed reads and test conditional paths. |
| Portable receipts and phase names | 3–4 | Content-derived directories, portable frame references, canonical databases and versioned readers/writers. |
| Native adoption | 2–3 | Regenerate run seals, local frame verification, safe publication and partial/foreign-journal behavior. |
| Cross-node checkpoint identity | 2–4 | Prove derived-config/preparation equality, bind resolver and mirror/slot checks, review any migration. |
| Two-node determinism gate | 1–2 | Independent cold builds, canonical digest comparison, adopt and checkpoint restore on the second node. |
| Independent admission review | 1–2 reviewer-days | Audit identity, publication rights, zero-write staging, adoption and refusal cases. |

Total estimate: **13–22 engineering days plus 1–2 reviewer-days**. The two-node cold-build gate budgets about 4.7–4.8 node-hours for mode p before staging, inferred from the measured envelopes. Test corrupt/purged objects, partial uploads, revoked sessions, all consumed inputs, unkeyed reads, interrupted/concurrent adoption and cross-node restore. The store must pass independent admission review before enablement.

## Expected saving and required measurement

Planning number: **about 70 min, the prepare half, until measured**. This is an inference, before subtracting fetch, full SHA and adoption costs, not a measured net saving. Entire mode p measured **140.57** and **145.27** minutes in jobs 172660 and 171377. Prepare-to-result estimates are 70.37 and approximately 73.20 minutes; the remaining 70.20 and approximately 72.07 minutes are residual envelopes, not isolated frame measurements. If each node repeats the frame audit, only the prepare half is potentially saved. A miss adds lookup cost and saves no preparation time.

The adoption floor is **not measured**. On one Orchard node, time native mode p against a complete journal with both phases reused. Include full `pinned()` rehash, `run.prepared` and `verify_frames`; record wall time, bytes, root mapping and warm-cache state. This same-node floor excludes network fetch and cross-node remapping, which need separate measurements. Follow [MEASURE_NATIVE_REUSE.md](MEASURE_NATIVE_REUSE.md). This dispatch cannot execute it: only trinity-1-18 is authorized, SSH/Slurm are forbidden, and no complete production journal is staged here. Synthetic timing cannot substitute for this measurement.
