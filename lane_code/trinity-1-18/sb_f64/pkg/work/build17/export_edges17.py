"""Exercise each export-only producer rejection with native export inputs."""
from copy import deepcopy
from pathlib import Path
import os
from unittest.mock import patch
from tests.test_r1_export17 import Export17
from tests.test_r2_build_n1 import write
from student_pilot.p3_provenance import load
from launch_r1 import p_export_receipt as E


class ProducerEdges(Export17):
    def test_manifest_refusals(self):
        root,cfg,run,_,_=self.fixture()
        artifact=load(cfg['init_artifact']['artifact']['path'])
        weights=load(artifact['full_weights']['path'])
        parent=Path(artifact['full_weights']['path']).parent
        cases=[]
        value=deepcopy(weights);value['files'][0]['name']='../outside'
        cases.append(('escape',value,'PATH_ESCAPE'))
        value=deepcopy(weights);value['files'][0]['sha256']='f'*64
        cases.append(('hash',value,'FILE_MISMATCH'))
        value=deepcopy(weights);value['files'].append(deepcopy(value['files'][0]))
        cases.append(('duplicate',value,'DUPLICATE_FILE'))
        value=deepcopy(weights);value['files']=[]
        cases.append(('empty',value,'STREAMS_OR_WEIGHTS_MISSING'))
        for name,value,refusal in cases:
            bad=deepcopy(artifact)
            bad['full_weights']=write(parent/'edge_manifest.json',value)
            pin=write(root/'edge_artifact.json',bad)
            with self.subTest(name=name),self.assertRaisesRegex(ValueError,refusal):
                E.collect(run,pin)

    def test_step_and_stop_refusals(self):
        root,cfg,run,_,_=self.fixture()
        artifact=load(cfg['init_artifact']['artifact']['path'])
        artifact['step']=401
        with self.assertRaisesRegex(ValueError,'STEP_NOT_MILESTONE'):
            E.collect(run,write(root/'edge_artifact.json',artifact))
        source=load(run['config']['path']);source['h1']['stop_after_step']=True
        bad=deepcopy(run);bad['config']=write(root/'edge_config.json',source)
        with self.assertRaisesRegex(ValueError,'STOP_INVALID'):
            E.collect(bad,cfg['init_artifact']['artifact'])

    def rebind_preparation(self,root,run,prep):
        result=deepcopy(run)
        result['preparation']=write(root/'edge_preparation.json',prep)
        source=load(run['config']['path']);source['preparation']=result['preparation']
        result['config']=write(root/'edge_config.json',source)
        bound=load(run['binding']['path']);bound['preparation']=result['preparation']
        result['binding']=write(root/'edge_binding.json',bound)
        return result

    def test_stream_refusal_and_index_closure(self):
        root,cfg,run,_,_=self.fixture()
        prep=load(run['preparation']['path'])
        name=next(iter(prep['streams']))
        prep['streams'][name]['indices']=write(root/'edge_indices.json',[0])
        updated=self.rebind_preparation(root,run,prep)
        closure,_,_,_=E.collect(updated,cfg['init_artifact']['artifact'])
        self.assertEqual(closure['indices/'+name],prep['streams'][name]['indices'])
        prep['streams'][name]['receipt']['sha256']='f'*64
        bad=self.rebind_preparation(root,run,prep)
        with self.assertRaisesRegex(ValueError,'STREAM_RECEIPT_MISMATCH'):
            E.collect(bad,cfg['init_artifact']['artifact'])

    def test_cli(self):
        root,cfg,run,_,_=self.fixture()
        run_pin=write(root/'edge_run.json',run)
        with patch.dict(os.environ,SLURM_JOB_ID='fixture'):
            receipt=E.main(['--run-pins',run_pin['path'],'--artifact',cfg['init_artifact']['artifact']['path'],
                '--output',str(root/'edge_h.json'),'--trainer-commit','fixture'])
        self.assertEqual(load(receipt['path'])['schema'],E.SCHEMA)
