from pathlib import Path
import base64,importlib.util,io,json,os,sys,unittest
from unittest.mock import patch
L=Path(__file__).resolve().parents[2];B=L/'work/build21';sys.path[:0]=[str(B),str(L/'work/tree_r1')]
import joblib as J,jobtest,naming21
O=B/'proofs/review_controls';O.mkdir(parents=True,exist_ok=True)
def module(path):
    s=importlib.util.spec_from_file_location('mutant21',path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
records=[]
old=J.load(L/'work/build20/kits/q/k/p.json')
records.append(dict(fix='ANON_OK staging',before_fails='ANON_OK.json' not in old['p_files'],after_passes='ANON_OK.json' in J.load(B/'kits/q/k/p.json')['p_files']))
for kit,label in [(L/'work/build20/kits/q','before'),(B/'kits/q','after')]:
    try:naming21.scan_decoded(kit);result='PASS'
    except (ValueError,OSError) as e:result=str(e)
    records.append(dict(fix='decoded operational names',control=label,result=result))
jobtest.Job20.setUpClass()
oldlib=module(B/'base/joblib.py')
r=J.resolve(jobtest.Job20.kit,jobtest.Job20.pool,jobtest.Job20.listing,O/'resolved.json')
request=oldlib.stage_payload(jobtest.Job20.kit,r,O/'old_layout')
from student_pilot.full_ft import read_export
try:read_export(O/'old_layout/u');before=False
except FileNotFoundError:before=True
r=J.resolve(jobtest.Job20.kit,jobtest.Job20.pool,jobtest.Job20.listing,O/'resolved.json')
J.stage_payload(jobtest.Job20.kit,r,O/'new_layout');read_export(O/'new_layout/w')
records.append(dict(fix='native export layout',before_fails=before,after_passes=True))
oldenv=module(B/'base/orchard_paths.py')
from student_pilot import orchard_paths as newenv
with patch.dict(os.environ,{'Q_E1':'1'},clear=True):
    records.append(dict(fix='opaque environment aliases',before_fails=not oldenv.enabled(),after_passes=newenv.enabled()))
mut=B/'mutant';mut.mkdir(exist_ok=True)
source=(B/'joblib.py').read_text()
for name,a,b in [
 ('wrong_manifest_name',"names={'full_weights.json':mp['sha256']","names={'other.json':mp['sha256']"),
 ('wrong_replica_parent',"resolved['config']['r1_training']['persisted_files'][h]=ns+'/w/'+name","resolved['config']['r1_training']['persisted_files'][h]=ns+'/u/'+h"),
 ('missing_index',"names.update({item['name']:item['sha256'] for item in manifest['files']})","names={k:v for k,v in names.items() if k=='full_weights.json'}\n    names.update({item['name']:item['sha256'] for item in manifest['files']})")]:
    assert a in source
    (mut/'joblib.py').write_text(source.replace(a,b,1));m=module(mut/'joblib.py')
    # A distinct fixed subfolder prevents a valid sibling from masking an omitted file.
    jobtest.Job20.setUpClass();original=jobtest.Job20.root
    dest=O/name;dest.mkdir(exist_ok=True)
    r=J.resolve(jobtest.Job20.kit,jobtest.Job20.pool,jobtest.Job20.listing,dest/'resolved.json')
    caught=False
    try:
        request=m.stage_payload(jobtest.Job20.kit,r,dest/'node')
        read_export(dest/'node/w')
        assert request['_paths'][jobtest.Job20.receipt['pins']['full_weights']['sha256']]==jobtest.Job20.spec['namespace']+'/w/full_weights.json'
    except (AssertionError,ValueError,OSError):caught=True
    records.append(dict(mutation=name,caught=caught));assert caught
# The executable scanner must inspect the decoded payload, including environment keys.
kit=B/'kits/q';p=kit/'k/j.json';saved=p.read_bytes()
for word in ('distill','Qwen','STUDENT_MODEL_ROOT'):
    cap=json.loads(saved);raw=base64.b64decode(cap['payload'])+('\nexport '+word+'=1\n').encode()
    p.write_bytes(jobtest.rawcap(raw))
    try:
        try:naming21.scan_decoded(kit);caught=False
        except ValueError:caught=True
        assert caught;records.append(dict(mutation='decoded_'+word,caught=caught))
    finally:p.write_bytes(saved)
for row in records:
    if 'before_fails' in row:assert row['before_fails'] and row['after_passes']
J.write(O/'RESULT.json',records)
print(json.dumps(records,indent=2))
