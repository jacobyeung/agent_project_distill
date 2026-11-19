"""Exercise persisted resume safeguards with CPU stub outputs; never launch a GPU."""
import copy,json,os,shutil,subprocess,sys,time
from pathlib import Path
sys.path.insert(0,'kit/files');import count_guard as G
R=Path.cwd();D=R/'out/runtime_tests_final';D.mkdir(exist_ok=True);M=R/'out/MANIFEST_R0DEV.json';man=G.read(M);original=G.read(R/'out/stub_final/RUNTIME.json');tests=[]
for name in ('cumulative_exhausted','expired_deadline','abnormal_active','changed_deadline','changed_output','clean_resume'):
 out=D/name;out.mkdir()
 for c in man['captures']:
  key=c['canonical'].replace('/','__');shutil.copytree(R/'out/stub_final'/key,out/key)
 state=copy.deepcopy(original);state.update(output=str(out),absolute_deadline=time.time()+600,budget_seconds=1800,status='time_cap')
 if name=='cumulative_exhausted':state['spent_seconds']=1800
 if name=='expired_deadline':state['absolute_deadline']=time.time()-1
 if name=='abnormal_active':state['status']='active'
 if name=='changed_output':state['output']=str(D/'elsewhere')
 G.write(out/'RUNTIME.json',state)
 deadline=state['absolute_deadline']+(1 if name=='changed_deadline' else 0)
 cmd=[sys.executable,str(R/'kit/files/run_count_teacher.py'),'--manifest',str(M),'--manifest-sha256',G.sha(M),'--out',str(out),'--stub','--resume','--deadline-unix',str(deadline)]
 result=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES=''))
 expected=0 if name=='clean_resume' else (3 if name in ('cumulative_exhausted','expired_deadline') else 1)
 assert result.returncode==expected,(name,result.returncode,result.stdout)
 final=G.read(out/'RUNTIME.json')
 if name=='clean_resume':assert final['spent_seconds']>state['spent_seconds'] and final['absolute_deadline']==state['absolute_deadline']
 tests.append(dict(name=name,command=cmd,returncode=result.returncode,stdout=result.stdout,spent_before=state['spent_seconds'],spent_after=final['spent_seconds'],passed=True))
G.write(R/'out/RUNTIME_TESTS.json',dict(passed=len(tests),tests=tests,inputs_sha256={str(M):G.sha(M),str(__file__):G.sha(__file__),str(R/'out/stub_final/RUNTIME.json'):G.sha(R/'out/stub_final/RUNTIME.json'),**G.pins()}))
print(len(tests),'runtime checks passed')
