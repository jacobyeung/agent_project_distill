"""Serial resource-limited suites with verbatim logs and measured storage checks."""
import hashlib,json,os,shlex,subprocess,sys
from pathlib import Path
r=Path(__file__).resolve().parent;root=r.parents[1];final=r/'final2';final.mkdir(exist_ok=True);applied=r/'applied_final'
env=dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1')
py='/scratch/jjyeung/envs/p1cpu/bin/python';fixture=root/'work/r2/fixture';runs=json.loads((final/'RUNS.json').read_text())['runs'] if (final/'RUNS.json').exists() else []
def run(name,file,python=py,args=(),extra=None,expected=0,wrapped=True):
    if any(row['name']==name for row in runs):return
    log=final/(name+'.log');command=['nice','-n','10','env']+[k+'='+str(v) for k,v in dict(env,**(extra or {})).items()]+[python,'-I','-s','-B']+([str(r/'run_test.py')] if wrapped else [])+[str(file)]+list(args)
    stamp=subprocess.check_output(['date','-u']).decode().strip();print(stamp+' START '+name,flush=True)
    with log.open('wb') as stream:result=subprocess.run(command,cwd=str(root),stdout=stream,stderr=subprocess.STDOUT)
    row=dict(name=name,command=' '.join(shlex.quote(x) for x in command)+' > '+str(log)+' 2>&1',log=str(log),returncode=result.returncode,expected_returncode=expected,started=stamp,sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    runs.append(row);(final/'RUNS.json').write_text(json.dumps(dict(cwd=str(root),runs=runs),indent=2)+'\n')
    stamp=subprocess.check_output(['date','-u']).decode().strip();(root/'work/STATUS.md').write_text(stamp+'\nRound 4: '+name+' returned '+str(result.returncode)+' (expected '+str(expected)+'). Exact command/output: work/r4/final/RUNS.json and '+str(log)+'.\n')
    print(stamp+' END '+name+' rc='+str(result.returncode),flush=True)
    if result.returncode!=expected:raise SystemExit('Unexpected result: '+name)
    size=int(subprocess.check_output(['nice','-n','10','du','-s','-B1',str(root)]).split()[0]);row['workspace_allocated_bytes']=size
    (final/'RUNS.json').write_text(json.dumps(dict(cwd=str(root),runs=runs),indent=2)+'\n');print('workspace_allocated_bytes='+str(size),flush=True)
    assert size<3000000000
def compact(*names):subprocess.run(['nice','-n','10',py,'-I','-s','-B',str(r/'compact.py')]+[str(final/name) for name in names],check=True)
run('before',applied/'test_review4.py',python='/usr/bin/python3',args=['Review4'],extra=dict(PACK_SOURCE=r/'before',PACK_R4_WORK=final/'before',PACK_R4_FIXTURE=fixture,PACK_DOCS=root/'out_round3'),expected=1)
run('review4',applied/'test_review4.py',extra=dict(PACK_R4_WORK=final/'review4',PACK_R4_FIXTURE=fixture,PACK_DOCS=root/'out'))
run('review4_login',applied/'test_review4.py',python='/usr/bin/python3',extra=dict(PACK_R4_WORK=final/'review4_login',PACK_R4_FIXTURE=fixture,PACK_DOCS=root/'out'))
run('review3',applied/'test_review3.py',extra=dict(PACK_R3_WORK=final/'review3',PACK_R3_FIXTURE=fixture,PACK_DOCS=root/'out'))
run('review3_login',applied/'test_review3.py',python='/usr/bin/python3',extra=dict(PACK_R3_WORK=final/'review3_login',PACK_R3_FIXTURE=fixture,PACK_DOCS=root/'out'))
run('pack',applied/'test_pack.py',extra=dict(PACK_TEST_WORK=final/'pack',PACK_TEST_FIXTURE=fixture))
run('native',applied/'test_native.py',args=['--work',str(final/'native')],wrapped=False)
compact('native/dcheck')
run('review1',applied/'test_review.py',extra=dict(PACK_REVIEW_WORK=final/'review1',PACK_REVIEW_FIXTURE=fixture,PACK_NATIVE_RESULT=final/'native/RESULT.json',PACK_DOCS=root/'out'))
run('review2',applied/'test_review2.py',extra=dict(PACK_R2_WORK=final/'review2',PACK_R2_FIXTURE=fixture,PACK_DOCS=root/'out'))
run('adapter_r10',applied/'cont_ops17/work/test_pack_token.py',python='/usr/bin/python3',wrapped=False)
run('adapter_d',applied/'cont_ops18/dbuild/test_pack_token.py',python='/usr/bin/python3',wrapped=False)
run('small_checks',r/'validate_small.py',python='/usr/bin/python3',wrapped=False)
print('ALL SUITES PASSED',flush=True)
