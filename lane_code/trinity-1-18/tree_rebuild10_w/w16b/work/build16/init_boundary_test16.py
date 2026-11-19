"""Prove the persisted-only metadata boundary without reading checkpoint shards."""
import unittest
from pathlib import Path
import os
from tests.test_r1_build16 import Build16
from tests.test_r2_build_n1 import write
from student_pilot import r1_persisted as P, r1_handover as H
from student_pilot.p3_provenance import load,pinned,file_pin

class InitializationBoundary(unittest.TestCase):
    setUp=Build16.setUp
    tearDown=Build16.tearDown
    root=Build16.root
    fixture=Build16.fixture

    def test_real_inputs_refuse_unstaged_runtime_inputs(self):
        from launch_r1.production_proof import run
        L=Path(os.environ['R2_LANE_ROOT']);B=L/'work/build16'
        cfg=load(B/'inputs/kit_config.json')
        root=self.root('real_room_boundary')
        room=write(root/'room_audit.json',dict(complete=False,unknown_overlap='unresolved',
            row_sources=cfg['r1_training']['row_sources'],remove_files=cfg['remove_files'],
            evidence=file_pin(B/'INPUTS.json')))
        request=dict(config=file_pin(B/'inputs/kit_config.json'),room_audit=room,
            staged_pins=[file_pin(B/'inputs/kit_config.json'),cfg['r1_training']['mix'],room])
        result=run(request,root)
        self.assertEqual(result['status'],'REFUSE')
        self.assertIn('R1_PROOF_NATIVE_ROUTING_REQUIRED',result['refusal'])

    def test_model_metadata_is_outside_persisted_closure(self):
        root,cfg,_,_=self.fixture(400)
        admission=P.admission(cfg,weights=True)
        self.assertEqual(admission['absolute_resume_step'],400)
        value=cfg['r1_training'];receipt=load(value['handover_receipt']['path'])
        with P.scope(admission['paths']):
            source=load(pinned(value['p_run']['config']))
            prep=load(pinned(source['preparation']))
        manifest=prep['model']
        self.assertNotIn(manifest['sha256'],{v['sha256'] for v in receipt['pins'].values()})
        # Simulate the N host: the P-local model manifest is absent. No bytes change.
        paths=dict(admission['paths']);paths[manifest['sha256']]=str(root/'absent_manifest')
        with P.scope(paths):
            with self.assertRaisesRegex(ValueError,'P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED'):
                H.donor_meta_model(source)
        write(root/'INIT_BOUNDARY.json',dict(metadata_handover='ADMIT',absolute_resume_step=400,
            full_initialization='REFUSE',reason='P_EXPORT_TOPOLOGY_METADATA_UNVERIFIED',
            required_manifest=manifest,in_direct_receipt_closure=False,
            qualification='Synthetic native export. Missing P model metadata stands in for its absence on N; no real export supplied.'))
