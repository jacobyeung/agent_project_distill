from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
s=(L/'work/integrity7.py').read_text()
s=s.replace("B=L/'out_round7'", "B=L/'out_round8'").replace("work/round7-before-u0","work/round8-before-u0").replace("work/round7-before-5.py","work/round8-before-5.py")
s=s.replace('assert len(pins)==37','assert len(pins)==38')
s=s.replace("tree=ast.parse((L/'work/src/u0/a20.py').read_text())", "tree=ast.parse((L/'work/src/u0/a19.py').read_text())")
s=s.replace("'## Review round 7: finding -> fix -> test'", "'## Review round 8: finding -> fix -> test'")
s=s.replace('workspace==119 and applied==38','workspace==129 and applied==48')
s=s.replace("'round7_before.txt','f16_behavior_before.txt'", "'round7_before.txt','round8_before.txt','f16_behavior_before.txt'")
s=s.replace("'run_checks7.txt','build_patches7.txt'", "'run_checks8.txt','build_patches8.txt'").replace("'gate_integration7.txt','docs7.txt','storage7.txt'", "'gate_integration8.txt','docs8.txt','storage8.txt'")
s=s.replace("assert '37 files' in report", "assert '38 files' in report\nassert 'FAILED (failures=29)' in (C/'round8_before.txt').read_text()\nassert '--bound-export' not in readme\nassert '33 GB' in note and '33 GB' in report\nassert 'adoption_environment' in (O/'kit_parity50/run.py').read_text()")
s=s.replace('datetime(2026,11,19,17,42,18','datetime(2026,11,19,18,30,31')
s=s.replace('reviewed_round7_source_verified','reviewed_round8_source_verified').replace('round7_expected_assertion_failures=10','round8_expected_assertion_failures=29')
s=s.replace("'integrity7.txt'","'integrity8.txt'")
start=s.index("(L/'work/STATUS.md').write_text")
s=s[:start]+'''(L/'work/STATUS.md').write_text(stamp+f"""\nVERDICT: DONE — round-8 fixes and delivery are complete.
All five findings are fixed. The archive preserves admitted symlinks, rejects escaping/broken/cyclic links and retains stderr.
The GPU interpreter/cache/preflight contract is explicit; CPU READY, gate, workers, ue.json and submit bind environment versions and SHA256.
The builder admits only step 400 before reading base inputs; no alternate-export gate parameter remains. Archive-path aliases resolve on both sides.
{workspace} workspace tests and {applied} fresh-application tests pass. All 12 retained failure controls reran; the ten round-8 tests produce 29 expected assertion failures before fixes.
Five diffs apply with zero fuzz; original reader bytes and OFF output bytes are unchanged. ON CPU answers/traces remain exact.
Archive/real-loader admission, CPU operator path, synthetic gate/submit integration, source probes, benchmark/profile and documentation checks pass.
Workspace size after seal: {size:,} unique-inode bytes. out_round8 and the reviewed source snapshot retain their original hashes.
No GPU, Git, SSH, scheduler operation, paid API, input-tree edit or deletion command ran. Production GPU parity/performance/memory and host interpreter/restore remain unrun.
Completed before 18:30:31 UTC. FINAL_INTEGRITY.json seals the delivery.
""")
print('PASS: immutable backup/source snapshot, five patches, fresh applications and all delivery hashes verified.')
print('PASS:',workspace,'workspace tests;',applied,'applied tests; 12 baseline controls; round 8 has 29 expected pre-fix assertion failures.')
print('PASS: step-400-only build, symlink archive/real-loader admission, environment/kit-bound submit; GPU gate remains unrun.')
print('Workspace unique-inode bytes:',size,'Completed:',stamp,'Deadline: Thu Nov 19 18:30:31 UTC 2026')
'''
(L/'work/integrity8.py').write_text(s)
print('Prepared final delivery seal.')
