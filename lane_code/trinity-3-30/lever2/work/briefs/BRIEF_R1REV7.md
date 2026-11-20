# Read-only gate review: DEV-MASK depth-writer package and relift harness (rank 1) before one Orchard GPU job

Seventh pass, before the ONE resubmission (Orchard job 173872 failed: 26 tower vendor files omitted; `/scratch/jjyeung/orch_n30/lever1_c/r1/DEBUG.md`). The sixth review (`/scratch/jjyeung/orch_n30/lever1_c/r1rev6/REVIEW.md`) left two items, addressed by `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R1FIX6.md`: (1) the orchestrator approved a 50-minute allocation (worker cap 30 or 35 min); check every resource line, minimum-allocation check and deadline window agrees with 50 minutes and the forecast has headroom; (2) an exhaustive static import audit of the GPU path (out/IMPORT_AUDIT.json plus a failing test for unresolved imports). Verify both first, and that the validation covers the exact delivery hash.
You are an independent Codex reviewer on trinity-2-28 (read-only). Write only `/scratch/jjyeung/orch_n30/lever1_c/r1rev7/REVIEW_R1.md` if the sandbox allows; else put the review in your final message. No ssh, git, network, GPU, kill, Slurm, or writes elsewhere; do not read /home or /data*. Reads of this node's local /scratch are approved (do not stop to ask).

Subject: `/scratch/jjyeung/orch_n30/lever1_c/r1/` (REPORT.md, PLACE.md, BUILD.json, build_depth.py, depth_format.py, relift.py, runtime/, orchard/, tests/, out/delivery.tgz, out/REFERENCE.json, out/COHORT.json), built to `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R1.md`. Base: the trusted T1 package (kit `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/g3/orchard_t1`, capture `cont_ops24_c/cap/t1.gz`).

Check, with file:line evidence, only problems that would waste or invalidate the one GPU job or the relift read:
1. Executability on Orchard: pinned inputs reused; resource line (general, gpu:1, 16 CPU, --mem=200G, --exclude=orchard-community-4, 50-min allocation vs 30- or 35-min worker cap); entry/CPU check; upload and receipt path; failure path still returns; cap 1 GB.
2. Serving fidelity: the dump reproduces the served depth grid (32 x 51 x 51), intrinsics, camera-to-world, applied scale, canvas transform, from the exact served PNGs and one prefill per capture; parity bounds from T1 repeats sound; the shortened path changes no geometry.
3. Naming: no project, benchmark, dataset, model or method word in any Orchard-visible job name, path, argument, environment variable, log or job-written file (current token as in PLACE.md / BUILD.json; all three agree).
4. Relift validity: the 0.00 m all-150 parity gate; cells a-g as in REPORT.md match the brief; the 56-item / 28-capture cohort; bootstrap.
5. Legality: no GT or label reaches the GPU job; dev-S1 stays a held-out diagnostic.
Verdict first: GO / GO AFTER FIXES (list) / NO-GO. At most 50 lines. Be quick.
