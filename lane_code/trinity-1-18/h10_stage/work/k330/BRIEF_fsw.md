# Task: third one-line fix in H1-0 package b01ec87a6f29b (CPU only), same method and rules as BRIEF_terminator.md / BRIEF_operator_member.md
Workspace /scratch/jjyeung/orch_n30/h10_stage/work/k330 (K = kit). No git, ssh, network, GPU, kills, deletion; write only inside k330.

## Bug (real Orchard failure, job 170620)
After staging, job.py main() runs the first namespace command; vendor orchard_job.namespace(root) binds root/'fsw' (and root/'sj', root/'m/ap'), but nothing creates root/'fsw' for this package, so bwrap exits: "Can't find source path /tmp/a170620b01ec87a6f29b/fsw: No such file or directory".

## Fix (only this)
In K/orchard_h10/job.py main(), immediately before `env=J.environment(root)`, add one line that creates every bind source the namespace needs and staging may not have created:
`for name in ('sj','fsw','m/ap'):(root/name).mkdir(parents=True,exist_ok=True)`
(match the file's compact style). Apply the identical bytes to payload member `orchard_h10/job.py`. Nothing else changes.

## How
1. Rebuild from the CURRENT package (0.tgz 2dd91b3b..., plan 8b89141f...) replacing payload `orchard_h10/job.py` with the edited K/orchard_h10/job.py; update only its payload pin. Back up the current package to K/orchard_h10/package_2dd91b3b/ first. Self-test: no-change rebuild reproduces the current 8 files.
2. Verify: 918 other members byte-identical; 9.json differs only in payload_pins['orchard_h10/job.py']; load_helpers (3.py path, which execs common.py and job.py from the tar) + verify_config pass; compile passes; opacity passes; the 4 package checks pass into kit/logs/t13/. Also add a focused test (K/tests/test_fsw_bind.py, run with bash cpu.sh -m pytest) that builds a fake root containing only what stage() creates (sj/, m/ap/, bwrap placeholder) and asserts that, after the new line, every --bind/--ro-bind source path in orchard_job.namespace(root) exists, except the uv-python ro-bind which comes from the runtime archive (create it in the fixture to mirror runtime group 0). It must FAIL on the old job.py logic and PASS on the new.
3. Append <=12 lines to k330/REPORT_terminator.md: new 0.tgz sha+bytes, plan, PACKAGE.json + five file hashes, test results.
