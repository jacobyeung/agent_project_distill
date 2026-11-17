import subprocess,sys
py=sys.executable
for name,path in [('build2','out/build_package.py'),('operator','out/build_operator.py'),('delivery','out/build_delivery.py'),
                  ('package_final','out/tests/test_package.py'),('constraints','out/tests/test_constraints.py'),
                  ('b1','work/test_b1.py'),('stubs','work/test_select_stubs.py'),('tower','work/test_tower.py'),
                  ('sequence','work/test_sequence.py'),('pairing','out/test_tower_pair.py'),('b1_report','out/test_b1_report.py'),
                  ('existing','work/run_existing_full.py')]:
 subprocess.run([py,'-B','work/run_logged.py',name,py,'-B',path],check=True)
