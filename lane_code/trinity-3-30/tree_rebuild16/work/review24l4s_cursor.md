# Short re-check (read-only, once) of TREE build 24l4s of lane tree_rebuild: your two SHOULD findings on 24l4r

You review; you do not fix. Different model family from the builder; legality code. Run once, read-only, on trinity-2-28. Report only verified problems with file:line and evidence. Final message is the verdict.

- Base: tree 24l4r `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1_24l4r` (seal 92fe11f8; your verdict `/scratch/jjyeung/orch_n30/tr16_rev24l4r/VERDICT.md`). Changed: `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1`, seal dd522bb92a7005e63130d40e9947258fda0c0196f533fb9d9677a1a0a7981781. In `../out/`: `HOST24L4S.patch`, `BUILD24L4S_REPORT.md`, `PROTECTED_ROOMS_API_24L4S.md`, `TREE24L4S_SEAL.json`, `UNCHANGED24L4S.json`. Prompt `../prompts/build24l4s.md`.
- Your MUST (native admission does not bind check_protected_rooms) is ruled a kit binding (census receipt pinned by h.py; re-verified by the in-job reviewer) and is not part of this tree change.

Verify: (1) only check_protected_rooms and the new tests differ from 24l4r; (2) SHOULD a fixed: a pointing row protected by any resolution (canonical_scene, Rooms.canonical/room on the other fields, withheld) refuses when admitted and counts as protected for list keys; your probe now refuses; (3) SHOULD b fixed: VQA uses the native VQA authority (Binding.room with tiered aliases) exactly as the tree's VQA census does, and still refuses rows it cannot resolve; (4) nothing else changed; (5) what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. nice -n 10, at most 8 threads, under 20 GB RAM; `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` for tests. Write the verdict to `VERDICT.md` in this folder only. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 15 lines.
