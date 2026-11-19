# Read-only investigation for lane tree_rebuild: how can vehicle N's production launch pass launch_r1.entry.admit()? (once, read-only, answer within 25 minutes)

You investigate; you do not fix or build. You run once, read-only, on trinity-1-18; nobody answers questions. Every claim cites file:line or an artifact path. Your final message is the answer.

## Facts so far
- Tree `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/work/tree_r1` (seal 57a1f14d). Kit `/scratch/jjyeung/orch_n30/tree_rebuild10_w/w24/out/kit_n_go` (build 24h, GO template; base64-json configs in k/, decode with `json.loads(base64.b64decode(json.load(open(f))['payload']))`). Build reports `w24/out/BUILD24H_REPORT.md` and `w24/out/PRODUCTION_BLOCKERS.md`.
- The launch job runs (decoded k/j.json): `a.py q` (launch_r1.production_proof.run on the request) -> d.py room audit -> h.py (writes v.json from q's p/q/RESULT.json config and, since 24h, pins a host receipt and a review) -> t.py -> u.py: `admit(cfg)` then `train(cfg)` on v.json.
- launch_r1/entry.py:60-105 admit() requires r1_training.host_receipt with status PASS, config_identity == identity(cfg), all of ASSERTIONS (entry.py:9) true and loader_audit.complete; four store_hashes; r2_sampling with row_plan_sha256; and a review. entry.frame_host() (entry.py:108-215), used only by `a.py p` with k/h.json, does the full native preparation (s1_admission prepare_only, r1_population.bind_prepared, r1_loader.production_audit) and returns config_identity = identity(produced population config). The kit's k/h.json lists as missing: the staging closure, the regenerated routing selection pin, the sampler indices and the real frame-host preparation. production_proof.run (mode q) never calls frame_host() but does preparation, population binding, loader audit and bind_handover (store_hashes, continuation_identity, handover_mapping).

## Answer
1. Trace both paths exactly. For mode p (frame_host) and mode q (production_proof.run): what each prepares, which config each produces, which fields of admit() each satisfies, and whether the config admit() and train() receive in u.py can carry a host receipt whose config_identity equals its own identity on either path. Does frame_host's produced config carry the four store_hashes and the handover binding that admit() and train() need, or does only q's?
2. Is there a native sequence in the sealed tree (for example launch_r1/build.py's own production flow, or a documented p -> t sequence) that yields a config which passes admit()? Name it and say what inputs it lacks in this kit (the h.json missing items) and whether they can be produced kit-only.
3. Give the smallest change that makes N's launch pass admit() legitimately, with no fabricated assertion: (a) a kit-only change, if one exists; else (b) the smallest tree change, with its scope, the files and lines, and what it must not touch (admission semantics, legality, scoring). For each option, give the cost in job time (a second preparation?) and the tests that would show it works. Rank them.
4. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM. First line: `KIT-ONLY PATH EXISTS`, `TREE CHANGE NEEDED` or `UNCLEAR`. Then at most 40 lines.
