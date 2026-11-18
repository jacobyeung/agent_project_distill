The packet adds a native selection regeneration tool and rejects new selection pins without their equality reports. The trainer, production selection, recipe and config identity remain unchanged; this packet is BLOCKED until production regeneration succeeds.

- `tools/selection_check.py` and `build/q.sh` regenerate from authenticated catalog inputs, compare raw and D0-projected receipts, and verify ordered index files. The standalone script is offline and below 1 MB.
- `tools/selection_guard.py`, `tools/make_deriver.py`, `tools/derive_kit_h1.py` and `payload/d.py` bind the candidate, reference, code, tool, input inventory and report. The generator uses the retained local base in evidence/fix7_before, so rebuilding needs no external source checkout.
- `tests/test_fix7_selection.py`, `tests/test_fix7_deriver.py`, `tests/test_fix7_admission.py` and `tests/test_fix7_package.py` cover regeneration, missing/invalid proofs, the complete fixture deriver, downstream native routing and transport integrity.
- `REPORT.md` and `FIX7.md` state the production blocker, exact inputs, downstream limits and operator sequence. `evidence/fix7_selection/` and `evidence/fix7_admission/` retain all audit output, including failed fixture-development attempts.
- `payload/sums.txt`, `UPLOAD.json`, transport scripts and build/c_patch.sh bind the hardened deriver. The patch remains a blocked inspection patch for the recorded live round-5 state; it is not an equality-bound deployment patch.

Current changed-member hashes are in evidence/fix7_patch_manifest.json. Full deliverable hashes are in evidence/fix7_selection/delivery.json and SHA256SUMS.txt. The original round-6 report and deriver are retained in evidence/fix7_before.
