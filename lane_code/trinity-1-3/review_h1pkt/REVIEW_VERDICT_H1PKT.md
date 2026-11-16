# H1-1 Orchard packet: cross-family refute review (Devin, trinity-1-3, 2026-11-16 ~20:30Z)
Verdict: **GO AFTER FIXES**. Two small fixes (F1, F2); nothing refutes items 1-4 or 6. Tests ran in copies under work/h1c (W below).

1. Derivation scope: holds. W/build/fx differs from a fresh D0 derivation only in b/r.sh, b/h.py, b/i.py, job.sh (fixed replace_once patches, derive_kit_h1.py:442-451), k/0.json (commit, trainer, record, one relocated receipt part with the same sha), 1.json, config, 4/7/archive/review/staging/s1_record/launch.json and the new trainer tar. The builder tests rerun PASS (W/../log_test_*.txt), including D0 identity 80f4af94 and contract aaf2d7b0. Extra refusals: force_from_step=0, missing h1, milestones [100,300] (W/rv/rv_mut.json).
2. Admission binding: holds. A one-byte-altered tree with a self-consistent pin is refused at derive ("new source needs its own conditional authorization"), and so are changed rows (vqa pin). Without add_k 4.json, derive admits the altered tree (identity 9746274d), but g.py:85 refuses it on source_revision (W/rv/rv_g_a2.py). See R1.
3. D0 isolation: holds for kit, bundle, slot root, run and sessions. H1 has its own RUN, KH, RS, sess.json, GCS keys (q8/8865619b/17c4ffa4_*, q8/d2d30e36/17c4ffa4_s*), and o.sh/orch_h1.sh refuse existing targets. D0's i_bb09a77d parts are only read through cat. The D0 source kit was unchanged after my derivations (sha256sum -c). See R3.
4. Stop bridge: holds on CPU (4 gloo ranks, real r.sh, job.sh, trainer run_steps and the jb.sh slot suffix; USR1 sent only to the batch shell):
   - signal: all ranks stop at step 3 and slot A (step 3) is verified;
   - fileonly: ranks ignore USR1 and the i.py relay delivers nothing; the run-dir request alone stops all 4 at step 3, and the slot is verified;
   - hfail: h.py exits 1; r.sh survives because on_stop runs inside r.sh:80's set +e wait; the ranks stop at step 3 and the slot is verified;
   - full200: H1_STOP at 200, stopped_for_resume=false, m100 and m200 exported, slot (step 200) verified.
   Evidence is in W/evidence/cpu/{signal,fileonly,full200}/result.json and W/evidence/cpu/hfail/{run,slots/A.json}. test_stop_bridge checks the NR->X/runs bwrap alias. Two limits remain: the harness's c.sh binds the run dir at its own path, and no GPU, NCCL or real Orchard /proc test was run.
5. Naming: fix needed (F1). The job name, kit/bundle/root/run tokens, GCS keys, WorkDir and stderr path are all opaque.
6. Faithful gate: holds. identity_check passes at 0.95 and fails at 0.94 and with no camera rows; f.py exits 1 below threshold and 2 on unreadable input (W/rv/rv_gate.json). r.py:33 asserts gate passes plus the receipt sha before the final derive, which alone creates KH, and s.sh needs KH's manifest. Native prep enforces the gate again (carrier_c1_run.py:646 prepare_identity) and so does training (:691 require_identity).

Fixes before submission:
- F1: g.sh:12 runs `tar -xf /project/community/jjyeung/distill/okit/in/cr/rt_b8b60bcef027.tar` on the login node, so the method word "distill" shows in argv to every user. Stage the rt tar into BUN or point to it through an opaque symlink. Inherited c.sh:11-13 (R=/project/community/jjyeung/distill/okit) puts the same word into compute-node argv (tar, kitx.py, sha), and c.sh:102 shows models--Qwen--Qwen3.5-9B. Those exposures already existed under D0; the orchestrator either accepts them as inherited or patches R with a fixed replace_once. Also confirm that okh7/ and KH are 0700, because derive creates KH under umask and its contents include the 372-room R0 list.
- F2: record tokens 5ee9da63, 17c4ffa4, 4b3114cf, 1be16f28 and 766136c1 in work/ORCHARD_LEDGER.jsonl (none there now) before any Orchard call.
Recommended, not blocking:
- R1: derive should refuse a code_tree without add_k 4.json.
- R2: r.py final should assert r['config_identity']==ids['identity'], and z.sh and s.sh should rerun `sha256sum -c sums.txt`.
- R3: K=8865619b shares the node-local tree /tmp/jjyeung/okit_8865619b with D0. If D0's /tmp survived on the same node, tk_persist_exports (c.sh:408) would tar D0's exports into the shared up/ and retry uploads every 10 min (they fail because sessions are absent). Either confirm per-job /tmp or add a jb.sh refusal for foreign run dirs.
- R4: the 4.json conditions still name a "canary-2 resume" that H1 never runs.
Not verified here: the real routing identity rate, the 4-GPU first batch, staging throughput, slot-copy time inside the 3,600 s USR1 window, the GCS fallback and the content scan.
