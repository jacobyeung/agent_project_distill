import subprocess,sys
for name,args in [('memo',['work/test_memo.py']),('multitype',['work/test_multitype_ab.py']),('baseline_ab',['work/test_baseline_ab.py','Proof.test_real_reader_ab']),('legacy',['work/run_existing_full.py'])]:
 subprocess.run([sys.executable,'-B','work/run_logged.py',name,sys.executable,'-B',*args])
subprocess.run([sys.executable,'-B','work/run_replay.py'])
subprocess.run([sys.executable,'-B','work/run_logged.py','replay_check',sys.executable,'-B','work/check_replay.py'])
