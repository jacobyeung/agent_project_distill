# build_rv_d0 result

`rv-proof` and `rv-read` accept staged D0 exports from lineage `8865619b`, run `359fcc3c`, at a positive optimizer step. They require complete stage-export evidence and matching artifact/checker identities. **329 CPU tests pass**, including 35 D0 tests and the 294 inherited tests. The pinned step-544 path retains its configuration and namespace behavior without an adapter overlay.

`TESTS_RV_D0_FULL_01.log` records 329 passed in 78.15 seconds with fresh basetemp `tests/d0_full_01`. System Python accepts the boundary CLI and parses all changed boundary modules. No model execution, GPU query/workload, production media decoding, SSH, network, Git, Slurm submission or deletion command ran.

## Adapter and receipts

D0 uses a single read-only file bind over `reader/official_adapter.py`. The wrapper authenticates the original adapter SHA, changes exactly four source snippets, records their literal old/new values and pins the generated overlay SHA. `DIFF.md` lists each substitution as **BEYOND**: the module's artifact hash, bind's checker step, bind's reader step and launch's checker step. The unchanged full export checker runs in bind and launch; completion also audits its `VERIFIED` result and the effective adapter code pin.

`ADAPTER_OVERLAY.json` retains the selected artifact/step, original and overlay SHAs, exact substitutions, stage receipt contents/hash, and checker evidence hashes. CONFIG and SANDBOX retain that overlay evidence. EXIT authenticates the overlay, its receipt, proof scope, admission, bound request and code pins. The wrapper verifies overlay bytes before entering each namespace, immediately before execution and after completion. The namespace entry checks the actual mounted SHA before entering the chain. Production requires an authenticated proof for the same artifact, staging evidence and deterministic overlay.

`D0_BUILD_CHECK.json` verifies that all **87 active payload files** and the payload pin manifest match build_rv. Of the inherited top-level Python modules and ReVSI entry points, only `rv_read.py` and `rv_entry.py` differ. `rv_d0.py` supplies the new admission/overlay boundary. The checker, processor, prompt, cohort, media, runtime, batching, scoring and llguidance files retain their bytes. The comparison implementation remains restricted to step-544 parity.

The tiny step-100 fixture produces overlay SHA256 `74b7ba9106121c6232a1b9a5e6763aaaeb37b4c33e106a0effc12e1f1cc50a92`. This identifies a **test fixture**, not a production D0 model. Each real staged export produces its own deterministic overlay SHA, recorded and checked in its packet.

## Proof scope

D0 reuses the kit's unchanged accepted 20-item prompt-byte/base-processor check. That check uses a dry step-544 reference bind and does not load its learned weights. C1 staging supplies tokenizer, processor and model metadata from the pinned base. The proof also retains the kit's 10-item synthetic generation/scoring exercise.

Every D0 packet includes `PROOF_SCOPE.json`. It distinguishes media/frame/prompt checks from selected-artifact validation, full-weight staging and metadata-dependent processor checks. Proof success establishes neither learned-token parity nor model accuracy nor real engine/GPU memory fit.

The untouched chain writes `AUTHORIZATION.json.step = 544`. That field remains a kit protocol label; the selected optimizer step is in `CONFIG.spec`, `ADAPTER_OVERLAY.json` and `a0/request.json.reader`. The proof-scope receipt explicitly records this limitation. The original adapter error message also retains the step-544 wording. No additional kit file is patched to change those labels.

## Validation

The tests create a tiny export through `stage-export` and run the unchanged checker with fixture-only filesystem mappings. They exercise the real overlaid adapter's model admission, bind and launch checker calls; model staging/execution stops at a test boundary. Separate wrapper fixtures exercise successful D0 proof/read packets and failed bound-identity or overlay audits.

Refusal tests cover wrong lineage/run/step/hash, missing or failed receipts, checker disagreement/source pins, artifact/ancestor/weight/receipt symlinks, and modified overlay bytes or receipt values. A real full-checker test rejects corrupted shard bytes. Tests also compare step-544 configuration bytes, namespace arguments and payload pins with build_rv, and reject a tampered completed D0 proof.

All edits and new evidence remain inside `build_rv_d0/`. The README includes the D0 operator sequence and receipt requirements. The documentation applies the no-archaeology skill; the requested source comparison and exact replacement descriptions belong in DIFF and validation evidence. No real D0 proof or production read has been run.
