**SEALABLE AFTER FIXES**: no blocker and no behavioural regression. One small binding fix (G1) is needed before sealing; G2 to G4 are low.
Reviewed patch e0770534 applied to 3d2e5fa8 with `patch`: it reproduces the candidate byte for byte (carrier 42d11e3a, warm_start 1d4264b8, data_identity 6202378b, row_order ae95e5c2). The code allowlist equals the published JSON (2f6f98df). Below, `W`=s1_warm_start.py, `D`=s1_warm_data_identity.py, `R`=s1_row_order.py, `P`=carrier_c1_run.py.

## Items
1. **F1 to F4 are fixed, and each test is red on 3d2e5fa8 and green on the candidate.** F1: D:112-137 compares the effective preparation (camera with donor overrides) and all four stream receipts. Changes to camera, depth, model, division, supervision or an unknown field refuse. F2: P:926 and W:133 refuse a stray export key. F3: dryrun plans and steps at s+1 (P:1621-1633). F4: W:38-40 requires zero own-value probabilities. On 3d2e5fa8 the author's fix suite gives 10 failures and 1 error (run_test_review_fixes_UNFIXED.log).
2. **The allowlist is exhaustive, recursive and type-strict** (D:56-76). Keys must match at every depth, list lengths must match, `type() is` must agree (2 vs 2.0 refuses), and any unlisted leaf refuses. Allowlisted fields, and why none can change what is drawn, decoded or seen:
   - database, indices and pose order (path and SHA): the row gate covers them.
   - stream receipts (path and SHA): D:137 compares them field by field.
   - scene_source.* : s1_exclusions.verify re-derives the outer selection from them, and the census counts are compared strictly.
   - census population DB: consistent_pins requires it to equal the stream DB.
   - native_preparation, routing materialization, pool references: audit metadata. The trainer never reads them; native_preparation is written only at s1_admission.py:214.
   - path-only aliases (model, division, camera supervision, pose sources and receipts): the SHA must stay equal, and every reader verifies it (pinned, verify, binding). An alias therefore cannot point at other content.
   I ran D.check on the real mirrored donor preparation, config and three receipts against a simulated fresh admission. Every run-local pin was moved and given a new SHA, and the receipt was shaped as prepared() hands it over. It binds. Seven targeted mutations refuse (run_sim_production_check.log).
3. **Row-content gate: the producer and consumer kernels are identical.** Both use the same canonical(), sort_keys and separators, allow_nan=False, an 8-byte length prefix, stream order from the receipt, and pose (source, index) pairs with the indices map. The scanner refuses duplicate keys and NaN; the consumer fails closed on these. On a four-stream fixture with a two-source pose mix and a VQA index map, the scanner hash equals R.fingerprint. Rebuilt DBs with another page size and reverse insert order, and reformatted index and order files, pass with the attestation and refuse without it. One changed character (target or row), swapped rows, a missing row, a changed index map or pose order, and a reordered stream list all refuse. An attestation naming another config or preparation, or with a tampered digest, also refuses. The attestation is bound to the donor's config and preparation pins (R:89) but not to the scanner's source hash: see G1.
4. **The byte gate is still the default** (W:114-121). With identical bytes and moved receipts, it binds as native-file-pins-v1. It refuses rebuilt bytes when no attestation is pinned.
5. **No regression.** I re-ran round 1's three tests, with the receipt's init_artifact set equal to the config's as P:669 does:
   - s=200 and s=650: the first step is s+1, the LR equals an independent statement of the sealed schedule at s+1, and the plan and qids equal the original plan at index s;
   - F1 and F2 now refuse.
   Fresh AdamW, strict loading and the default branch tests pass. Without warm_start, dryrun and the loader make the sealed calls (initial=0; require_all_heads is not passed).
6. **Identity.** The run key comes from digest(policy, choice), and the choice includes donor_row_order. Three choices give three keys (87348220, 21b29e54, a0d44a5b), and the output, preparation and persistent roots derive from them. The collision check with 469ddece/5da50f2b is kept, and bad or extra pins refuse.

## Findings (by severity, smallest fix)
- **G1 (medium, fix before seal). Scanner provenance is not bound.** accept_scan.py keeps only {schema, config, preparation, rows}, and R.verify (R:86-93) cannot tell who produced the rows digest. My test test_limit_attestation_does_not_carry_scanner_provenance builds an envelope from the NEW admission, with a changed target, wrapped in the donor pins, and it binds. Fix: keep `scanner.source_sha256` in the envelope. Have verify require it to equal the bundle's scan_donor_rows.py (5c1f4408...), and record it in the lineage.
- **G2 (low). The author's earlier suites are stale against the candidate.** test_warm_start gives 14/20 and test_review_fixes 3/8. Each failure has one of two causes:
   - a fixture that prepared() would refuse first (the receipt's init_artifact differs from the config's, or the stream pins differ between config and receipt);
   - a refusal that now comes from an earlier gate, with a different message.
   Adapted versions pass. Fix: update those fixtures and messages so every suite is green on the sealed candidate.
- **G3 (low, fail-closed usability).** R:89 compares the config and preparation pins with their paths. The scanner records the donor's logical `/inputs/` path, while the template's placeholder names a mirrored path. If they differ, a launch refuses. Fix: pin warm_start.donor_config at the scanner's logical path, or compare only the SHA-256.
- **G4 (low).** canonical() sorts keys, so row key order is not bound; test_limit_row_key_order_is_not_bound shows this. It is benign while no encoder depends on dict order and the row builders are unchanged. Document it, or hash with key order preserved.
- **Note.** R:32 hashes every DB again on rank 0 at each launch: about 7.8 GB plus 387k lookups, roughly 4-5 min at the scanner benchmark. This fits inside the 60-min startup group (P:2738), but it is charged to the 24-h leg.

## Ran (CPU, private copies in work_warm_start_2/, verified hashes)
- Author guarded suite: 8/8 OK.
- Author original suite: 14/20; the 6 failures are stale fixtures (G2).
- Author fix suite: 3/8 on the candidate (G2) and red on 3d2e5fa8, as required.
- Round-1 original tests: 0/3 unchanged, because their fixtures are inconsistent.
- My test_reviewer_round2.py: 17/17 OK. It holds the adapted round-1 tests, 13 row-gate tests that run the real bundle scanner and accept_scan, and the author's inherited-metadata test with a consistent receipt.
- sim_production_check.py: passes on the real schema, and its 7 mutations refuse.

## Not checked; the first GPU steps must check
- Not checked: whether a real fresh admission reproduces the donor's ordered row content (if not, both gates refuse and the contingency is unusable; run the scanner on the donor and R.fingerprint on a trial admission before the donor is lost); the real export layout and mirror; frame files on disk, which neither gate binds unless rows pin them; FSDP, BF16 at scale, memory.
- The first GPU steps must show: step label s+1 with the LR logged at schedule(s+1); first-step qids equal to the dryrun's ranks at s+1; init_report with unselected=[], kept=[], planned_init=[] and the full head count; per-stream losses near the donor's at s, with no cold jump; clip and gradient norms over the first ~20 steps.
