import subprocess,sys
paths=['out/tests/test_package.py','out/tests/test_constraints.py','work/test_b1.py','work/test_select_stubs.py','work/test_tower.py','work/test_sequence.py','out/test_tower_pair.py','out/test_b1_report.py','work/test_memo_binding.py','work/test_module_selection.py','work/test_operator_memory.py','work/test_fixes.py','work/test_return_cli.py']
for path in paths:
 subprocess.run([sys.executable,'-B','work/run_logged.py',path.split('/')[-1][:-3],sys.executable,'-B',path])
