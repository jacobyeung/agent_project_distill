# Task sb_alias: rebuild rows_a2's scene alias map for store v7 and rerun the whole-store room audit
Workspace: /scratch/jjyeung/orch_n30/sb_alias (write here only). W = /scratch/jjyeung/orch_n30/tree_rebuild10_w (read-only).

## Background
Store v7 (204,413 rows, sha 210b2534; mirror /scratch/jjyeung/n30_mirror/rows_r1, design notes: rows_r1's own reports there) was audited for rooms by build 17 (W/w17b/work/build17/proofs/rooms/RESULT.json and the code that wrote it; find it under W/w17b). 85,038 rows resolved to a canonical scene; 119,375 rows carry opaque d1/d2 scene tokens the audit could not resolve, because rows_a2's alias_map.json (token -> canonical scene) was lost. 41,259 rows were resolved through an alias route already: they are your test set.

## Do
a. Rebuild each d1/d2 opaque token's canonical scene from the rows_a2 v4 to v6 build inputs that survive: /scratch/jjyeung/n30_mirror/rows_a2 (v4, v5, v6, a2_vqa_v2, a2_vqa_v3, a2_room_ft2_v1) and the D0 store's provenance fields (find the D0 store under /scratch/jjyeung/n30_mirror by its reports). Join on (dataset, scene token) via each source row's provenance canonical. Read the rows_a2 builder code where it survives to learn how tokens were minted (hash of what, salt where). Self-check: the rebuilt map must reproduce the canonical scene of every one of the 41,259 already-resolvable rows; report agreements, disagreements (with 20 examples) and coverage. If the build inputs do not survive, say which file is missing and stop; never guess a mapping.
b. Rerun the room audit over all 204,413 rows with build 17's canonicalisation against these lists (find each under W/inputs, W/ext, W/w18, W/w19 or the kit metadata W/w12/fixtures/work/kit07ca49df_meta/m/k/, and verify by sha256 prefix): R0 bdb5d402, the 80 withheld rooms 634820b4, dev-S1 969cdb56, BENCH v2 3119aa4a, K1 held-out 4d4736cf.
c. Report hits per list, per stream/family, and the count still unresolved, with 20 example rows per non-empty list (row id, stream, token, canonical scene, list).
Outputs: out/alias_map.json (token -> canonical, with the source row that proves each), out/ALIAS_SELFCHECK.json, out/ROOM_AUDIT.json, out/ALIAS_AUDIT_REPORT.md (at most 80 lines; first line states hits on R0 / withheld-80 / BENCH v2 / dev-S1 / K1 and unresolved count). Tar out/ as out/sb_alias.tar, sha256 in the report.
## Standing rules and answers (read first; you will get no replies, so do not wait for any)
- You run on trinity-1-18 (CMU Trinity cluster), CPU only, no GPU, no network. Never ssh, never kill a process, never touch tmux sessions, no Git, no deletion outside your workspace.
- /home and /data* are an overloaded NFS server: never search, list recursively or bulk-read there. Read only files this prompt names, each once. /scratch is local disk: bounded `rg --files`/`find` under the directories named here is fine.
- Write only inside your workspace. Every path outside it that this prompt names is read-only to you (other lanes own it).
- Local-disk IO needs no approval. Ordinary failures: debug and rerun. The sandbox has no loopback sockets. Stay under 40 GB RAM per process; use at most 16 cores.
- Legality: never invent a mapping, a manifest, a scene list or a proof. A missing input is reported by its exact name and expected location; the affected output says MISSING, never a guess.
- Every output JSON records sha256 of each input it rests on, and your report states the command that produced each number. Write a STATUS.md in the workspace after each stage (one paragraph) and a final report named in the task.
