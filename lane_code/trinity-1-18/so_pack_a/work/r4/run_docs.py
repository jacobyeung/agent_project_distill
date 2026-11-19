"""Check the final operator text under actual login Python."""
from pathlib import Path
import hashlib,json,shlex,subprocess
r=Path(__file__).resolve().parent;root=r.parents[1];final=r/'final2';applied=r/'applied_verified';fixture=root/'work/r2/fixture'
env=dict(CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',PYTHONDONTWRITEBYTECODE='1',PACK_DOCS=str(root/'out'))
rows=[]
cases=[('docs1','test_review.py','PACK_REVIEW',['Review.test_r6_operational_inventory']),('docs2','test_review2.py','PACK_R2',['Review2.test_05_exact_forbidden_rule_documented','Review2.test_06_five_rows_and_error_limit']),('docs3','test_review3.py','PACK_R3',['Review3.test_07_operator_docs','Review3.test_07_native_archive_documented','Review3.test_07_header_confirmation_documented']),('docs4','test_review4.py','PACK_R4',['Review4.test_03_policy_archive_is_sha_pinned','Review4.test_06_operator_docs_current','Review4.test_07_ledger_precedes_verify_in_note'])]
for name,file,prefix,args in cases:
    stamp=subprocess.check_output(['date','-u']).decode().strip();extra={prefix+'_WORK':str(final/name),prefix+'_FIXTURE':str(fixture)}
    cmd=['nice','-n','10','env']+[k+'='+v for k,v in dict(env,**extra).items()]+['/usr/bin/python3','-I','-s','-B',str(applied/file)]+args
    log=final/(name+'.log')
    with log.open('wb') as stream:result=subprocess.run(cmd,stdout=stream,stderr=subprocess.STDOUT,cwd=str(root))
    rows.append(dict(name=name,command=' '.join(shlex.quote(x) for x in cmd)+' > '+str(log)+' 2>&1',log=str(log),returncode=result.returncode,expected_returncode=0,sha256=hashlib.sha256(log.read_bytes()).hexdigest(),started=stamp))
    (final/'DOC_RUNS.json').write_text(json.dumps(rows,indent=2)+'\n');print(stamp+' '+name+' rc='+str(result.returncode),flush=True);assert result.returncode==0
