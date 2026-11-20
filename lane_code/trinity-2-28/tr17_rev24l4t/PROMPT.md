# Short re-check (read-only, once) of TREE build 24l4t of lane tree_rebuild: your MUST on 24l4s

You review; you do not fix. Different model family from the builder; legality code. Run once, read-only, on trinity-2-28. Report only verified problems with file:line and evidence. Final message is the verdict.

- Base: tree 24l4s `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1_24l4s` (seal dd522bb9; your verdict `/scratch/jjyeung/orch_n30/tr16_rev24l4s/VERDICT.md`); 24l4r at `../work/tree_r1_24l4r` (seal 92fe11f8). Changed: `/scratch/jjyeung/orch_n30/tree_rebuild15_w24l/work/tree_r1`, seal c558ad33286680e17c45ec54c825a9f236e80fd789f4ce6b0189273cd63fc16c. In `../out/`: `HOST24L4T.patch` (vs 24l4s), `HOST24L4TR.patch` (vs 24l4r), `BUILD24L4T_REPORT.md`, `PROTECTED_ROOMS_API_24L4T.md`, `TREE24L4T_SEAL.json`, `UNCHANGED24L4T.json`. Prompt `../prompts/build24l4t.md`.
- The census binding of check_protected_rooms in native admission is ruled a kit binding and is not part of this tree change.

Verify: (1) only the pointing resolution of check_protected_rooms and new tests differ from 24l4s; (2) MUST fixed: a pointing row with a present but unresolvable canonical_scene and no withheld hit refuses R1_PROTECTED_ROOM_UNRESOLVED:pointing even when the ordinary Rooms resolution is clean, and is not accepted as a protected list key; your 46 fuzz rows now refuse; (3) SHOULD a and b still PASS; (4) rerun your 4-stream fuzz against 24l4r and 24l4s: 24l4t admits no row either tree refuses; name every row that flips the other way; (5) what you did not check.

Rules: Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. nice -n 10, at most 8 threads, under 20 GB RAM; `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` for tests. Write the verdict to `VERDICT.md` in this folder only. First line `GO`, `GO AFTER FIXES` or `NO-GO`; at most 15 lines.
