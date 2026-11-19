from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch
from tests.test_r1_build16 import Build16
from tests.test_r2_build_n1 import write
from student_pilot.p3_provenance import load
from student_pilot import r1_persisted as P

class Edges(unittest.TestCase):
    setUp=Build16.setUp
    tearDown=Build16.tearDown
    root=Build16.root
    fixture=Build16.fixture

    def test_checkpoint_and_stream_closure(self):
        root,cfg,_,_=self.fixture()
        r=cfg['r1_training'];original=load(r['handover_receipt']['path'])
        def variant(change,reason):
            receipt=deepcopy(original);pins=receipt['pins'];records={k:load(r['persisted_files'][pins[k]['sha256']]) for k in ('preparation','config','binding','checkpoint')}
            change(records)
            pin=write(root/'variant_preparation.json',records['preparation'])
            records['config']['preparation']=pin;records['binding']['preparation']=pin
            records['checkpoint']['binding']=records['binding'];pins['preparation']=pin
            for k in ('config','binding','checkpoint'):pins[k]=write(root/('variant_'+k+'.json'),records[k])
            paths={p['sha256']:r['persisted_files'].get(p['sha256'],p['path']) for p in pins.values()}
            run={k:pins[k] for k in r['p_run']}
            with self.assertRaisesRegex(ValueError,reason):
                P.verify(write(root/'variant_h.json',receipt),run,pins['artifact'],paths)
        variant(lambda d:d['checkpoint'].update(files={}), 'CHECKPOINT_FILES_REQUIRED')
        variant(lambda d:d['checkpoint'].update(layouts={}), 'CHECKPOINT_FILES_REQUIRED')
        variant(lambda d:d['checkpoint']['files'].update({'../escape':{'sha256':'0'*64}}),'PATH_ESCAPE')
        variant(lambda d:d['checkpoint']['files'][next(k for k in d['checkpoint']['files'] if k.startswith('rng'))].update(bytes=1),'FILE_MISMATCH')
        variant(lambda d:d['preparation']['streams'].pop('vqa'),'STREAMS_MISMATCH')
        variant(lambda d:d['preparation']['streams']['vqa'].update(receipt={}), 'STREAM_RECEIPT_MISMATCH')
        variant(lambda d:d['preparation']['streams']['vqa'].update(indices=write(root/'idx.json',[0])), 'CLOSURE_MISMATCH:indices/vqa')
        receipt=deepcopy(original);receipt['pins']['heads']['sha256']='invalid'
        paths={k:v for k,v in r['persisted_files'].items() if k in {p['sha256'] for p in receipt['pins'].values()}}
        with self.assertRaisesRegex(ValueError,'PIN_INVALID'):
            P.verify(write(root/'bad_pin.json',receipt),r['p_run'],cfg['init_artifact']['artifact'],paths)
        receipt=deepcopy(original);receipt['pins']['extra']=receipt['pins']['heads']
        with self.assertRaisesRegex(ValueError,'CLOSURE_MISMATCH'):
            P.verify(write(root/'extra.json',receipt),r['p_run'],cfg['init_artifact']['artifact'],r['persisted_files'])

    def test_export_manifest_and_artifact(self):
        root,cfg,_,artifact=self.fixture()
        r=cfg['r1_training'];original=load(r['handover_receipt']['path'])
        def variant(change,reason):
            receipt=deepcopy(original);pins=receipt['pins'];art=deepcopy(artifact)
            manifest=load(r['persisted_files'][pins['full_weights']['sha256']])
            change(manifest,pins)
            mp=write(root/'variant_weights.json',manifest);art['full_weights']=mp;pins['full_weights']=mp
            pins['artifact']=write(root/'variant_artifact.json',art)
            paths={p['sha256']:r['persisted_files'].get(p['sha256'],p['path']) for p in pins.values()}
            with self.assertRaisesRegex(ValueError,reason):
                P.verify(write(root/'variant_h.json',receipt),r['p_run'],pins['artifact'],paths)
        variant(lambda m,p:m.update(files=[]),'EXPORT_MANIFEST_MISMATCH')
        variant(lambda m,p:m['files'][0].update(sha256='f'*64),'CLOSURE_MISMATCH:export/')
        variant(lambda m,p:m['files'][0].update(bytes=1),'FILE_MISMATCH:export/')
        def escape(m,p):
            item=m['files'][0];old=item['name'];item['name']='../escape'
            p['export/../escape']=p.pop('export/'+old)
        variant(escape,'PATH_ESCAPE')
        from student_pilot.r1_handover import donor
        with self.assertRaisesRegex(ValueError,'ARTIFACT_MISMATCH'):
            donor(cfg,dict(artifact,step=600))

    def test_invalid_resume_position(self):
        from student_pilot import carrier_c1_run as C,r1_mix as M
        root,cfg,_,_=self.fixture()
        card,idx,_=M.validate_binding(cfg['r2_sampling'])
        receipt=dict(streams={c['stream']:dict(count=len(idx['cells'][c['type']])) for c in card['cells']})
        cfg['preparation']=write(root/'empty_prep.json',receipt)
        with patch.object(C,'validate'),patch.object(C,'prepared',return_value=(receipt,{})):
            for step in (True,-1,1000):
                with self.assertRaisesRegex(ValueError,'RESUME_POSITION_INVALID'):
                    C.first_batch_check(cfg,[0,1,2,3],root/'never.json',start_step=step)
