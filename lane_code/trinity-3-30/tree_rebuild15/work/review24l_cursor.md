# Independent re-review (read-only, once) of TREE build 24l of lane tree_rebuild: the fixes to your review of build 24j (vehicle N's host receipt, ORCH RULING 1943Z Option T)

You review; you do not fix or design fixes. You are a different model family from the builder; this change produces the evidence an admission gate reads. You run once, read-only, on trinity-1-18. Report only verified problems, each with file:line and the command or reading that shows it. Your final message is the verdict.

## What changed
- Base: build 24j's tree `/scratch/jjyeung/orch_n30/tree_rebuild10_w/work/x24l_back/work/tree_r1_base` (seal 189df6ac590caf7622354c3bd1f991e599776494ced635a23f0c93eb1b567710). Changed: `x24l_back/work/tree_r1`. Patch, report, evidence: `x24l_back/out/{HOST24L.patch,BUILD24L_REPORT.md,UNCHANGED24L.json,TREE24L_SEAL.json,ROUTING_DIGEST_STABILITY.json,KIT_WIRING_24L.md}`. The 24j base is itself reviewed (your verdict on 24j is `x24l_back/REVIEW24J_CURSOR.md`; read it first).
- The fixes requested: (MUST 1) check_host_scene certifies the twin-augmented config that trains (production_proof.py augment block); (SHOULD) host.json records the request's routing_selection pin and digest(regenerated); host.json records the routing_base / routing_inputs substitution (sha256 before and after, routing_substituted); staged entries are re-verified after a caller stage hook, or the stager recorded. (MUST 2 is handled in the kit and by an independent row-equality check; ROUTING_DIGEST_STABILITY.json says whether the digest depends on anything besides the root path and staged inputs: check that claim.)

## Verify
1. Each fix is present, correct and tested; the test for MUST 1 fails on the 24j order.
2. Only production_proof.py, entry.py and test files differ from 189df6ac (recompute every sha256 yourself against UNCHANGED24L.json); admit(), identity(), row legality, exclusions, routing policy, sampling, scoring and mode p are byte-identical; your 24j findings are not reintroduced elsewhere.
3. The receipt still cannot be PASS unless all seven assertions hold on evidence, after bind_handover, for the final config identity.
4. Say what you did not check.

## Rules
Read-only. No ssh, network, GPU, Git, tmux, scheduler or another agent. Never list, search or grep on /home or /data*. Any process runs under nice -n 10, at most 8 threads, under 20 GB RAM; use `/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B` to run the tree's tests if you need to. Write your verdict to `VERDICT.md` in this folder and nowhere else. First line: `GO`, `GO AFTER FIXES` (each fix MUST or SHOULD, with evidence) or `NO-GO`. Then at most 25 lines.
