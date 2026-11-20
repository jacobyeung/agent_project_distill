"""CPU point-selection and replay tests; no model weights or GPU use."""
import contextlib
import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch
import numpy as np
import build
ROOT=build.ROOT
sys.path.insert(0,str(ROOT))

# Load the added modules together with unchanged round-1 runtime modules.
pkg=types.ModuleType('points_test_runtime');pkg.__path__=[str(ROOT/'gpkg/point_runtime'),str(ROOT/'gpkg/runtime')]
sys.modules[pkg.__name__]=pkg
points=importlib.import_module(pkg.__name__+'.points')
socket=importlib.import_module(pkg.__name__+'.point_socket')


class PointTests(unittest.TestCase):
    def test_unreviewed_api_refuses_build_and_worker(self):
        geometric=importlib.import_module(pkg.__name__+'.geometric')
        with self.assertRaisesRegex(RuntimeError,'unreviewed'):
            geometric.admit('/not-read')
        with patch.object(build.json,'loads',return_value={'reviewed':False}),self.assertRaisesRegex(ValueError,'SAM Prompt API'):
            build.build(ROOT/'out2/blocked',points='/not-read')

    def test_worker_150_points_ten_fresh_text_and_capture_exclusion(self):
        pw=importlib.import_module(pkg.__name__+'.pw')
        geometric=importlib.import_module(pkg.__name__+'.geometric')
        restricted=importlib.import_module(pkg.__name__+'.restricted')
        refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        source=Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0/POINTS_gpt-6.2-astra.json')
        raw=source.read_bytes();value=json.loads(raw)
        def module(name,**kwargs):
            m=types.ModuleType(name);m.__dict__.update(kwargs);return m
        for mismatch in (False,True):
            root=Path(tempfile.mkdtemp(prefix='points_',dir=ROOT/'work/tests'))
            (root/'2.json').write_bytes(raw)
            (root/'3.json').write_text(json.dumps(dict(points_sha256=hashlib.sha256(raw).hexdigest())))
            settings=dict(stage1_select_rule='candidates_argmax',perception_memo='verify',perception_memo_modules=['g3t'],
                          save_own_depth=False,export_dir='e',artifact_manifest='b',frames_json='0',dense_manifest='1',
                          sam3=dict(source_root='staged'))
            memo=types.SimpleNamespace(modules=frozenset(['g3t']));gen=types.SimpleNamespace(perception=types.SimpleNamespace(memo=memo))
            made=types.SimpleNamespace(generator=gen,load_info={'export':{'step':544}})
            adapter=module('h1eval.h10.parity_adapter',settings_for=lambda *a:settings,prepare_runtime=lambda x:None,
                           artifact_spec=lambda x:{},make_capped_real=lambda *a,**k:made)
            caps={r['task']['native']:dict(pin=r['mapping']['frame_binding_sha256'],frames=[dict(sha256=h) for h in value['frame_sha256_by_scene'][r['capture']]]) for r in refs}
            excluded=refs[-1]['capture'] if mismatch else None
            if mismatch:caps[refs[-1]['task']['native']]['frames'][0]['sha256']='0'*64
            def bound(task,settings):return dict(row=dict(student_input=dict(frames=caps[task['native']]['frames'])))
            parity=module('e2e_reader.parity',FRAMES='0',DENSE='1',_captures=lambda x:caps,bind_item=bound)
            stage=module('e2e_reader.stage1',name_key=lambda x:x.strip().lower())
            items=module('h1eval.items',digest=lambda v:v['anchors']['pin'] if 'anchors' in v else build.canonical(v))
            def write(path,value):
                path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value))
            cuda=types.SimpleNamespace(synchronize=lambda:None,reset_peak_memory_stats=lambda:None,max_memory_allocated=lambda:11,max_memory_reserved=lambda:22)
            modules={'orchard_h10':module('orchard_h10'),'orchard_h10.common':module('orchard_h10.common',write=write),
                     'h1eval':module('h1eval'),'h1eval.h10':module('h1eval.h10'),'h1eval.h10.parity_adapter':adapter,'h1eval.items':items,
                     'e2e_reader':module('e2e_reader',parity=parity,stage1=stage),'e2e_reader.parity':parity,'e2e_reader.stage1':stage,
                     'torch':module('torch',cuda=cuda)}
            seen=[];in_point=[];in_restricted=[]
            @contextlib.contextmanager
            def context(*args):
                in_point.append(True)
                try:yield
                finally:in_point.pop()
            @contextlib.contextmanager
            def control_context(*args):
                in_restricted.append(True)
                try:yield
                finally:in_restricted.pop()
            def replay(g,b,r):
                mode='points' if in_point else 'restricted' if in_restricted else 'text'
                self.assertEqual(memo.modules,frozenset(['g3t']) if in_point or in_restricted else frozenset())
                seen.append((r['item_id'],mode))
                return dict(schema='ground-capture-v1',item_id=r['item_id'],capture=r['capture'],source_indices=r['source_indices'],
                            geometry=None,objects=[],calls=r['calls'],prefills=1,decode_steps=0,answer_pass=False)
            config=dict(output=str(root/'r'),stop_file=str(root/'r/metadata/STOP'),settings='unused')
            with patch.dict(sys.modules,modules),patch.object(pw,'__file__',str(root/'pw.py')),patch.object(pw.w,'load_rows',return_value=refs),patch.object(pw.w,'replay',side_effect=replay),patch.object(geometric,'admit',return_value=(object,{})),patch.object(socket,'point_context',context),patch.object(restricted,'restricted_context',control_context),patch.object(pw.w,'bind_reader_root'),patch.object(pw.w,'assert_reader_root'):
                result=pw.run(config,100,clock=lambda:0)
            self.assertTrue(result['complete'],result)
            report=json.loads((root/'r/metadata/PARITY.json').read_text())
            self.assertFalse(report['parity_gate_applies'])
            expected_main=sum(r['capture']!=excluded for r in refs)
            self.assertEqual(sum(mode=='points' for _,mode in seen),expected_main)
            self.assertEqual(sum(mode=='restricted' for _,mode in seen),expected_main)
            self.assertEqual(result['restricted_completed'],150)
            self.assertEqual([key for key,mode in seen if mode=='text'],[r['item_id'] for r in refs if r['calls']][:10])
            self.assertEqual(result['completed'],150);self.assertEqual(result['repeat_completed'],10)
            self.assertEqual(report['excluded_items'],150-expected_main)

    def test_all_point_admissions_and_exact_name_mapping(self):
        refs=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        from gpkg.score_ceiling import name_key
        for name in ('POINTS_gpt-6.2-astra.json','POINTS_gemini-4-argon.json'):
            path=Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0')/name
            value=points.load(path,hashlib.sha256(path.read_bytes()).hexdigest(),refs)
            for ref in refs:
                hashes=value['frame_sha256_by_scene'][ref['capture']]
                br=points.binding(value,ref,hashes,name_key);self.assertFalse(br['excluded'])
                bad=list(hashes);bad[0]='0'*64
                self.assertTrue(points.binding(value,ref,bad,name_key)['excluded'])
        self.assertEqual(points.resolve(' Lamp ',{'lamp':{}},name_key),('lamp','normalized'))
        self.assertEqual(points.resolve('lamp',{'lamp':{},' Lamp ':{}},name_key),('lamp','exact'))
        self.assertEqual(points.resolve('LAMP',{'lamp':{},' Lamp ':{}},name_key),(None,'ambiguous'))
        self.assertEqual(points.resolve('lamps',{'lamp':{}},name_key),(None,'unmapped'))

    def test_containment_joint_fallback_boundaries(self):
        a=np.zeros((10,20),bool);a[2,15]=True;b=np.ones((10,20),bool);c=np.zeros_like(a)
        self.assertEqual(socket.choose([a,b,c],[.7,.9,.99],.5,[.75,.2])[:2],(1,False))
        self.assertEqual(socket.choose([a,c],[.7,.99],.5,[0.,1.])[:2],(1,True))
        self.assertEqual(socket.choose([b],[.7],.5,[1.,1.])[:2],(0,False))
        self.assertEqual(socket.choose([],[],.5,[0.,0.])[:2],(None,False))
        with self.assertRaises(ValueError):socket.choose([a],[float('nan')],.5,[.5,.5])

    def test_point_forward_null_skip_same_phrase_and_masks(self):
        import torch
        from gpkg.grid import resize
        # Use tensor arithmetic on CPU, with a stand-in model that records calls.
        seen=[]
        masks=torch.full((1,3,10,20),-1.)
        masks[0,0,2:4,14:17]=1;masks[0,1,0:5,10:19]=1
        raw=dict(pred_logits=torch.tensor([[.1,2.,4.]]),presence_logit_dec=torch.tensor([2.]),pred_masks=masks)
        model=types.SimpleNamespace(backbone=types.SimpleNamespace(forward_text=lambda phrase,**kw:seen.append(('text',phrase)) or {}),
                                    forward_grounding=lambda **kw:seen.append(('ground',kw)) or raw)
        tower=types.SimpleNamespace(_load=lambda:None,device='cpu',_autocast=contextlib.nullcontext,
                                    _backend=types.SimpleNamespace(model=model,find_stage='same'))
        features=types.SimpleNamespace(frames=[dict(backbone_fpn=[torch.zeros(1)]) for _ in range(32)],sizes=[(10,20)]*32)
        # Constructor verification is a separate source-pinned test, once the source is authorized.
        geometric=types.ModuleType(pkg.__name__+'.geometric');geometric.make_prompt=lambda cls,point,device:dict(point=point,device=device)
        geometric.check_detector=lambda tower:None
        student=types.ModuleType('student_pilot');student.routed_features=types.SimpleNamespace(resize=resize,SHAPE=(480,640))
        reader=types.ModuleType('e2e_reader');stage=types.ModuleType('e2e_reader.stage1');stage.name_key=lambda s:s.strip().lower()
        stage.K1_CONTRACT=dict(joint_floor=.05,cap=30)
        with patch.dict(sys.modules,{'student_pilot':student,'e2e_reader':reader,'e2e_reader.stage1':stage,geometric.__name__:geometric}):
            result=socket.detect(tower,features,' Lamp ',[[.75,.2]]+[None]*31,object)
        self.assertEqual(seen[0],('text',['lamp']));self.assertEqual(len(seen),2)
        self.assertEqual(seen[1][1]['geometric_prompt']['point'],[.75,.2])
        self.assertEqual(result[0]['chosen'],1);self.assertFalse(result[0]['fallback'])
        self.assertEqual(result[0]['mask'].shape,(240,320))
        self.assertTrue(all(x['chosen'] is None for x in result[1:]));self.assertEqual(len(result[0]['proposals']),3)

    def test_point_context_skips_head_and_records_unchanged_lifter(self):
        import torch
        from gpkg.runtime.c import unrle
        sys.path[:0]=[str(ROOT/'work/payload/b'),str(ROOT/'work/payload/tree')]
        from e2e_reader import stage1,grounding
        ref=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items'][0]
        mask=np.zeros((240,320),bool);mask[100:110,100:110]=True
        frames=[dict(point=[.3,.4],proposals=[dict(mask=socket.c.rle(np.repeat(np.repeat(mask,2,0),2,1)),score=.9,presence=.8)],chosen=0,mask=mask,fallback=False,reason='contains point') for _ in range(3)]
        frames += [dict(point=None,proposals=[],chosen=None,mask=None,fallback=False,reason='null point') for _ in range(29)]
        C=np.tile(np.eye(4),(32,1,1))
        geom=types.SimpleNamespace(K=np.tile(np.eye(3),(32,1,1)),A=np.tile(np.eye(3),(32,1,1)),C=C,
            contract=types.SimpleNamespace(camera_to_world=C,scale=1,reference_source_frame=ref['source_indices'][0],
                camera_axes='x_right_y_down_z_forward',world_axes='x_right_y_heading_z_up',depth_kind='optical_axis',pixel_centres='edge_origin_half',gravity_up=[0,0,1]),
            frame_map=types.SimpleNamespace(source_indices=ref['source_indices']),depth_scale_count=1,pose_scale_count=1,
            depth_grid=np.zeros((32,2,2)),identity='synthetic',has=lambda f:True,
            lift=lambda frame,uv,mode:(np.c_[uv/1000,np.ones(len(uv))],np.c_[uv/1000,np.ones(len(uv))],np.zeros(len(uv))))
        head=types.SimpleNamespace(with_null=lambda *a:(_ for _ in ()).throw(AssertionError('selector entered')))
        with socket.point_context(None,ref,{'lamp':{str(s):[.3,.4] for s in ref['source_indices']}},object):
            with socket.w.Capture(stage1.StageOne,grounding) as captured:
                obj=stage1.StageOne(lambda name:frames,head,geom)
                sock=grounding.StageOneSocket(obj.propose,obj.select,(240,320),32)
                entries=sock('lamp');lift=grounding.lift_bestspread('lamp',entries[0]['masks'],geom)
        self.assertEqual(lift['frames'],[1,2,3]);self.assertEqual(captured.objects[0]['lift']['frame_count'],3)
        self.assertEqual(captured.objects[0]['selector']['skipped'],'point prompts')
        self.assertIs(stage1.StageOne, socket.original_stage if hasattr(socket,'original_stage') else stage1.StageOne)
        self.assertEqual(len(captured.objects[0]['selected_masks']),3)


if __name__=='__main__':unittest.main()
