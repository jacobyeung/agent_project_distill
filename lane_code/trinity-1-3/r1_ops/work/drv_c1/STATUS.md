BUILT_AND_LOCALLY_VALIDATED — r1_drvc3, continuation C fix round 4.

Archive: p_08f3a7b2.tar
SHA256: 08f3a7b2ef2e1923ba77b464afcedbbe668a77a1915b4c32c0a815044ff7d9fd
Config: 6594f46cdc16168514aca26a6ce38285907adfc6ece0b75d8e10428ea0b2fe74
Run/job: 05b8ac69 / a15_cot_ap05b8ac69.
Bundle/kit: /project/community/jjyeung/okh7/i_7f1589c1 and x_7f1589c1.

m1.sh preserves FAILED proof 172180's bundle and kit as *.f172180. It refuses queued 172180 or any same-name job, checks old packet bytes, and preflights both targets. Its same-filesystem no-replace move includes the requested EINVAL fallback after a fresh absence check. Old sessions remain in the moved kit. Minting uses fresh packet-specific local filenames and creates 20 new sessions.

All active drivers pin CONT4. The review builder requires eleven verdicts, with review_r1c3/REVIEW_VERDICT_R1C3.md final and r1p–r1p8, r1c1, r1c2 antecedent. The real final review grants GO for the exact archive; rv1.sh is ready and REVIEW_CHAIN_C3.json records its eleven authenticated review hashes. sc1.sh and si1.sh remain PENDING for the new certificate and sessions. Preserved local ANON_OK.json and session artifacts belong to the deployed old packet and must not be reused.

rh1.sh uses the exact CONT4 zero-GPU general rehearsal command and a separate one-shot ledger. rhf.sh accepts only REHEARSAL_OK/FAIL terminal receipts. pr1/pr2 default to general, reject bootstrap, support --hold, and require REHEARSAL_OK before submission. Their history guard permits only FAILED 172180 plus the rejected bootstrap's no-ID records in the moved bundle. Training history allows only the new proof and FAILED 172180.

go_submit_canary_08f3a7b2.sh pins ruling SHA 31f5e70ca014a370913115e124290805744e5947790e8d2463e5b0225130aa89, admission 172180, and the moved admission kit. It requires the new proof PENDING/RUNNING on general, accepts held PENDING, rejects queued rehearsals/duplicates, and verifies A has released advanced and has a verified integer step-200 slot record. The sealed gate authenticates admission evidence. go_submit_08f3a7b2.sh provides the completed-PASS route. Both share one-shot training markers.

pre1.sh reads the real A archive once without extraction or tensor deserialization. It authenticates the A binding, complete manifest, four-rank checkpoint payloads, and C's sealed resume policy. It compares C's pinned admission log counts and retained preparation with A's archived preparation, reporting equal/different per stream and family. C's prepared inputs must be login-visible; the original node-local path may be unavailable there. Missing receipts refuse. README.md names the exact original path and optional preserved-input argument.

VALIDATION_C3.json records 18 local validation logs and 136 PASS lines. Coverage includes review/installer checks, general/held proof guards, 33 authority mutations per checker and top-level import-shadow refusal, sealed proof binding, scan, REMOVE and switches, mocked fresh minting, read-only monitors, PASS/canary scheduler history, no-replace/EINVAL moves, rehearsal argv/receipts/one-shot ledger, and synthetic slot/family verification. The existing local READY fixture supplied unchanged derivation bytes; only p_05b8ac69.sh, s.sh and sums.txt differ in the packet. Tests do not attest real Orchard populations, donor state, or production approval.

The operator sequence begins with m1.sh and is complete in README.md. Respect the ruling's general-slot order and kill conditions. No remote operation, Git command, GPU use, live mint, submission, deletion, job stop, outside-workspace write, or mirror transfer occurred. All local Python used /scratch/jjyeung/envs/p1cpu/bin/python. LANE_RULES.md was read at its specified path. The user restricted this build to drv_c1, so the RESULT handoff remains local.
