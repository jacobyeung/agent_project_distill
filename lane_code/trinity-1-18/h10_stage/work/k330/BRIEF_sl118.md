# Task: fourth fix in H1-0 package b01ec87a6f29b (CPU only): package b04's heads/selector/sl118 sources
Workspace /scratch/jjyeung/orch_n30/h10_stage/work/k330 (K = kit). Same hard rules as before: no git, ssh, network, GPU, kills, deletion; write only inside k330.

## Bug (real Orchard failure, job 170631)
All camera types read; the first object_abs_distance read failed: `No module named 'selector_inputs'`. b/e2e_reader/stage1.py:118-120 inserts `HEADS/'selector/sl118'` on sys.path and imports selector_inputs; build.py sources() packaged only `heads/selector/*.py`, so payload `b/heads/selector/sl118/` is missing.

## Fix
Add these four files verbatim to the payload as `b/heads/selector/sl118/<name>`, from k330/b04_sl118_from_330/heads/selector/sl118/ (copied from b04_e2ehook on trinity-3-30); their sha256 must equal b04's current pins:
- name_emb.py, selector_inputs.py, sl_tables.py, sl_tables_v1.py (pins in /scratch/jjyeung/orch_n30/h10_stage/work/b04_pins.txt; selector_inputs.py also equals payload b/heads/selector/selector_inputs.py byte-for-byte). Do not add SCALES_S4.json or src118/.
Also make build.py's sources() include `heads/selector/sl118/*.py` so a future full build matches (source edit only; do not run sources()).

## How
1. Rebuild from the CURRENT package (0.tgz e82ac329..., plan 1de19b86...) adding the 4 members and their payload pins; nothing else changes (tar member order as build.py's tar_bytes produces). Back up current package to K/orchard_h10/package_e82ac329/. Self-test no-change rebuild reproduces current 8 files.
2. Verify: 920 old members byte-identical; 9.json differs only by the 4 new payload_pins; load_helpers/verify_config/opacity/compile pass; 4 package checks + test_fsw_bind pass into kit/logs/t14/.
3. Add K/tests/test_distance_imports.py (bash cpu.sh -m pytest): extract the new 0.tgz to a tmp dir, set sys.path exactly as orchard_h10/entry.py does (p/b, p/tree, p), then execute stage1.StageOne.__init__'s import lines (insert HEADS/'selector/sl118', `import selector_inputs`) and assert selector_inputs.__file__ resolves inside p/b/heads/selector/sl118; also import e2e_reader.stage1, e2e_reader.grounding, e2e_reader.real if they import on p1cpu without CUDA (skip a module only with the exact ImportError reason recorded). The test must fail on the old package and pass on the new.
4. Append <=12 lines to k330/REPORT_terminator.md: new 0.tgz sha+bytes, plan, PACKAGE.json + five file hashes, the 4 added members with sha, test results.
