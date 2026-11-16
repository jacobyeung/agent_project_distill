# Build N5 + R3: restore the mandated job-name prefix and make the opaque names non-reversible (one-shot Codex build)

Same rules as `builds/BRIEF_N4.md` (read it): write source, docs and final evidence only inside
`/scratch/jjyeung/orch_n30/b07_offread/builds/N/` and `.../builds/R/`, at most 60 MB of new bytes there in
total; all pytest basetemps, rehearsals, fixture runs and packet builds under `/dev/shm/b07_n4/<fresh name>`;
no ssh, network, Git, GPU, Slurm or Orchard command; no deletion; Python `/scratch/jjyeung/envs/p1cpu/bin/python -B`;
never open a benchmark answer or score.

## Defects in the N4 pass
1. Job names. AGENTS.md and the lane rules mandate that every Orchard job is named `a15_cot_ap` followed by an
   opaque hex token, so the other project's admission check counts it as ours; N4 changed both kits to
   `a0` + hex (builds/N/offnative/cli.py:55, transport.py:65; builds/R kit launcher `--job-name=a0`). Restore
   `a15_cot_ap` + `secrets.token_hex(8)` in both kits, validated by `^a15_cot_ap[0-9a-f]{16}$`, and remove
   `a15_cot_ap` from every forbidden-word list (it is the one required string). The env var may stay `A0_PACKET_SHA256`.
2. The reviewer's gate test was edited (builds/N/kit/tests/test_review_offnative.py lines 70 and 72 differ from
   `/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/review_offnative/review_offnative_tests/test_review_offnative.py`).
   Restore it byte-equal. If a case cannot pass byte-equal because it hard-codes the old argv API, keep the
   original file untouched, add a sibling test file that states the case's intent with the new API, and
   explain in NATIVE_KIT_READY.md in one sentence per case why the original cannot pass; never weaken an assertion.
3. Reversible opaque names. `offnative/opacity.py` and build R's `xnames.py` spell a forbidden name as
   `x0_` + hex of the name, which anyone can decode on Orchard (`x0_767369_0` is "vsi"). Replace this with
   random tokens: a build-time map from each logical name to `x` + `secrets.token_hex(6)` (stable within one
   build, stored only Trinity-side in each kit's `out/` as the name map, sha-pinned), with the packet carrying
   only the tokens; in-job code resolves through a token-only table that holds no logical name. Keep the
   byte-preserving source loading. Extend the packed-byte scans to fail on any hex or base64 spelling of a
   forbidden word as well.

## Gate
Whole N suite, whole R suite, the reviewer's 5 cases (byte-equal file), all CPU fixtures and rehearsals, R's
exact reproduction of 68.77 [66.5, 71.0] and 64.94 [61.3, 68.4]. Rebuild R packages and N code.tar with all
manifests and pins (refresh N's R snapshot deliberately), update both readiness reports, RUN.md, DIFF.md.
Nothing submitted or uploaded. Final message under 10 lines: hashes and test counts.
