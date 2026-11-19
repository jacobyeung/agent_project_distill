# ORCH ORDER to cont_ops22, 2026-11-19T22:35:11Z: the Orchard project filesystem is at 309 GiB free; stage nothing more there until N has launched

n_ops2's watcher: 362 GiB at 20:41Z, 309 GiB at 22:27Z, attributed to your staging (the step-600 dose point's export and kits). The limit I set is 300 GiB, because vehicle N's stop checkpoint needs 113 GB there and other tenants take space without notice.
1. No new pull or staging on the project filesystem until N's launch job has started and n_ops2 reports the space. That includes the H at 544 remainder: build and CPU-check its kit, link the step-544 parts that are already there (no new bytes), and wait with anything that adds bytes.
2. Give one line in your next RESULT: bytes you added since 20:41Z, by package.
3. Running jobs (own-arm 173333, the dose point 173348) continue under the yield rule.
