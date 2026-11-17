import subprocess,sys
py=sys.executable
for name,path in [('operator_sealed','out/build_operator.py'),('delivery_sealed','out/build_delivery.py'),('package_sealed','out/tests/test_package.py'),('sequence_sealed','work/test_sequence.py'),('tower_sealed','work/test_tower.py'),('binding_sealed','work/test_memo_binding.py'),('audit_sealed','work/audit_payload.py')]:
 subprocess.run([py,'-B','work/run_logged.py',name,py,'-B',path],check=True)
