Review and fixes are complete; the full dependency inventory is in [REVIEW8c.md](REVIEW8c.md).

| Review finding | Resolution / file:line |
|---|---|
| Host bwrap is unavailable | `tools/proof_prepare.py:45` reads certified k/0.json, checks absolute executable and SHA256; no PATH fallback. |
| Non-login host/environment assumptions | `proof_prepare.py:23` checks Python >=3.9 and all host programs; :29 normalizes environment; `tools/package_proof.py:17` uses Bash -p and absolute isolated Python. |
| Nested namespaces and absent O/r | `proof_prepare.py:54` probes production namespace flags before staging; :109 keeps writable proc/PID/dev, explicitly creates a user namespace, shares host network and overlays O/r; :81 creates private fresh /tmp storage. |
Tests: pinned-only bwrap with host binary masked, wrong SHA/missing/non-executable/relative pin refusals, verbatim nested tk_bwrap, absent O/r, clean environment, fresh /tmp and isolation PASS; 10 patch cases plus repeat refusal and 13 submission cases PASS.
Rebuild: exact selection/derivation, proof, upload, sums, transport and guarded patches are deterministic; evidence/fix8c_checks.json records results and unchanged bindings.
Production jb.sh/job.sh/b/c.sh/b/r.sh, KH manifest, identity, contract, go binding, receipt schema, s.sh and exports remain unchanged; the real job reuses nothing.
Proof: `build/a_8c74b291.sh` SHA256 `3814df676f9e2090057da9c3989b459fb51badbaef9368026e8c1401f2613e48`.
Patch: `build/c_patch_8c.sh` SHA256 `dc5615785d1b0dbeb902fce537a6c7f83bcc71069b6cd8820e266e752a89cdf3`; checks old proof f1f6a151… and current sums 80bb318e…; changes only proof + sums line; retains both in BUN/v_8c.
Operator: deliver that patch as `/project/community/jjyeung/okh7/t_8c.sh`, then run `printf '%s  %s\n' dc5615785d1b0dbeb902fce537a6c7f83bcc71069b6cd8820e266e752a89cdf3 /project/community/jjyeung/okh7/t_8c.sh | sha256sum -c - && bash /project/community/jjyeung/okh7/t_8c.sh`.
Then submit a fresh CPU-only proof using the existing command; KH/o/<job>.proof.json must PASS before s.sh accepts PROOF_JOB. Do not apply the full-bundle c_patch.sh to the installed round-8b state.
Validation was local and CPU-only; no SSH, network, Orchard job, GPU, Git or deletion. Orchard kernel policy and full preparation remain runtime checks.
