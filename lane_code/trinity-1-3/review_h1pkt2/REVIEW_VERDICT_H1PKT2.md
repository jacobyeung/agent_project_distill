# H1-1 packet fixes 3-5 + content scan: cross-family review (Devin, trinity-1-3, 2026-11-16 ~23:05Z)
Verdict: **GO AFTER FIXES**. Fixes 3-5 hold. One item is left: compute-node exposures inherited from D0 need an orchestrator ruling or a patch (C1).
Reviewed tree: upload p_d1279a8677c91e57.tar sha256 d1279a8677c91e577d67933139bd52e320d9054b999d99b2d9a2b447d794ceb2 (decoded from orch_h1.sh 87fb17b7c50f6751..., identical bytes), gate patch g_patch.sh f240e251f52780468c43..., packet SHA256SUMS.txt 83a6653bcd154731... (sha256sum -c passes). Test copies are in trinity-1-3 /scratch/jjyeung/orch_n30/review_h1pkt2/work (W).

1. Scope of fixes 3-5. I compared the post-fix-2 upload (e3a462be) with the current one member by member. Only d.py, r.py, g.sh and sums.txt changed.
   - Unchanged bytes: 4.json (admission/authorization), ids.json (identity 6e4f2846..., contract 9a527092...), f.py, trainer tar 25f1c3a7, over.json, jb.sh, s.sh, z.sh, o.sh, v.py, 7.json and d_*.json.
   - d.py diff: the SealedOutput writer, the manifest-scoped mode inventory and member-only copying all replace plain writes. Fresh 0700 o/ and runs/ are created, and the certificate is now always UNREVIEWED. Every replace_once patch string (the stop fix in r.sh/h.py/i.py, job.sh 13 h, c.sh, p0.sh) is byte-identical except for the added fs argument. validate_h1, identity and the authorization checks do not appear in the diff.
   - r.py diff: it adds mode assertions and mode digests and sends launch.json/ANON_OK writes through SealedOutput. The gate assert is unchanged.
   - g.sh diff: tmpfs-root sandbox, create-only extraction that verifies digests on reuse, and a refusal if gate.json already exists. The verdict now comes from fresh JSON bound to the receipt (pass 0, below threshold 1, else 2). The threshold still lives in the unchanged f.py/trainer, and g.sh no longer touches the distill path, so first-review F1 is fixed on the login node.
   - The gate patch embeds exactly g.sh 757a00e4 and sums d23b6e39 (old: c277738e/308ba77b) and refuses if gate, ready or compare evidence already exists.
2. First reviewer's tests on the fixed tree (W/h1c, logs W/log_*.txt). All pass except the noted cases.
   - rv_mut: the baseline derives identity 6e4f2846, and the fresh fixture manifest equals build/fx and ids.fixture_manifest 2e504f0f. Refused: alt tree, changed rows, force0, missing h1, ms300, and A2 (alt tree without 4.json), which is now refused at derive (first-review R1 implemented). rv_g_a2 has no admitted A2 tree left to test.
   - Also pass: rv_g_fx and rv_gate (0.95 pass / 0.94 fail / no-camera fail; f.py rc 1/2).
   - Chains: signal, fileonly and full200 results equal the first review field for field (step 3 / step 3 relay-suppressed / H1_STOP 200, slot verified). hfail ends the same way as in the first review (ranks stop at step 3, slot verified; the harness's m100 assert is an artifact). One harness adaptation: the jb.sh slice anchor moved to '# BEGIN directory preflight' (jb.sh is unchanged since before fix 3).
   - Builder tests pass: test_derivation, gate_binding, staging, stop_bridge, sealed_modes, runtime_inventory, gate_sandbox.
3. Content scan (ANON_SCAN.json). I used a superset regex over 25 upload members, 796 trainer-tar files, the transport scripts and the derived kit, and got 10,194 hits.
   - Exempt content: 10,140 hits, including all 383 prescan hits (372 R0_ROOMS.txt + 11 h1_r0.py).
   - Visible and clean: the job name, sbatch line, WorkDir, okh7 paths, /tmp/jjyeung/a_17c4ffa4, upload names, GCS keys, log names, all login-node argv, and g.sh's bwrap argv.
   - Visible hits (52), all on compute nodes, all inherited byte-for-byte from sealed kit 07ca49df (D0). H1 adds none: its 100 distill part paths are a subset of D0's 111.
     - b/c.sh:11-13,115,117,151,174 and p0.sh:12: /project/community/jjyeung/distill/okit/... appears in tar, cat $parts and python argv (the 43 part paths come from over.json).
     - c.sh:102: mv argv contains models--Qwen--Qwen3.5-9B.
     - c.sh:429: argv `gcsput.py split` contains the literal project word.
     - c.sh:369-375 and r.sh:61: env names STUDENT_* ("student" is arguably a method word).
Fix before submission:
- C1: the orchestrator either accepts these as inherited D0 exposures (then GO) or patches them. A patch would use fixed replace_once edits: R to an opaque okh7 symlink, part paths rewritten under okh7/ (the d.py PART regex already admits them), a gcsput mode alias, and an opaque model dir name. It would then need a re-derive and rerun of the identity check.
Not verified: bubblewrap 0.9.0 on Orchard (local 0.4.0); g.sh walking the real /lustre and /scratch ancestors on Orchard; the two absent local tars (np226, t_e6456bce); GPU/NCCL; first-review F2 (ledger) is outside this brief.
