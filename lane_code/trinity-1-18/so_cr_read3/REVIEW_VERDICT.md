VERDICT: GO AFTER FIXES

Scope: `so_read/out/` (REPORT, NOTE, patches 01–03, MANIFEST, kit_parity50, checks) and `so_read/work/src/u0` (a0–a18, tests), against base `.../A4/src` and returns `.../A4/ret`, `.../B5/ret`. Paths below are relative to `so_read/work/src/u0/` unless stated; `A4/` is `.../c15/r1route/out3/A4/`.

Method: I read the code myself and ran only in-memory, read-only checks (`nice -n 10`, `-I -s -B`, CPU only). I did not run the builder's suites, because they write to `so_read/work/test-artifacts`. For fail-before and pass-after I rely on the recorded outputs in `out/checks/`.

The OFF path is safe: the patches only add files. No HIGH finding. ON adoption at step 600 needs findings 1 and 2 fixed, plus the GPU kit gates that the NOTE already requires.

## Round-1 findings (Codex)

| # | Fix correct and complete? | Fails before / passes after |
|---|---|---|
| 1 Key collision | Yes. The digest is typed and length-prefixed (a0.py:35-87). | Yes (round1_before.txt:11; round1.txt). |
| 2 Vacuous parity | Yes. Requires exactly the 50 ids, validates the schema of every row, and requires hits above zero for every enabled cache plus a memory receipt (a10.py:15-63, 117-166). | Yes (:19). |
| 3 OFF contract | Yes. The patches add only `u0/*`. All 927 base files match the MANIFEST pins, which I checked. | Yes (:28). The test is structural. |
| 4 Model identity | Correct, but the live content hash runs on every call (finding 1). | Yes (:36). |
| 5 Recovery outside lock | Yes. Recovery runs under the flock only (a4.py:146-170), and the deadline handler no longer repairs (a4.py:420-424). | Partly. The test is textual (tests/test_round1.py:75-78). The behavioural `test_deadline_recovery_keeps_writer_lock` loads only in after-mode (test_round1.py:107-116), so it was never shown failing on the pre-fix code (finding 4). |
| 6 Opacity | Yes for names and roots (a9.py:13-41, 185-192). | Yes (:52). |
| 7 Memory bound | Yes. Admission and eviction happen before the snapshot, with bookkeeping counted (a0.py:221-265). | Yes, both tests (:71, :79). |

## Round-2 findings (Cursor 1–10, 16)

- 1: fixed. `-I` import path at a8.py:54, with a real subprocess test.
- 2: fixed. Established prefixes plus the FORBIDDEN screen (a9.py:13).
- 3: fixed. argv comes from production `submit_argv`, the shell retry is tested with a fake scheduler, and `approved=false` stays.
- 4: partly fixed. The generic job path is fixed; the operator path that actually ran A4/B5 is not covered (finding 2).
- 5: partly fixed. The SAM cap is 12 GiB, but the hashing cost remains (finding 1).
- 6–10: fixed, with behavioural tests.
- 16: fixed (kit run.py:54). The test is textual.
- All 13 round-2 tests failed before (round2_before.txt:179-181) and pass after.

## Findings

1. **MEDIUM: the vision and SAM caches hash every weight on every call, so ON probably costs more time than it saves.**
   - Evidence: `module_identity` hashes every parameter and buffer on each call (a0.py:327-329). It runs on each vision forward (a0.py:361) and each SAM detect (a3.py:223).
   - GPU tensors are hashed in 64 KiB device-to-host chunks, one sync per chunk (a0.py:50-54).
   - Measured `digest` throughput for CPU-resident bf16 is 1.58 GB/s. GPU-resident weights add a sync for every 64 KiB.
   - Distance items average about 1.8 SAM calls each (profile.json: ground 176 plus gap 88 over 150 items), so expect seconds per item against 23.6 s per item. The NOTE already credits no saving.
   - Smallest fix: hash the weights once at install and again at each type-journal boundary. Fail the run, not just the cache lookup, on a mismatch. Per call, check only (id, data_ptr, `_version`).
   - Alternative fix: adopt only the processor cache, whose key hashes frames and is cheap, and keep the vision and SAM caches off until a GPU profile shows a net gain.

2. **MEDIUM: the production integration targets the generic `orchard_h10` job path, not the operator bootstrap that produced A4/B5.**
   - Evidence: the hex bundle in `A4/package/BATCH.sh` decodes to a `0.py` whose `make_dispatch` reroutes action 1 to a bundled `7.py`, which is `A4/tower_sequence.py`. That `0.py` also requires a CPU proof with `bundle_guard_passed`, `entry_sequence_passed` and memory basis `fixed_g3t_shapes`.
   - The returns use the layout `metadata/reads/0/...`, and `A4/unpack_return.py:54` binds `operator_sha256`.
   - `tower_sequence.py:82` refuses more than one card, so the 2-shard and 4-shard forecasts cannot run through this operator.
   - `tower_sequence.py:101-114` sets `sam_memo_bytes=0`, which leaves the 12 GiB read cache out of the memory proof.
   - a12.py:59-60 puts a17 in as `runner.py`, and the flags pass through `**config` (tower_sequence.py:37-41). So this path probably works, but no test, REPORT, NOTE or README mentions it.
   - Smallest fix: add a CPU test that builds an ON payload with a12 and runs A4's `0.py` and `7.py` through actions 0 and 1 with stub workers. It should assert that the overlays are active and that the merge lands under `reads/0/metadata/u0`. Then add `read_cache_bytes` to the operator memory bound, and give a multi-card operator for sharding.
   - Alternative fix: state in the NOTE that step 600 must use a12's bootstrap, and update fetch and unpack for its layout.

3. **LOW: the kit does not authenticate the base source.**
   - Evidence: `validate_roots` (kit run.py:34-46) pins only `u0/*` and checks that the two roots differ. It never checks either root's non-u0 files against MANIFEST `base_pin.inventory` (927 files).
   - Consequence: if both roots point at the same wrong base, ORIGINAL, OFF and ON all agree and the gate passes on the wrong reader.
   - Smallest fix: before any arm, hash both roots' non-u0 inventories against `base_pin`.

4. **LOW: some regression tests are weak.**
   - Evidence: round-1 F5 and round-2 F16 are string checks (test_round1.py:75-78; test_round2.py:300-303). The behavioural lock test is added only when not BEFORE (test_round1.py:107-116).
   - Smallest fix: run `test_deadline_recovery_keeps_writer_lock` against the round-1-before a4 and record the failure.

5. **INFO: Orchard-visible content under token roots.**
   - Evidence: the opacity checks screen path roots and segments only (a9.py:19-41).
   - The staged source tree keeps descriptive subdirectories under the token root.
   - Without `--public`, kit journals hold raw item ids (`vsi590k_…`, `devs1cam-…`) and audit paths (`…/sam3.pt`).
   - Production keeps these inside the tar and extracts it node-locally.
   - Fix: stage the source as an archive, extract it on node-local disk, and always run with `--public`, as README:22-28 describes.

6. **INFO: the array path is not production-staged.**
   - Evidence: a14 and a7 bypass production staging, restore and the namespace. Inputs must exist on every requeue node.
   - Real requeue is untested (README:75), and approval stays false.
   - Nothing blocks, because no launch is authorised.

7. **INFO: the OFF import guard does not list the round-2 files.**
   - Evidence: `RefuseExtensions` covers a0–a10 only (tests/test_off.py:20-36), not a11–a18.
   - The risk is nil, because the original files are byte-identical and import no u0.

8. **INFO: the six checks.**
   - (1) OFF: holds. The patches add only new files. The added files I reconstructed from the diffs equal `work/src`. Settings, imports and timing fields are untouched; only a18 writes `read_*` keys, and only in ON packages.
   - (2) Cache keys: hold. Keys cover pixels, indices, metadata, kwargs, weights, dtype, device, autocast and execution state (a0.py:296-307). Hooks force a bypass (a0.py:333-340). Snapshots go to CPU (a0.py:90-111). The cache resets on a PID change. Nothing question- or state-dependent is cached, only processor output, the visual forward and SAM features and detections. SAM caching is refused when the `sam3` memo is on (a1.py:198-200). The cost problem is finding 1.
   - (3) Journal and shards: hold on CPU. Commits use temp file, fsync, `os.replace` and a directory fsync (a5.py:29-43); `recover` is at a5.py:67 and the whole-scene assignment at :98. The merge rejects duplicate, missing and extra ids (a6.py:44, 84, 91), and the tgz is deterministic with mtime 0 (a6.py:103-106).
   - (4) Parity kit: holds. Every field except telemetry must be byte-equal (DROP at a10.py:11). It requires the 50 ids, valid per-row schemas and positive hits. In the sample, all 50 items fall into 12 scene-and-frame groups, so hits are reachable.
   - (5) Forecast: correct. 580 × 23.599762 = 13687.86 s, plus 125.21 s, gives 13813.07 s (3 h 50 min), 6969.14 s (1 h 56 min) and 3547.17 s (59 min). Ten long reads carry 1308.7 s of the 3540 s distance total, so balancing shards by item count can be uneven; the NOTE excludes imbalance.
   - (6) Opacity: holds. Names are `a15_cot_ap` plus a token, roots are tokens, and the public wire is hashed. See finding 5.

9. **INFO: integrity.** The hashes of the patches, MANIFEST, REPORT and NOTE match `checks/FINAL_INTEGRITY.json`. The kit files match the MANIFEST, and the B5 archive hash matches.
