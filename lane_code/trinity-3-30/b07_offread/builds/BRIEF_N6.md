# Build N6 + R4: fix re-review findings F1-F3 and residuals in builds N and R (one-shot Codex build)

Same rules as `builds/BRIEF_N4.md` and `builds/BRIEF_N5.md` (read both): write source, docs and final evidence
only inside `/scratch/jjyeung/orch_n30/b07_offread/builds/N/` and `.../builds/R/`, at most 60 MB of new bytes
there; all pytest basetemps, rehearsals, fixture runs and packet builds under `/dev/shm/b07_n6/<fresh name>`
(you may also create `/scratch/jjyeung/orch_n30/b07_offread/builds/N/work/nonshm_<k>/` for the non-/dev/shm
rehearsals below, each under 20 MB, or say why a rehearsal needs more); no ssh, network, Git, GPU, Slurm or
Orchard command; no deletion; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`; never open a benchmark answer
or score. Verdict to satisfy:
`/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative2/REVIEW_VERDICT_OFFNATIVE2.md`;
the reviewer's tests are in `.../events/review_offnative2/review_offnative2_tests/` (test_review_offnative2.py
plus sim_r_namespace.py; F1 and F2 run from builds/R, F3 from builds/N/kit/tests; all three fail now). Copy them
in byte-equal; they are the gate, with both whole suites, all CPU fixtures and rehearsals, and R's exact
reproduction of 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4].

## Fixes
1. F1 (blocks every direct read): on a non-/dev/shm root, as on Orchard, R's xnames maps absolute argv paths but
   `vllm_isolated.sh` (run by /bin/sh without xnames) still execs the logical interpreter path that is absent from
   the namespace (orchard_launcher.py:225/:227, orchard_job.py:130). Write the mapped path into the script (or
   exempt bind targets consistently) and add one full CPU rehearsal on a non-/dev/shm root for R and one for N,
   so the production mapping branch executes in tests.
2. F2: no dataset word in in-job arguments. orchard_job.py:140 adds 288 `--ro-bind .../arkitscenes/<id>.mp4`
   arguments that `ps` shows for the whole job. Bind media by opaque relative names (sha-keyed, map on Trinity),
   and scan every child argv (bwrap and each subprocess) with the forbidden-word scan, in both kits.
3. F3 (before a VSI-Bench harness read): partition VSI-Bench harness shards by scene, charge each shard its own
   scenes' staging, G3T and SAM cost, and compute K so each shard's honest estimate (decode + its scenes + proof
   with its second model load + canary + loading + 600 s reserve) fits 21,600 s; record the estimate per shard.
4. Residuals: `--export=A0_PACKET_SHA256=<sha>` (not `NONE,...`); add R's `--account=mt01` and `--no-requeue` to
   N's argv; Log.fileno (opacity.py:235) must keep child logs (WATCHDOG, chain) in the job's log files and not
   leak an fd per call; remove the test-only /dev/shm bypass from shipped code (proposals.py:61-64) by injecting
   the allowed root in tests instead, so test_frozen_proposal_pipeline passes from any basetemp.

## Deliver
Rebuild R packages and N code.tar with all manifests and pins (refresh N's R snapshot deliberately), update both
readiness reports (first sentence READY / NOT READY per benchmark x reader), RUN.md, DIFF.md. Nothing submitted
or uploaded. Final message under 10 lines: hashes and test counts including the reviewer's three.
