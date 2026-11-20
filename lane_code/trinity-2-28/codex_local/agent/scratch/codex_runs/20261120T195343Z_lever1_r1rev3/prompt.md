# Read-only gate review: DEV-MASK depth-writer package and relift harness (rank 1) before one Orchard GPU job

Third pass (after two fix rounds; reviews /scratch/jjyeung/orch_n30/lever1_c/r1rev_findings.md and r1rev2_findings.md, fix briefs BRIEF_R1FIX.md and BRIEF_R1FIX2.md; final token a49a2224fff01: verify each of its four findings is fixed, then re-check everything below).
You are an independent Codex reviewer on trinity-2-28 (read-only). Write only `/scratch/jjyeung/orch_n30/lever1_c/r1rev3/REVIEW_R1.md` if the sandbox allows; else put the review in your final message. No ssh, git, network, GPU, kill, Slurm, or writes elsewhere; do not read /home or /data*. Reads of this node's local /scratch are approved.

Subject: `/scratch/jjyeung/orch_n30/lever1_c/r1/` (REPORT.md, PLACE.md, build_depth.py, depth_format.py, relift.py, runtime/, orchard/, tests/, out/delivery.tgz, out/REFERENCE.json, out/COHORT.json), built to `/scratch/jjyeung/orch_n30/lever1_c/BRIEF_R1.md`. Its base is the trusted T1 package (kit `/scratch/jjyeung/orch_n30/cont_ops24_c/gbuild/g3/orchard_t1`, capture `cont_ops24_c/cap/t1.gz`).

Check, with file:line evidence, only problems that would waste or invalidate the one GPU job or the relift read:
1. Executability on Orchard: the package reuses pinned inputs; resource line (general, gpu:1, 16 CPU, --mem=200G, --exclude=orchard-community-4, 40-min allocation vs 30-min worker cap); entry/CPU check; upload and receipt path; failure path still returns; cap 1 GB.
2. Serving fidelity: the dump reproduces the served depth grid the lift reads (32 x 51 x 51), intrinsics, camera-to-world, applied scale, canvas transform, from the exact served PNGs and one prefill per capture; parity bounds derived from T1 repeats are sound; nothing in the shortened path (no segmentation/linking/decoding) changes the geometry.
3. Naming: no project, benchmark, dataset, model or method word in any Orchard-visible job name, path, argument, environment variable or log (token a09fdd101cc93, job a15_cot_apa09fdd101cc93).
4. Relift validity: the 0.00 m all-150 parity gate; cells a-g as defined in REPORT.md match the brief (b best linked candidate by GT identity, c score floor 0.3 -> 0, d merged link splits, e GT masks, f voted box, g GT relative pose via rank 3's transport, which passed a rigid-transport check); the 56-item / 28-capture cohort; bootstrap.
5. Legality: no GT or label reaches the GPU job; dev-S1 stays a held-out diagnostic.
Verdict first: GO / GO AFTER FIXES (list) / NO-GO. At most 50 lines.
