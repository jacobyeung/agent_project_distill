# Read-only review: amendment C1 of the registered R1 pooled harm tool, its tests, and the runaway counter

You review; you do not edit, ssh, submit or delete. Read only these paths; no recursive search elsewhere; no Git.
- Registered tool: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/pooled_rule/pooled_harm_rule_v3.py (sha256 3c7661fe...), its registration REGISTERED_POOLED_RULE_R1.md and POOLED_RULE_REGISTRATION_v3.md in the same folder.
- Amended copy: /scratch/jjyeung/orch_n30/cont_ops17/pooled_c1/pooled_harm_rule_v3_c1.py; diff C1.diff in that folder.
- Tests: test_c1.py and its output TEST_C1_OUTPUT.txt (same folder). Runaway counter: count_runaways.py (same folder); it must equal runaways() of /scratch/jjyeung/orch_n30/cont_ops16/work/c15/cfix/derived_v3.py.
- Operator scripts: /scratch/jjyeung/orch_n30/cont_ops16/work/c15/h1read7/post_r1_c.sh and post400.sh; diffs POST_R1_C.diff, POST400.diff against h1read/post_r1.sh and post200.sh.
Context: leg R1 (run 673bc60f) continues from step 200 under a new run id 6ed2c7aa (continuation C', same lineage). The orchestrator ruled the rule does not change; only the decision-run pin becomes step-keyed: 673bc60f for steps up to 200, 6ed2c7aa for 400/600/800. Levels, base manifests (dev-S1 e08a1d34, R0-dev 86c8f993), crosswalk 994902af, bootstrap, seeds, output format must stay byte-equal.
Answer with file:line evidence:
1. Does anything other than the run pin differ between the two tools (code paths, constants, output fields, ledger writes)?
2. Can the amended tool pass (stay SILENT on, or accept) a read that the registered tool would STOP, for any run/step/manifest combination other than a 6ed2c7aa read at 400/600/800? Can it accept a 6ed2c7aa read at a step it should refuse, or a 673bc60f read at 400+?
3. Do the tests establish what they claim (regression byte-identity on the real step-200 decision read, the three refusals, acceptance at the later-look levels of a 6ed2c7aa m400 manifest built by build_manifest.py)? Any synthetic-fixture weakness that hides a real failure?
4. Is count_runaways.py's definition identical to derived_v3.runaways() and to the amendment's repair test (single counts, bounds 2/150 dev-S1 and 8/287 R0-dev)? Does post400.sh gate every step-400 output behind the registration file and use the C1 tool in decision mode with ledger and export receipt?
Verdict line: REGISTER, REGISTER AFTER FIXES (list), or DO NOT REGISTER. Under 50 lines.
