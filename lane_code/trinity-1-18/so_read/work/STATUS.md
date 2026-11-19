Thu Nov 19 17:52:26 UTC 2026
VERDICT: DONE — round-8 fixes and delivery are complete.
All five findings are fixed. The archive preserves admitted symlinks, rejects escaping/broken/cyclic links and retains stderr.
The GPU interpreter/cache/preflight contract is explicit; CPU READY, gate, workers, ue.json and submit bind environment versions and SHA256.
The builder admits only step 400 before reading base inputs; no alternate-export gate parameter remains. Archive-path aliases resolve on both sides.
129 workspace tests and 48 fresh-application tests pass. All 12 retained failure controls reran; the ten round-8 tests produce 29 expected assertion failures before fixes.
Five diffs apply with zero fuzz; original reader bytes and OFF output bytes are unchanged. ON CPU answers/traces remain exact.
Archive/real-loader admission, CPU operator path, synthetic gate/submit integration, source probes, benchmark/profile and documentation checks pass.
Workspace size after seal: 2,940,997,394 unique-inode bytes. out_round8 and the reviewed source snapshot retain their original hashes.
No GPU, Git, SSH, scheduler operation, paid API, input-tree edit or deletion command ran. Production GPU parity/performance/memory and host interpreter/restore remain unrun.
Completed before 18:30:31 UTC. FINAL_INTEGRITY.json seals the delivery.
