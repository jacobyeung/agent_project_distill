"""Unpatched negative tests for leg-wasting row, init, version and export failures."""
import copy, json, os, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
import torch
from safetensors.torch import save_file
from student_pilot import carrier_c1_run as run, full_ft
from student_pilot.p3_provenance import file_pin
from student_pilot.trace_format313 import bind_generate
from tests.test_carrier_c1_final import final_fixture

class Guards(unittest.TestCase):
    def directory(self):return Path(tempfile.mkdtemp(dir=os.environ['LANE_TEST_OUTPUT']))
    def test_dropped_row_field_cannot_substitute(self):
        model,batch,target=final_fixture()
        class Rows:
            def count(self,stream):return 2
            def get(self,stream,index):
                b=dict(batch)
                if index==0:b.pop('aux_camera_positions')
                return b,target,{}
        for call in (lambda:run.fetch(Rows(),'pose',0,model),lambda:run.fetch_nominal(Rows(),'pose',[0],model)):
            with self.assertRaisesRegex(ValueError,'no substitution'):call()
        self.assertEqual(run.fetch(Rows(),'pose',1,model)[2]['index'],1)
    def test_requested_own_values_cannot_keep_gt(self):
        model,batch,_=final_fixture()
        class Rows:
            def row(self,stream,index):return {'routing':{}},{}
        with self.assertRaisesRegex(ValueError,'refusing GT fallback'):
            run.own_values(model,Rows(),batch,{},0,(True,True),torch.device('cpu'))
    def test_program_version_cannot_override_checkpoint(self):
        model=SimpleNamespace(trace_program_version='3.13')
        def decoder(model,processor,batch,**kwargs):return 'executed'
        bound=bind_generate(decoder)
        self.assertEqual(bound(model,None,{}),'executed')
        with self.assertRaisesRegex(ValueError,'trace_program_version_mismatch'):
            bound(model,None,{},trace_program_version='3.14')
        model.trace_program_version='3.14'
        with self.assertRaisesRegex(ValueError,'trace_program_version_missing'):bound(model,None,{})
        session=SimpleNamespace(spec_version='3.14',execute=lambda call:'ok')
        self.assertEqual(bound(model,None,{},trace_session=session),'executed')
    def artifact(self,model,root,geometry=None,drop=()):
        state={k:v for k,v in model.auxiliary_heads.state_dict().items() if not k.startswith(drop)}
        torch.save(state,root/'heads.pt')
        value=dict(schema='carrier-c1-artifact-v1',pose_backing='lm_final_norm',placement=model.carrier_placement,
            frame_layout=model.frame_layout,carrier_position_policy=model.carrier_position_policy,training_mode='final',heads=file_pin(root/'heads.pt'))
        if geometry:value['geometry_online']=geometry
        (root/'artifact.json').write_text(json.dumps(value))
        return dict(artifact=file_pin(root/'artifact.json'),lm='base',heads=['pose','frame_embeddings','depth'])
    def test_missing_trained_connector_refuses(self):
        model,_,_=final_fixture()
        model.auxiliary_heads.pose.cam_token_connector=torch.nn.Linear(3,3)
        model.geometry_online={'mode':'frozen'}
        spec=self.artifact(model,self.directory(),model.geometry_online,('pose.cam_token_connector.',))
        with self.assertRaisesRegex(ValueError,'init heads differ'):run.init_from_artifact(model,spec)
    def test_warm_fusion_must_be_selected(self):
        model,_,_=final_fixture();model.auxiliary_heads.patch_fusion=torch.nn.Linear(3,3)
        model.geometry_online={'mode':'frozen','patch_fusion':{'align_steps':0}}
        spec=self.artifact(model,self.directory(),model.geometry_online)
        with self.assertRaisesRegex(ValueError,'requires patch_fusion'):run.init_from_artifact(model,spec)
        spec['heads'].append('patch_fusion')
        self.assertGreater(run.init_from_artifact(model,spec)['head_tensors'],0)
    def test_wrong_artifact_refuses(self):
        model,_,_=final_fixture();root=self.directory()
        spec=self.artifact(model,root)
        spec['artifact']['path']=str(root/'does_not_exist.json')
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):run.init_from_artifact(model,spec)
    def test_existing_wrong_artifact_refuses(self):
        model,_,_=final_fixture();root=self.directory()
        spec=self.artifact(model,root)
        artifact=json.loads((root/'artifact.json').read_text());artifact['schema']='wrong-artifact-v1'
        (root/'artifact.json').write_text(json.dumps(artifact));spec['artifact']=file_pin(root/'artifact.json')
        with self.assertRaisesRegex(ValueError,'not a C1 milestone'):run.init_from_artifact(model,spec)
    def test_duplicate_shard_tensor_cannot_hide_missing_tensor(self):
        model=torch.nn.Module();model.a=torch.nn.Linear(2,2,bias=False);model.b=torch.nn.Linear(2,2,bias=False)
        root=self.directory()
        full_ft.save_export({n:p.detach().to(torch.bfloat16) for n,p in model.named_parameters()},root/'weights',{}, {})
        root=root/'weights';manifest=json.loads((root/full_ft.EXPORT_MANIFEST).read_text())
        files=[]
        for name in ('one.safetensors','two.safetensors'):
            save_file({'a.weight':torch.ones(2,2,dtype=torch.bfloat16)},str(root/name))
            files.append(dict(name=name,sha256=full_ft.sha256_file(root/name),bytes=(root/name).stat().st_size,tensors=1))
        index={'weight_map':{'a.weight':'one.safetensors','b.weight':'two.safetensors'}}
        path=root/manifest['index']['name'];path.write_text(json.dumps(index))
        manifest['files']=files;manifest['index']['sha256']=full_ft.sha256_file(path)
        (root/full_ft.EXPORT_MANIFEST).write_text(json.dumps(manifest))
        for load in (full_ft.load_export,run.load_export_masters):
            model.to(torch.bfloat16 if load is full_ft.load_export else torch.float32)
            with self.assertRaisesRegex(ValueError,'shard membership'):load(model,root)

if __name__=='__main__':unittest.main()
