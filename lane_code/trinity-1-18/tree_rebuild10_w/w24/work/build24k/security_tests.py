from pathlib import Path
import ast,copy,importlib.util,json,os,sys
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];D=L/'work/build24k';F=D/'security_tests_final';F.mkdir(exist_ok=True)
sys.path[:0]=[str(L/'out/kit_n_go/b'),str(L/'work/tree_r1'),str(L/'work/build24')]
import rv,joblib as J
from student_pilot.carrier_c1_run import identity
source=Path(rv.__file__);hits=set()
def trace(frame,event,arg):
 if event=='line' and frame.f_code.co_filename==str(source):hits.add(frame.f_lineno)
 return trace if frame.f_code.co_filename==str(source) else None
cfg=J.load(D/'review_tests/no_pass/node/q_22c714e1_91/v.json')
cfg['r1_training'].pop('review',None)
cases=[('extra_keys','R1_REVIEW_FILE_UNUSABLE'),('nonobject','R1_REVIEW_FILE_UNUSABLE'),('bad_json','R1_REVIEW_FILE_UNUSABLE'),('directory_leaf','R1_REVIEW_FILE_UNUSABLE'),('directory_symlink','R1_REVIEW_FILE_UNUSABLE'),('too_large','R1_REVIEW_CONFIG_TOO_LARGE'),('owner','R1_REVIEW_FILE_UNUSABLE'),('pass',None)]
records=[]
sys.settrace(trace)
for name,expected in cases:
 f=F/name;f.mkdir();k=f/'kit';(k/'k').mkdir(parents=True);n=f/'node';(n/'p').mkdir(parents=True);target=f/'target';target.mkdir();private=target/'n_r';private.mkdir(mode=0o700)
 J.write(k/'k/p.json',dict(n_root=str(target)));J.write(k/'k/a.json',dict(review_wait_seconds=1))
 J.write(n/'rooms.json',dict(scope='synthetic security fixture'));J.write(n/'v.json',cfg)
 value=dict(verdict='PASS',config_identity=identity(cfg),evidence={});review=private/'review.json'
 if name=='extra_keys':value['scope']='outside evidence'
 if name=='nonobject':value=[]
 if name=='directory_leaf':review.mkdir(mode=0o600)
 else:J.write(review,value);review.chmod(0o600)
 if name=='bad_json':review.write_text('{broken')
 if name=='directory_symlink':private.rename(target/'elsewhere');private.symlink_to(target/'elsewhere',target_is_directory=True)
 if name=='too_large':
  with (n/'v.json').open('wb') as file:file.seek(50_000_000);file.write(b'X')
 if name=='owner':
  with patch.object(rv.os,'getuid',return_value=-1):rc=rv.run(k,n,n/'v.json','72',interval=.01)
 else:rc=rv.run(k,n,n/'v.json','72',interval=.01)
 live=target/'o/72/live'
 if expected:assert rc==1 and J.load(live/'REVIEW_REFUSED.json')['refusal']==expected
 else:assert rc==0 and J.load(live/'REVIEW_ACCEPTED.json')['identity']==identity(cfg)
 records.append(dict(case=name,refusal=expected,returncode=rc))
sys.settrace(None)
statements={n.lineno for n in ast.walk(ast.parse(source.read_text())) if isinstance(n,ast.stmt)}
J.write(D/'SECURITY_TESTS.json',dict(status='PASS',records=records))
J.write(D/'COVERAGE.json',dict(source=str(source.relative_to(L)),sha256=J.sha(source),covered=sorted(hits&statements),missing=sorted(statements-hits),statement_count=len(statements),covered_statements=len(hits&statements),scope='Standard-library sys.settrace on direct native-evidence and security cases only. Separate shell/signal tests cover subprocess paths; no total-coverage claim.'))
print('security and size refusals PASS; traced',len(hits&statements),'of',len(statements),'helper statements')
