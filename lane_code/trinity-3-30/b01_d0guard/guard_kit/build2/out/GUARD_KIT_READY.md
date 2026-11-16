# Guard-read kit: G3 sealed; production NOT READY

The package passes integrity verification and all 134 tests (`FINAL_AUDIT.json`, `TESTS.json`). All 25/25 report mutants are detected (`MUTANTS.json`). Packet tests bind the refreshed family and code pins (`PACKET_TEST.json`, `ALL_STEPS_TEST.json`). Production launch remains blocked by naming, independent review and milestone authority (`RELEASE_BLOCKERS.json`, `FAMILY.json`).

The native merge compares per-key canonical-JSON digests, so tuple/list representations with equal contents admit. A changed score refuses and writes `MERGE_DIFF.json`; missing keys refuse. Matching rows still undergo the request, denominator, parity, score and geometry checks. The merge uses the journal rows after comparison (`guard_kit/admission.py:14`, `G2_TESTS.json`).

The code tar retains the original production member inventory. Only `admission.py` changes; rehearsal-only mount splitting, torchvision and argument forwarding, plus operator backup files, stay outside the tar (`G3_SEAL.json`, `CODE_MANIFEST.json`). The input archive, inherited backend, reviewed stager and report retain their hashes (`INPUT_MANIFEST.json`, `SOURCE_IDENTITY.json`, `FINAL_AUDIT.json`).

The whole-worker blocker is CLOSED for the CPU fixture on operator-supplied evidence: `rehearsal/whole/31f44f39c63b4d68be53660ff5780980/RESULT.json`. The proof passes 20/20; the report correctly refuses the 20-item fixture with return code 3 (`rehearsal/OPERATOR_EVIDENCE_G3.json`). G3 neither accesses that protected directory nor reruns the namespace worker. The fixture cannot establish real tensors, GPU parity or token identity. Production cloud staging and allocation remain unvalidated (`rehearsal/RUNBOOK.md`).

The real candidate metadata passes config identity, preparation, source seals, initialization-chain and unchanged restoration checks (`CLOSURE_ADMISSION.json`, `RESTORATION_TEST.json`). Those metadata results do not establish actual candidate tensor restoration.

Runtime naming remains blocked as written in `RELEASE_BLOCKERS.json`. The seven names sit inside the sealed trainer tree b01ce449, the same tree job 170056 and D0's training job already staged on Orchard; ORCH decides (`NAMING_CONFLICT.json`; operator context in `RELEASE_BLOCKERS.json`). The neutral outer archive round-trips to identical file bytes, but runtime projections remain unintegrated (`NAME_ROUNDTRIP.json`, `NAMING.json`).

| Artifact | SHA256 | Evidence |
|---|---|---|
| `code_g2.tar` | `9ffa724919aa52adf94793a5f0a6912d867797d8aa55a179d2366282bc695bdc` | `CODE_MANIFEST.json` |
| `inputs_g2.tar` | `3be24165b9856024dc5359b1760a8a1ad88f11022972fb3d075edb70c02aff72` | `INPUT_MANIFEST.json` |
| `FAMILY.json` | `273d5d5661fc7fea166aa6603411c1db8e23c7a8e9bc8b7ae8f8c1044737029b` | `FINAL_AUDIT.json` |
| `candidate_m50/metadata.tar` | `d04e294d2cf2908fef45208280f9bc7313b0a54ae0b71d0be1403358a9cde443` | `candidate_m50/CLOSURE.json` |
| Unchanged report | `6fead56128b2081314e52aa0ca6a7ab2f077aac72078554f2d1d7b61067aacc6` | `FINAL_AUDIT.json` |

Reproduce this seal from the build directory with `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B`: run `work/family.py`, `work/run_g3_tests.py`, `work/seal.py --g3`, `work/g3_docs.py`, then `work/finish.py --g3`, under `nice -n 10` with numerical-library threads set to one. The operator rehearsal command and overlay are in `rehearsal/RUNBOOK.md`.

`DIFF.md` gives current admission line ranges; `G3_ADMISSION.patch` isolates the merge change. `PIN_CLASSIFICATION.md` covers the contract checks. `RUN.md` gives production preparation and authority commands. Remote commands remain unexecuted.

Not checked: real tensors, GPU parity, token identity, production Orchard/GCS/pool/credentials, the namespace proof-mismatch variant, and complete runtime naming. Local size excluding protected operator runs is in `BUILD_SIZE_G3.json`; G3 timing is in `../work/TIMING_G3.json`.
