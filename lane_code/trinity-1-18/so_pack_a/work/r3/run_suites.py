"""Serial bounded validation; record the commands actually executed."""
import json,os,shlex,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[1];applied=r/'applied'
env=dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1')
py='/scratch/jjyeung/envs/p1cpu/bin/python';fixture=root/'work/r2/fixture';runs=[]
def run(name,file,python=py,args=(),extra=None,expected=0):
    extra=extra or {};log=r/(name+'.log');command=['nice','-n','10','env']+[k+'='+str(v) for k,v in dict(env,**extra).items()]+[python,'-I','-s','-B',str(file)]+list(args)
    stamp=subprocess.check_output(['date','-u']).decode().strip();print(stamp+' START '+name,flush=True)
    with log.open('wb') as stream:result=subprocess.run(command,cwd=str(root),stdout=stream,stderr=subprocess.STDOUT)
    row=dict(name=name,command=' '.join(shlex.quote(x) for x in command)+' > '+str(log)+' 2>&1',log=str(log),returncode=result.returncode,expected_returncode=expected,started=stamp)
    runs.append(row);(r/'RUNS.json').write_text(json.dumps(dict(cwd=str(root),runs=runs),indent=2)+'\n')
    stamp=subprocess.check_output(['date','-u']).decode().strip();(root/'work/STATUS.md').write_text(stamp+'\nRound 3 validation: '+name+' returned '+str(result.returncode)+' (expected '+str(expected)+'). Exact command/output in work/r3/RUNS.json and '+str(log)+'.\n')
    print(stamp+' END '+name+' rc='+str(result.returncode),flush=True)
    if result.returncode!=expected:raise SystemExit('Unexpected result: '+name)
def compact(*names):
    command=['nice','-n','10',py,'-I','-s','-B',str(r/'compact.py')]+list(names)
    subprocess.run(command,check=True);size=int(subprocess.check_output(['nice','-n','10','du','-s','-B1',str(root)]).split()[0]);print('workspace_allocated_bytes='+str(size),flush=True);assert size<3000000000
compact('before_tests','after_tests')
run('before_final',applied/'test_review3.py',extra=dict(PACK_SOURCE=r/'before',PACK_R3_WORK=r/'before_final',PACK_R3_FIXTURE=fixture,PACK_DOCS=root/'out_round2'),expected=1)
compact('before_final')
run('review3',applied/'test_review3.py',extra=dict(PACK_R3_WORK=r/'review3',PACK_R3_FIXTURE=fixture,PACK_DOCS=root/'out'))
compact('review3')
run('review3_login',applied/'test_review3.py',python='/usr/bin/python3',extra=dict(PACK_R3_WORK=r/'review3_login',PACK_R3_FIXTURE=fixture,PACK_DOCS=root/'out'))
compact('review3_login')
run('pack',applied/'test_pack.py',extra=dict(PACK_TEST_WORK=r/'pack',PACK_TEST_FIXTURE=fixture))
compact('pack')
run('native',applied/'test_native.py',args=['--work',str(r/'native')])
compact('native/dcheck')
run('review1',applied/'test_review.py',extra=dict(PACK_REVIEW_WORK=r/'review1',PACK_REVIEW_FIXTURE=fixture,PACK_NATIVE_RESULT=r/'native/RESULT.json',PACK_DOCS=root/'out'))
compact('review1')
run('review2',applied/'test_review2.py',extra=dict(PACK_R2_WORK=r/'review2',PACK_R2_FIXTURE=fixture,PACK_DOCS=root/'out'))
compact('review2')
run('adapter_r10',applied/'cont_ops17/work/test_pack_token.py',python='/usr/bin/python3')
run('adapter_d',applied/'cont_ops18/dbuild/test_pack_token.py',python='/usr/bin/python3')
run('small_checks',r/'validate_small.py',python='/usr/bin/python3')
print('ALL SUITES PASSED',flush=True)
