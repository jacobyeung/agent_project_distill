Thu Nov 19 20:07:53 UTC 2026
VERDICT: DONE — round-10 fixes and delivery are complete.
147 workspace tests and 66 fresh-application tests pass. All 14 fail-before controls reran; all seven new tests fail before and pass after.
Pinned script preflight, exact boot bytes, one alias table, sealed-path existence, direct namespaced workers and one-pass archive hashing are verified on CPU fixtures.
Five patches apply with zero fuzz; original reader files and OFF output bytes remain unchanged. CPU ON equality passes; H100 byte equality remains required and unrun.
Supplied wrapper hashes/sizes match coordinator evidence; prior MANIFEST had no independent wrapper-member hashes. Exact supplied hashes are recorded and checked.
All 13 runtime parts plus bwrap remain pinned Orchard prerequisites. REPORT/NOTE include Review round 10 and exact test outputs. MANIFEST and FINAL_INTEGRITY seal the delivery. out_round10 bytes are unchanged.
Workspace after seal: 2,915,877,145 unique-inode bytes. An interim sample reached 3,041,057,187 bytes; byte-verified duplicate sharing restored the cap without removing paths.
No Git, SSH, SCP, Slurm, GPU, paid API, input edit or file-deletion command ran. Completed before 20:47:20 UTC.
