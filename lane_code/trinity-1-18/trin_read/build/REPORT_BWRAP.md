proof, read, need, and selfcheck accept --bwrap PATH, default /usr/bin/bwrap; the pinned Orchard binary never executes.
COMMAND.json/EXIT.json/PROOF.json and CPU/selfcheck evidence record the executed path, SHA256, and exact --version output.
Executed host: /usr/bin/bwrap, bubblewrap 0.4.0; SHA256 e60f175f82b2d6779a543ba52152f636f6260d092e44b195713f7650fb7bed76.
Every emitted flag is listed by 0.4.0 and included in the CPU true probe; no substitutions were needed (BWRAP_FLAGS.json).
Tests: 76 passed in 9.24 s; see TESTS_BWRAP_FINAL.log. DIFF.md marks selection PATH/ENV and evidence/classification BEYOND.
Real-root selfcheck exited 2: CONFIG passed with 153 pinned_evidence findings and eight root-backed aliases; integrity checks passed.
Missing: base, reader_payload, runtime_0, runtime_1, runtime_2; a0 lacks its member inventory (SELF_CHECK_BWRAP.json).
The probe exited 1: bwrap: loopback: Failed to create NETLINK_ROUTE socket: Operation not permitted. This sandbox blocks namespace execution.
STAGING/pinned files are unchanged; root/trinity_runner is updated. No tar wait, staging, kit edit, SSH, network access, Git, or GPU work ran.
