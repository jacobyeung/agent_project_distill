Cprime is built for independent review. Config `774503e26f274a10c96ad06210d339c49ebc9a704ac254df81f389b0da4d98a1`; run `6ed2c7aa`; job `a15_cot_ap6ed2c7aa`; bundle `/project/community/jjyeung/okh7/i_ee227714`; kit `/project/community/jjyeung/okh7/x_ee227714`.

Archive `p_32337655.tar`, SHA256 `3233765535fc95eb34b876b2e96895b5f684bd8b4e6c5c93f9e23123d320317b`. Verify DRIVER_SHA256SUMS.txt before use. The names are fresh; m1 is unnecessary unless the operator finds a collision. No proof or rehearsal driver is provided.

| Order | Driver or local builder | Expected output or condition |
|---|---|---|
| 1 | u1.sh | Fresh private bundle; authenticated archive uploaded and unpacked; PASS outer SHA, 43 members, exact sums.txt inventory, files 0600 |
| 2 | q1.sh | PASS native selection and bound-unit regeneration |
| 3 | review_build.py --cprime PATH, then rv1.sh | Twelve-review chain: eleven pinned C4 antecedents plus events/review_cprime/REVIEW_VERDICT_CPRIME.md; READY rv1.sh, then PASS installed chain |
| 4 | ev1.sh, then evp1.sh | STARTED e0; then e0 rc=0; both REMOVE additions and final identity bound |
| 5 | dv1.sh, then dvp1.sh | STARTED d0; then d0 rc=0, READY evidence, exact p/t/u authority and code directories 0500 |
| 6 | scan1.sh | Exact packet/config/manifest inventory for independent whole-kit content classification; B1r itself has zero content deny hits |
| 7 | cert_build.py, then sc1.sh | Packet-specific independent CLEAN certificate accepted and installed |
| 8 | L1_mint.sh on trinity-3-30 | PASS 20 fresh create-only sessions, packet-specific filenames, mode 0600; URI contents withheld |
| 9 | session_build.py, then si1.sh | READY si1.sh; exact 20 export destinations installed privately |
| 10 | pre1.sh | PASS REAL A resume pointer; verified step-200 slot archive, manifest, binding and shards; Cprime rebind policy verified |
| 11 | go_submit_canary_delta_32337655.sh <GO_SHA> | Pinned GO and admission 172180 accepted; one advanced four-GPU, 24-hour submission; training.job.id recorded |
| 12 | mon.sh | Read-only queue/accounting and bounded redacted logs |

The required GO SHA is `1f3dff81041a58c45966e83535ec50182a616de94d036fcfcfa5142141862b7e`. No PROOF_JOB is needed. The new review must explicitly state Packet Cprime: GO (or GO AFTER FIXES with only LOW nonblocking fixes) and name the full config identity or archive SHA. The reviewer hashes bind the original review bytes. rv1/sc1/si1 exit 4 until their independent inputs arrive; no review, certificate or session is fabricated.

The mint helper is present and verified at `/scratch/jjyeung/orch_n30/cont_ops/work/d0/jobB/mint.py`, SHA256 `b7388f557f941ccd0e3c2d82bf3ade0e1ad34e8a96e5f995d35dcefef79cf57d`. L1_mint.sh is a local Trinity step; the other shell drivers target Orchard. Use each local builder's --help for its required independent inputs. Recompute the checksum manifest after an approved builder replaces a pending script.

Local validation: 17 delta/removal tests and five driver tests pass; 50 legacy tests pass and 62 cannot run because recovered inputs are missing. Census, 1,000-step VQA audit, deterministic reseal, D0 equivalence and four-rank first batch pass. Local H1 derivation cannot run without pinned k/s1_record.json. See `/scratch/jjyeung/orch_n30/r1_pkt/out/CPRIME.md` and its missing-input ledger; production derivation and admission remain mandatory.

u1.sh includes the archive transfer and extraction. u3.sh is the extraction helper embedded into u1; do not run it again after u1 succeeds. Poll at most once a minute. Stop after any failed or uncertain operation and preserve attempt markers; do not retry automatically. The private pool mapping stays on Trinity and is never uploaded.
