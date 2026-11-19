# Task sb_evidence: rebuild the nine component-evidence records for vehicle N's tree (schema r2-component-evidence-v1)
Workspace: /scratch/jjyeung/orch_n30/sb_evidence (write here only). W = /scratch/jjyeung/orch_n30/tree_rebuild10_w (read-only; another lane builds there).

## Background
N's trainer tree gates phase 'training' (and every official benchmark read) on nine records read by hash from the kit registry: student_pilot/r2_policy.py (find it under W/w19 or W/w18; read components() and everything it calls, and the tests that exercise it). Today the registry (n1fix2/inputs/registry.json in the kit; locate it under W/w19) has record=null for every slot, and the kit holds gap records EVIDENCE_*.json (status BLOCKED) that say what each slot needs. The slots:
- lineage: init_m544 (the step-544 init, artifact 1d6eeb28: W/.../init_artifact.json), heads_pose, heads_depth, heads_frame_embeddings, depth_init_vc. Each needs an overlaps list and checked_banks covering VSI-Bench, VSTI and ReVSI; any overlap inside that scope refuses. "Complete parent scene manifests, parent membership receipts and checked-bank intersections; inherited exposure must be disclosed."
- external: geometry_tower, segmenter: EXEMPT_FROZEN with frozen=true, resting on upstream release identity and a frozen inventory record.
- new: data_rows_r2, heads_gf1_connector: PROVEN_CLEAN with exclusions_complete.
The original records were lost with a dead node. An orchestrator ruling defers the gate for training only; these records are owed before any official read.

## Sources known to survive (start here; extend the survey by exact names)
- W/w12/fixtures/work/kit07ca49df_meta/m/k/ : the LEG-S1 kit 07ca49df metadata (b02e4385.json, s1_record.json, pool_manifest.json, pool_selection.json, scene_reference.json, benchmark_scene_exclusions.json, dev_scene_exclusions.json, pool_exclusion_*.tsv, pool_indices_*.json and opaque-named JSONs). Identify each by content.
- W/inputs/ (p_configs, p_runtime, records, rooms incl. R0 bdb5d402 and v7 EXCLUSIONS 0cbbf997), W/ext/ (pk = P's staged copies incl. per-stream receipts: benchmark_scene_exclusions 3119aa4a comparisons, benchmark_rows_dropped, heldout_overlap; r1_ops; b12 with K1SPLIT_R0.json), W/w17b, W/w18, W/w19 (packages, proofs).
- /scratch/jjyeung/n30_mirror/ (local; lanes' mirrored outputs: h1_headsft, b08_headrows, rows_a2, rows_r1, rows_r2, tower_redecide, k1_ops3, gt_audit, ...): the head-training runs' row stores and receipts may name the scenes each head trained on.
- The sealed LEG-S1 source archives on NFS, each under 10 MB: /data3/jjyeung/distill_src_archive/t_b01ce449beffe35b.tar, t_37845077e30ea5a2.tar, t_38917ea542d7becf.tar. You may copy each once, one at a time, into your workspace (plain cp of a single file) and untar there. Check first whether W already holds an untarred copy.
- Benchmark scene lists: find the VSI-Bench, VSTI and ReVSI scene lists inside the sources above (benchmark_scene_exclusions 3119aa4a = BENCH v2; the ReVSI dev set record says zero overlap). Identify by sha256 and content.

## Stages
1. Survey: for each slot, list every source that bears on it (path, sha256, what it proves, what it lacks). Write out/SURVEY.json and out/SURVEY.md.
2. Records: for each slot whose sources suffice, write out/records/<slot>.json in the exact schema r2_policy.py accepts (field names and value types from the code and its tests, not from memory), with every claim pointing to source paths and sha256. For lineage slots, compute the checked-bank intersections yourself from the parent scene manifests you found (scene identity after the same canonicalisation the tree uses for rooms) and list any overlap honestly: an overlap is disclosed, never dropped; the gate decides. For a slot whose sources do not suffice, write no record; write out/gaps/<slot>.json naming each missing manifest or receipt by exact name and where it was expected.
3. Self-check: build a copy of the kit registry inside your workspace (never edit W) that binds your records by hash, and run r2_policy's components(registry, 'training') and the official-read phase(s) against it on CPU; show which slots pass, which refuse and why. Run the existing r2_policy tests against your copy.
4. Report out/EVIDENCE_REPORT.md (at most 120 lines): per slot one row (status, record sha256 or gap, what it rests on, overlaps found), the self-check output, and the list of missing sources by name. Tar out/ as out/sb_evidence_records.tar and print its sha256 in the report.
## Standing rules and answers (read first; you will get no replies, so do not wait for any)
- You run on trinity-1-18 (CMU Trinity cluster), CPU only, no GPU, no network. Never ssh, never kill a process, never touch tmux sessions, no Git, no deletion outside your workspace.
- /home and /data* are an overloaded NFS server: never search, list recursively or bulk-read there. Read only files this prompt names, each once. /scratch is local disk: bounded `rg --files`/`find` under the directories named here is fine.
- Write only inside your workspace. Every path outside it that this prompt names is read-only to you (other lanes own it).
- Local-disk IO needs no approval. Ordinary failures: debug and rerun. The sandbox has no loopback sockets. Stay under 40 GB RAM per process; use at most 16 cores.
- Legality: never invent a mapping, a manifest, a scene list or a proof. A missing input is reported by its exact name and expected location; the affected output says MISSING, never a guess.
- Every output JSON records sha256 of each input it rests on, and your report states the command that produced each number. Write a STATUS.md in the workspace after each stage (one paragraph) and a final report named in the task.
