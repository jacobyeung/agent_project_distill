# ORCH ORDER (2026-11-21T09:12Z; to n_ops10; copy tree_rebuild27, n_review1i): /project at 21 GiB free; measure, say what N still writes there, and list what the user could free

The danger before the stop checkpoint is the gate: if /project fills before about 11:15Z, the gate files (X/o/174101_gate), the fallback copy and the install of review.json cannot be written, and the job times out at the gate after 120 minutes without a training step.

1. Measure, in one niced pass over our own okh7 only: bytes per top-level folder, largest first. From the watch's history give the free space every 10 minutes since 06:00Z, so the rate is known. State whether our own writes moved it (N's job writes less than 20 MB there by design; lever4 at most 50 MB).
2. Write a list for the user, B/events/n_ops/ORCHARD_REMOVAL_CANDIDATES_20261121.md: each folder or file of ours on /project that no running or planned job reads (outputs of ended discovery, evidence and test jobs, superseded kits that are already archived elsewhere, old pools), with its size, what it is, and what would be lost without it. No agent removes or shrinks anything on /project; the user decides and runs it. Post the RESULT with the total that the list would free.
3. Say in one line each what N still writes to /project from now to its end and what happens to each write at 0 bytes free: logs, live mirror, gate copy, review install, upload bookkeeping, and the stop checkpoint's fallback (it needs its size plus 50 GiB, so it is not available now; GCS is the only route).
4. The watch keeps its flag; make it raise a new BLOCKER at 10 GiB and at 5 GiB.
5. If free space is under 8 GiB at any reading before the gate has passed, post a BLOCKER at once with the list's top entries, so that I can ask the user to free space in time.
