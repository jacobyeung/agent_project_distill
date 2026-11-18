"""Run the permanent regression oracle against the clean and greedy functions."""
import hashlib,json,os,sys,unittest
from pathlib import Path
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix2';T=L/'work/tree_r1';O=L/'work/merge11/proofs/n1/mutation_M02'
O.mkdir(exist_ok=True);sys.path.insert(0,str(T));os.environ['R2_PROOFS']=str(O)
import student_pilot.row_text_audit as audit
from tests import test_r2_build9fix as test
source=Path(audit.__file__).read_text();mutated=source.replace('[^<]*',r'[\s\S]*')
assert mutated!=source
namespace={'__name__':'student_pilot.mutant'};exec(compile(mutated,str(O/'M02.py'),'exec'),namespace)
sizes=[]
def run():
    before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert before<=200_000_000
    result=unittest.TestResult();test.Fixes('test_M02_interspan_status').run(result)
    after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file());assert after<=200_000_000
    sizes.append(dict(before_bytes=before,after_bytes=after));return result
clean=run();assert clean.testsRun==1 and not clean.errors and not clean.failures
with patch.object(test,'reasons',namespace['reasons']):changed=run()
assert changed.testsRun==1 and not changed.errors and len(changed.failures)==1
result=dict(mutant='M02',status='CAUGHT',test='tests.test_r2_build9fix.Fixes.test_M02_interspan_status',
    source_file=str(Path(audit.__file__).relative_to(L)),source_sha256=hashlib.sha256(source.encode()).hexdigest(),
    mutant_sha256=hashlib.sha256(mutated.encode()).hexdigest(),operator=dict(before='[^<]*',after=r'[\s\S]*'),
    input='<tool_response>\na\n</tool_response> not seen <tool_response>\nb\n</tool_response>',
    clean=dict(tests=clean.testsRun,failures=len(clean.failures),errors=len(clean.errors)),temporary_sizes=sizes,
    mutant_run=dict(tests=changed.testsRun,failures=len(changed.failures),errors=len(changed.errors)),
    failure=changed.failures[0][1],method='In-memory source mutation; the same permanent test oracle runs against each reasons function. Sealed files remain unchanged.',
    M10='Equivalent duplicate blocker insertion; unchanged. Source: review9/REVIEW_VERDICT_TREE9.md finding F2.')
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k!='failure'}))
