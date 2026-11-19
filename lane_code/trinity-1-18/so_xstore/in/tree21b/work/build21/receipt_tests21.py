from pathlib import Path
from copy import deepcopy
import unittest
from student_pilot import r1_training as T,r1_handover as H
from student_pilot.r1_persisted import scope
from student_pilot.p3_provenance import load
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
class Receipts21(unittest.TestCase):
 def test_every_receipt_hash_is_authenticated(self):
  value=load(B/'proofs/receipts/RESULT.json');index=load(B/'proofs/receipts/INDEX.json')
  with scope(index):
   for record in value['receipts']:
    pin=dict(record['pin'],sha256='0'*64);stream=record['uses'][0][1]
    with self.subTest(receipt=record['pin']['sha256']):
     with self.assertRaises(ValueError):T.target_identity(dict(r1_training={},streams={stream:pin}))
 def test_prepared_store_mismatch_and_missing_orders(self):
  value=load(B/'proofs/receipts/RESULT.json');index=load(B/'proofs/receipts/INDEX.json')
  missing=0
  with scope(index):
   for record in value['prepared']:
    receipt=load(record['pin']['path']);stream=deepcopy(load(record['preparation']['path'])['streams'][record['stream']])
    if record['status']=='REFUSE':
     with self.assertRaises((OSError,ValueError)):H.prepared_stream_identity(receipt,stream,record['stream'])
     missing+=1;continue
    if receipt.get('schema')=='c1-pose-mix-v1':
     part=stream.get('scene_source',stream);part['sources'][0]['database']['sha256']='0'*64
    else:stream['database']['sha256']='0'*64
    with self.subTest(preparation=record['preparation']['sha256'],stream=record['stream']):
     with self.assertRaisesRegex(ValueError,'MISMATCH'):H.prepared_stream_identity(receipt,stream,record['stream'])
  self.assertEqual(missing,0)
  self.assertEqual(value['missing_order_pins'],[])
  record=next(r for r in value['prepared'] if r['preparation']['sha256'].startswith('888da8e2') and r['stream']=='pose')
  receipt=load(record['pin']['path']);stream=deepcopy(load(record['preparation']['path'])['streams']['pose'])
  stream.get('scene_source',stream)['order']={'path':str(B/'proofs/receipt_auth/absent_order.json'),'sha256':'0'*64}
  with scope(index):
   with self.assertRaises((OSError,ValueError)):H.prepared_stream_identity(receipt,stream,'pose')
