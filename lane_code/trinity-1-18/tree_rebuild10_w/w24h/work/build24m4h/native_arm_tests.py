import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
import copy,importlib.util,sqlite3,json,ast
from unittest.mock import patch
from student_pilot.p3_provenance import digest,file_pin
from launch_r1 import entry
F=D/'arming_final';workspace=F/'workspace';N=D/'native_arm';N.mkdir()
sp=importlib.util.spec_from_file_location('native_arm',L/'out/arm_routing.py');arm=importlib.util.module_from_spec(sp);sp.loader.exec_module(arm)
base=J.load(F/'base.json');input_db=base['database']['sha256']
db=N/'out.sqlite'
with sqlite3.connect(db) as c:
 c.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)');c.execute('INSERT INTO rows VALUES(0,?,?)',(json.dumps(dict(qid='native-fixture')),'{}'))
dh=J.sha(db)
receipt=dict(schema='c1-routing-stream-v1',stream='routing',count=1,database=dict(path='/tmp/q_22c714e1/p/q/selection/rows.sqlite',sha256=dh))
rp=J.write(N/'receipt.json',receipt)
v=J.load(F/'routing_selection.json');v.update(regenerated_sha256=digest(receipt),regenerated_receipt=dict(path='/tmp/q_22c714e1/p/q/selection/receipt.json',sha256=rp['sha256']))
selection=J.write(N/'selection.json',v)
metadata=J.load(F/'db_bytes.json');metadata['files'].append(dict(path='o/1/selection/rows.sqlite',sha256=dh,size=db.stat().st_size));J.write(N/'metadata.json',metadata)
verdict=N/'RESULT.txt';verdict.write_text('Synthetic test only: PASS\n'+selection['sha256']+'\n'+dh+'\n')
auth=dict(reviewed_selection_sha256=selection['sha256'],reviewed_regenerated_sha256=dh,review_verdict=verdict,regenerated_receipt_path=N/'receipt.json')
with patch.object(arm,'L',workspace):
 result=arm.apply(N/'selection.json',N/'metadata.json',workspace/'out/native_armed',base_path=F/'base.json',**auth)
assert result['native_regeneration']['database_sha256']==dh
assert result['regenerated_sha256']==digest(receipt)!=dh
assert result['already_staged'][0]['sha256']==input_db
assert all(row['name']!='u/'+dh for row in result['files'])
# Execute the real unchanged C host-selection check with only materialization stubbed.
# This verifies that the helper leaves the native receipt digest intact.
point=J.write(N/'point.json',dict(division={}));cfg=dict(streams=dict(pointing=point))
from student_pilot import s1_routing,mdg_parent
host=dict(assertions={})
with patch.object(s1_routing,'build',return_value=receipt),patch.object(mdg_parent,'model_pin',return_value={}):
 entry.check_host_selection(cfg,N/'host',dict(routing_selection=selection),host)
assert host['assertions']['routing_selection'] is True
negative=[]
def refuse(label,code,*,selected=None,receipt_file=None,meta=None,changes=None):
 sel=selected or N/'selection.json';m=meta or N/'metadata.json';a=dict(auth);a.update(changes or {})
 if receipt_file is not None:a['regenerated_receipt_path']=receipt_file
 with patch.object(arm,'L',workspace):
  try:arm.apply(sel,m,workspace/('native_bad_'+label),base_path=F/'base.json',**a)
  except ValueError as e:assert code in str(e),(label,str(e));negative.append(dict(case=label,refusal=str(e)))
  else:raise AssertionError('Accepted '+label)
 assert not (workspace/('native_bad_'+label)).exists()
refuse('missing_receipt','R1_REGENERATED_RECEIPT_REQUIRED',changes=dict(regenerated_receipt_path=None))
J.write(N/'bad_receipt.json',dict(receipt,count=2));refuse('receipt_bytes','E10:',receipt_file=N/'bad_receipt.json')
# Independently reviewed selection bytes cannot supply an arbitrary receipt digest.
bad=copy.deepcopy(v);bad['regenerated_sha256']='e'*64;pin=J.write(N/'bad_selection.json',bad)
rv=N/'BAD_RESULT.txt';rv.write_text('Synthetic test only: PASS\n'+pin['sha256']+'\n'+dh+'\n')
refuse('fabricated_digest','R1_REGENERATED_RECEIPT_DIGEST_DIFFERS',selected=N/'bad_selection.json',changes=dict(reviewed_selection_sha256=pin['sha256'],review_verdict=rv))
# Independently reviewed output hash must still equal the authenticated receipt DB.
rv=N/'BAD_DB_RESULT.txt';rv.write_text('Synthetic test only: PASS\n'+selection['sha256']+'\n'+'e'*64+'\n')
refuse('fabricated_db','R1_REVIEWED_REGENERATED_DIFFERS',changes=dict(reviewed_regenerated_sha256='e'*64,review_verdict=rv))
refuse('missing_output_metadata','R1_DATABASE_METADATA_MISSING:'+dh,meta=F/'db_bytes.json')
mut=copy.deepcopy(metadata);mut['files'][-1]['size']=0;J.write(N/'bad_meta.json',mut)
refuse('invalid_output_size','R1_DATABASE_METADATA_SIZE_INVALID',meta=N/'bad_meta.json')
# Changing the receipt and its pin cannot change the source row count unnoticed.
badreceipt=dict(receipt,count=2);bpin=J.write(N/'count_receipt.json',badreceipt);bad=copy.deepcopy(v);bad.update(regenerated_sha256=digest(badreceipt),regenerated_receipt=bpin);spin=J.write(N/'count_selection.json',bad)
rv=N/'COUNT_RESULT.txt';rv.write_text('Synthetic test only: PASS\n'+spin['sha256']+'\n'+dh+'\n')
refuse('count','R1_REGENERATED_RECEIPT_INVALID',selected=N/'count_selection.json',receipt_file=N/'count_receipt.json',changes=dict(reviewed_selection_sha256=spin['sha256'],review_verdict=rv))
J.write(D/'NATIVE_ARM_TESTS.json',dict(status='PASS',native_host_digest_check=True,generated_database_sha256=dh,input_database_sha256=input_db,receipt_digest=digest(receipt),receipt_file_sha256=rp['sha256'],negative=negative,source_seals=J.load(D/'SEALS.json'),scope='Synthetic SQLite outputs, real arming, three decoded scans, unchanged native host digest check with only build/model materialization stubbed; production data not exercised'))
print('NATIVE ARM PASS',len(negative),'refusals; unchanged native receipt-digest check passes')
