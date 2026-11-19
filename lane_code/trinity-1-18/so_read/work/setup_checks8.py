from pathlib import Path
L=Path('/scratch/jjyeung/orch_n30/so_read')
p=L/'work/run_checks.py';s=p.read_text().replace("('round7','work/src/u0/tests/test_round7.py'),", "('round7','work/src/u0/tests/test_round7.py'),\n                  ('round8','work/src/u0/tests/test_round8.py'),")
s=s.replace("('round7_before','test_round7.py','READ_ROUND7_BEFORE','FAILED (failures=10)',[]),", "('round7_before','test_round7.py','READ_ROUND7_BEFORE','FAILED (failures=10)',[]),\n    ('round8_before','test_round8.py','READ_ROUND8_BEFORE','FAILED (failures=27)',[]),")
p.write_text(s)
p=L/'work/build_patches.py';s=p.read_text().replace("'u0/tests/test_round7.py']}","'u0/tests/test_round7.py','u0/tests/test_round8.py']}").replace("'work/apply-round7'","'work/apply-round8'").replace("('off','round4','round5','round6','round7','compare')","('off','round4','round5','round6','round7','round8','compare')").replace('round-4/5/6/7 integration','round-4/5/6/7/8 integration');p.write_text(s)
print('Added round 8 to workspace, fail-before and fresh-application test runners.')
