"""Receipt identity and official component integrity regressions."""
from pathlib import Path
from copy import deepcopy
import os, unittest
from student_pilot.p3_provenance import load, file_pin, digest
from student_pilot import r1_handover as H, r1_training as T, r1_components as C, r2_policy as R
from student_pilot.r2_contract import selected_init
from tests.test_r2_build_n1 import write

L=Path(os.environ['R2_LANE_ROOT'])

class Review20(unittest.TestCase):
    def setUp(self):
        self.root=Path(os.environ['R2_PROOFS'])/'review20'/self._testMethodName
        self.root.mkdir(parents=True,exist_ok=True)
        from unittest.mock import patch
        original=Path.open
        def opened(path,mode='r',*args,**kwargs):
            return original(path,mode.replace('x','w') if path.is_relative_to(self.root) else mode,*args,**kwargs)
        context=patch.object(Path,'open',opened);context.start();self.addCleanup(context.stop)

    def test_real_pose_target(self):
        pin=file_pin(L/'fixtures/work/kit07ca49df_meta/m/k/8957d119.json')
        cfg=dict(r1_training={},streams={'pose':pin})
        value=T.target_identity(cfg)
        self.assertEqual(value['stores']['pose'],digest(H.pin_values(load(pin['path']))))
        original=load(pin['path'])
        for key in ('schema','division','sources'):
            changed=deepcopy(original)
            if key=='schema':changed[key]='other'
            elif key=='division':changed[key]['sha256']='bad'
            else:changed[key][0]['receipt']['sha256']='bad'
            cfg['streams']['pose']=write(self.root/'bad.json',changed)
            with self.assertRaises(ValueError):T.target_identity(cfg)
        changed=deepcopy(original);changed['sources'].reverse()
        self.assertNotEqual(H.stream_identity(changed,'pose'),value['stores']['pose'])
        with self.assertRaises(ValueError):H.stream_identity(original,'vqa')

    def test_prepared_mix(self):
        child=write(self.root/'child.json',dict(database=dict(path='/opaque',sha256='b'*64),count=3))
        division=dict(path='/division',sha256='c'*64)
        receipt=dict(schema='c1-pose-mix-v1',division=division,sources=[dict(kind='rows',receipt=child,frame_prefix=None)])
        stream=dict(kind='mix',division=division,count=2,sources=[dict(receipt['sources'][0],database=load(child['path'])['database'],count=2)],
                    order=write(self.root/'order.json',[[0,0],[0,2]]))
        self.assertEqual(H.prepared_stream_identity(receipt,stream,'pose'),(H.stream_identity(receipt,'pose'),2))
        filtered=dict(stream,scene_source=deepcopy(stream),count=1,order=write(self.root/'filtered.json',[[0,2]]))
        self.assertEqual(H.prepared_stream_identity(receipt,filtered,'pose')[1],1)
        filtered['order']=write(self.root/'foreign.json',[[0,1]])
        with self.assertRaises(ValueError):H.prepared_stream_identity(receipt,filtered,'pose')
        for change in ('source','database','order','count','division'):
            bad=deepcopy(stream)
            if change=='source':bad['sources'][0]['receipt']=dict(child,sha256='d'*64)
            if change=='database':bad['sources'][0]['database']['sha256']='d'*64
            if change=='order':bad['order']=write(self.root/'wrong.json',[[0,0],[0,3]])
            if change=='count':bad['sources'][0]['count']=3
            if change=='division':bad['division']=None
            with self.assertRaises(ValueError):H.prepared_stream_identity(receipt,bad,'pose')

    def identity(self,sha):
        return dict(artifact_sha256=sha,parent_run='r',parent_kit='k',parent_source_seal='a'*64,parent_configuration_prefix='b',step=544)

    def test_selection_binds_returned_identity(self):
        checked=write(self.root/'checked.json',{})
        selected=write(self.root/'selected.json',dict(component_evidence={'init_m544':dict(status='DEFERRED')}))
        value=dict(schema='r2-init-selection-v1',artifact=checked,identity=self.identity(selected['sha256']))
        with self.assertRaisesRegex(ValueError,'IDENTITY_MISMATCH'):selected_init(write(self.root/'selection.json',value),official=True)
        value['identity']=self.identity(checked['sha256'])
        self.assertEqual(selected_init(write(self.root/'selection.json',value),official=True),value['identity'])
        value.update(artifact=selected,identity=self.identity(selected['sha256']))
        with self.assertRaisesRegex(ValueError,'DEFERRED'):selected_init(write(self.root/'selection.json',value),official=True)

    def verified(self):
        from tests.test_r2_policy import evidence
        registry=evidence(self.root/'records')
        records=R.components(registry,'training');status=C.normalize(records)
        prep=write(self.root/'prep.json',dict(schema='c1-preparation-v1',component_evidence=records,r1_training=dict(registry=registry)))
        return dict(r1_progress=dict(step=600),component_evidence=status,component_preparation=prep,component_evidence_sha256=digest(status))

    def test_guard_status_tampering(self):
        # A caller cannot promote lost evidence by changing a status label.
        artifact=dict(r1_progress=dict(step=600),component_evidence={k:dict(status='VERIFIED') for k in (*R.LINEAGE,*R.EXTERNAL,*R.NEW)})
        with self.assertRaisesRegex(ValueError,'RECORD_REQUIRED'):C.guard(artifact,['VSI-Bench'],'test')
        artifact['component_evidence']={'init_m544':dict(status='VERIFIED')}
        with self.assertRaisesRegex(ValueError,'SLOTS_DIFFER'):C.guard(artifact,['VSI-Bench'],'test')

    def test_guard_preparation_and_records(self):
        artifact=self.verified();C.guard(artifact,['VSI-Bench'],'test')
        for change in ('missing','extra','status','record','hash','pin','absent_pin','prep','registry'):
            bad=deepcopy(artifact)
            if change=='missing':bad['component_evidence'].pop('segmenter')
            if change=='extra':bad['component_evidence']['extra']=dict(status='VERIFIED',record={})
            if change=='status':bad['component_evidence']['segmenter']['status']='OTHER'
            if change=='record':bad['component_evidence']['segmenter']['record']={}
            if change=='hash':bad['component_evidence_sha256']='0'*64
            if change=='pin':bad['component_preparation']['sha256']='0'*64
            if change=='absent_pin':bad.pop('component_preparation')
            if change in ('prep','registry'):
                prep=load(bad['component_preparation']['path'])
                if change=='prep':
                    prep['component_evidence']['segmenter']['frozen']=False
                    bad['component_evidence_sha256']=digest(C.normalize(prep['component_evidence']))
                else:
                    reg=load(prep['r1_training']['registry']['path']);reg['segmenter']['record']['sha256']='0'*64
                    prep['r1_training']['registry']=write(self.root/'registry.json',reg)
                bad['component_preparation']=write(self.root/'changed_prep.json',prep)
            with self.subTest(change=change),self.assertRaises(ValueError):C.guard(bad,['VSTI'],'test')

    def test_export_binding(self):
        artifact=self.verified();status=artifact['component_evidence']
        cfg=dict(r1_training={},preparation=artifact['component_preparation'])
        self.assertEqual(C.artifact_binding(cfg,status)['component_evidence_sha256'],digest(status))
        with self.assertRaises(ValueError):C.artifact_binding(dict(r1_training={}),status)
        parent=write(self.root/'parent.json',artifact)
        self.assertEqual(C.artifact_binding(dict(init_artifact=dict(artifact=parent)),status)['component_preparation'],artifact['component_preparation'])
        self.assertEqual(C.artifact_binding({},{}),{})
