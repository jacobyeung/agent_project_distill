from pathlib import Path
import os,unittest
from copy import deepcopy
from tests.test_r1_build20 import Review20
from student_pilot import r1_components as C,r1_handover as H
from student_pilot.p3_provenance import digest,load
from tests.test_r2_build_n1 import write

class Edges20(Review20):
    def test_official_export_deferred(self):
        pin=write(self.root/'parent.json',dict(component_evidence={'init_m544':dict(status='DEFERRED')}))
        with self.assertRaisesRegex(ValueError,'DEFERRED'):
            C.artifact_status(dict(init_artifact=dict(artifact=pin),r2_evaluation=True))

    def test_composite_donor_producer(self):
        from launch_r1 import p_export_receipt as E
        from student_pilot import r1_persisted as P
        from student_pilot.p3_provenance import file_pin
        native=Path(os.environ['R2_LANE_ROOT'])/'work/build20/proofs/native/400'
        source=load(native/'config.json');prep=load(native/'preparation.json')
        original=source['streams']['pose'];receipt=load(original['path'])
        spec=write(self.root/'mix.json',dict(schema='c1-pose-mix-v1',division=receipt['inputs']['division'],
                    sources=[dict(kind='rows',receipt=original,frame_prefix=None)]))
        order=write(self.root/'order.json',[[0,0]])
        source['streams']['pose']=spec
        identity=H.export_identity(source);prep['config_sha256']=identity
        prep['streams']['pose']=dict(receipt=spec,kind='mix',division=receipt['inputs']['division'],count=1,order=order,
            sources=[dict(kind='rows',receipt=original,frame_prefix=None,count=1,database=receipt['database'])])
        source['preparation']=write(self.root/'prep.json',prep)
        bound=load(native/'binding.json');bound.update(config_sha256=identity,preparation=source['preparation'])
        run=dict(config=write(self.root/'source.json',source),preparation=source['preparation'],binding=write(self.root/'binding.json',bound))
        artifact=load(native/'export/artifact.json');artifact['config_sha256']=identity
        ap=write(self.root/'artifact.json',artifact)
        hp=E.produce(run,ap,self.root/'receipt.json',job_id='6ed2c7aa',trainer_commit=bound['trainer_commit'])
        n=load(native/'request_config.json');n['init_artifact']['artifact']=ap
        n['r1_training'].update(p_run=run,handover_receipt=hp,persisted_files={},proof_mode='q',donor_config_sha256=identity)
        with P.proof_scope():
            donor,recipe,actual,plan=H.donor(n,artifact)
        self.assertEqual(plan['indices']['pose'],order['sha256'])
        self.assertEqual(actual['stores']['pose'],H.stream_identity(load(spec['path']),'pose'))

    def test_descendant_empty_map(self):
        a=self.verified();a.pop('r1_progress');a['component_evidence']={}
        with self.assertRaisesRegex(ValueError,'MISSING'):C.guard(a,['VSI-Bench'],'test')
        a.pop('component_preparation')
        with self.assertRaisesRegex(ValueError,'MISSING'):C.guard(a,['VSI-Bench'],'test')

    def test_verified_record_conflict(self):
        a=self.verified();prep=load(a['component_preparation']['path'])
        prep['component_evidence']['segmenter']['extra']='altered'
        a['component_evidence']=C.normalize(prep['component_evidence']);a['component_evidence_sha256']=digest(a['component_evidence'])
        a['component_preparation']=write(self.root/'different.json',prep)
        with self.assertRaisesRegex(ValueError,'RECORD_MISMATCH'):C.guard(a,['VSI-Bench'],'test')
        with self.assertRaises(ValueError):C.artifact_binding(dict(r1_training={},preparation=a['component_preparation']),{'x':dict(status='DEFERRED')})

    def test_clip_and_plain(self):
        pin=dict(path='/opaque',sha256='a'*64)
        s=dict(kind='c1r_clips',clips_plan=pin,dense_plan=pin,teacher=pin,cache_root='/cache',model=pin,layout='spread',count=2)
        spec=dict(schema='c1-pose-mix-v1',sources=[s])
        prepared=dict(kind='mix',sources=[dict(s)],count=2,order=write(self.root/'order.json',[[0,0],[0,1]]))
        self.assertEqual(H.prepared_stream_identity(spec,prepared,'pose')[1],2)
        prepared['kind']='other'
        with self.assertRaises(ValueError):H.prepared_stream_identity(spec,prepared,'pose')
        self.assertEqual(H.prepared_stream_identity(dict(database=pin,count=2),dict(database=pin),'pose'),('a'*64,2))
        with self.assertRaises(ValueError):H.prepared_stream_identity(dict(database=pin,count=2),{},'pose')
