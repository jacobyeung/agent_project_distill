# STATUS b03_e2etest (EAT-1 acceptance test), trinity-3-30
Brief: /data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/briefs/b03_e2etest.md -> qs/03_e2e_acceptance_test.md. Lane folder L=/scratch/jjyeung/orch_n30/b03_e2etest. Python env: /scratch/jjyeung/envs/p1cpu (torch 2.11 cpu, transformers 5.12.1).
## Done
- L/eat1/: artifact.py (manifest eat1-artifact-v1), hook.py (audit hook + /proc/self/maps + strace windows; model monitor; token provenance; executed-line scope), scan.py + allowlist.json (PROPOSED, unreviewed), run.py (runner, clauses A1-A5, A5 i bwrap sandbox, A5 ii head perturbation, A6 report), toy/ (clean toy + planted.py with five violations), tests/test_eat1.py.
- Tests: `cd L && EAT1_TMP=$L/work/tmp /scratch/jjyeung/envs/p1cpu/bin/python -m unittest eat1.tests.test_eat1` -> 14 OK (12:05Z).
- Inputs copied: C8r code tar (sha f4535bc0, L/work/c8r_src); sealed tree b01ce449 audit copy L/work/audit_copies/tree_b01ce449 (792 files equal RUNTIME_TREE.json); next-leg package b5 L/work/nextleg/tree_rebuild_b5_ba346bd9.tar (sha bc31a06d..., equal to trinity-1-3).
## Next
1. C8r tiny-model dynamic run (adapter L/eat1/adapters/c8r_tiny.py over tree tests' tiny fixture) + static audit -> L/out/BASELINE_C8R.md.
2. Static audit of next-leg tree (b5; b6 when final: trinity-1-3 /scratch/jjyeung/orch_n30/tree_rebuild_w/out/) -> L/out/BASELINE_A2_TREE.md.
3. L/out/RUN.md, L/out/EAT1_READY.md, mirror to second node, design record, RESULT event asking for cross-family refute review of clause definitions + allowlist.
