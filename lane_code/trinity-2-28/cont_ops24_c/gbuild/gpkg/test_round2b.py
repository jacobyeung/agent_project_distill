"""Source-backed point API, restricted selection, and delivered import checks."""
import ast
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
from import_smoke import smoke
from test_points import pkg,socket

ROOT=build.ROOT
geometric=importlib.import_module(pkg.__name__+'.geometric')
restricted=importlib.import_module(pkg.__name__+'.restricted')


def temp():return Path(tempfile.mkdtemp(prefix='r2b_',dir=ROOT/'work/tests'))


def real_prompt(filename=None):
    import torch
    source=ROOT/'sam3_ref/geometry_encoders.py'
    tree=ast.parse(source.read_text())
    node=next(n for n in tree.body if getattr(n,'name',None)=='Prompt')
    ns=dict(torch=torch,__name__='sam3.model.geometry_encoders')
    # The provided reference lacks its relative dependencies. Execute the
    # complete, unchanged real Prompt class rather than inventing a double.
    exec(compile(ast.Module([node],type_ignores=[]),str(filename or source),'exec'),ns)
    return ns['Prompt']


class Round2bTests(unittest.TestCase):
    def test_real_prompt_constructor_and_encoder_xy(self):
        import torch
        pin=json.loads((ROOT/'gpkg/point_runtime/PROMPT_API.json').read_text())
        Prompt=real_prompt();geometric.verify_signature(Prompt,pin)
        prompt=geometric.make_prompt(Prompt,[.75,.25],'cpu')
        self.assertEqual(tuple(prompt.point_embeddings.shape),(1,1,2))
        self.assertEqual(prompt.point_embeddings.tolist(),[[[.75,.25]]])
        self.assertEqual(prompt.point_mask.tolist(),[[False]])
        self.assertEqual(prompt.point_labels.tolist(),[[1]])
        self.assertEqual(prompt.point_labels.dtype,torch.long)
        self.assertEqual(prompt.point_embeddings.dtype,torch.float32)
        self.assertEqual(prompt.box_embeddings.shape,(0,1,4))
        self.assertEqual(Prompt(point_embeddings=prompt.point_embeddings).point_labels.tolist(),[[1]])
        for point in ([1.01,.1],[float('nan'),.5],[.5]):
            with self.assertRaises(ValueError):geometric.make_prompt(Prompt,point,'cpu')
        tree=ast.parse((ROOT/'sam3_ref/geometry_encoders.py').read_text())
        cls=next(n for n in tree.body if getattr(n,'name',None)=='SequenceGeometryEncoder')
        fn=next(n for n in cls.body if getattr(n,'name',None)=='_encode_points')
        ns=dict(torch=torch);exec(compile(ast.Module([fn],type_ignores=[]),'real_encoder','exec'),ns)
        encoder=types.SimpleNamespace(points_direct_project=None,points_pos_enc_project=None,
              points_pool_project=torch.nn.Identity(),d_model=1,label_embed=lambda labels:torch.zeros(1,1,1))
        # (x=.75,y=.25) is the top-right pixel center of this 2x2 grid.
        result,_=ns['_encode_points'](encoder,prompt.point_embeddings,prompt.point_mask,
                                     prompt.point_labels,torch.tensor([[[[1.,2.],[3.,4.]]]]))
        self.assertEqual(result.item(),2.)

    def test_staged_api_signature_hash_and_disabled_encoder_refusals(self):
        pin=json.loads((ROOT/'gpkg/point_runtime/PROMPT_API.json').read_text());root=temp()
        (root/'4.json').write_text(json.dumps(pin))
        for name in pin['source_files']:
            path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes((ROOT/'sam3_ref'/path.name).read_bytes())
        path=root/'sam3/model/geometry_encoders.py';Prompt=real_prompt(path)
        module=types.ModuleType('sam3.model.geometry_encoders');module.__file__=str(path);module.Prompt=Prompt
        with patch.dict(sys.modules,{module.__name__:module}),patch.object(geometric,'__file__',str(root/'geometric.py')):
            admitted,receipt=geometric.admit(root)
            self.assertIs(admitted,Prompt);self.assertEqual(receipt['positive_label'],1)
            path.write_text(path.read_text()+'\n')
            with self.assertRaisesRegex(RuntimeError,'source differs'):geometric.admit(root)
        with self.assertRaisesRegex(RuntimeError,'signature differs'):
            geometric.verify_signature(lambda point_embeddings=None:None,pin)
        with self.assertRaisesRegex(RuntimeError,'disabled'):
            geometric.check_detector(types.SimpleNamespace(_backend=types.SimpleNamespace(model=object())))

    def test_restricted_raw_member_mask_and_original_logits(self):
        import torch
        sys.path[:0]=[str(ROOT/'work/payload/b'),str(ROOT/'work/payload/tree')]
        from e2e_reader import stage1,grounding
        ref=json.loads((ROOT/'kit2/kit/rerun2/items544.json').read_text())['items'][0]
        mask=np.zeros((4,6),bool);mask[1,4]=True
        other=np.zeros_like(mask)
        proposals=[dict(id='1:0',frame=1,mask=socket.c.rle(mask)),dict(id='1:1',frame=1,mask=socket.c.rle(other))]
        record=dict(name=' Lamp ',proposals=proposals,linked_tracks=[dict(id='a',members=['1:0']),dict(id='b',members=['1:1'])],
                    candidates=[dict(id='a',masks={'1':socket.c.rle(mask)}),dict(id='b',masks={'1':socket.c.rle(other)})],
                    selector={},selected_masks={})
        frame_points=[[.75,.25]]+[None]*31
        self.assertEqual(restricted.eligible_tracks(record,frame_points),[0])
        values={'lamp':{str(s):point for s,point in zip(ref['source_indices'],frame_points)}}
        seen=[]
        def logits(x,unused,name):seen.append(x.clone());return torch.tensor([1.,20.,100.])
        obj=stage1.StageOne.__new__(stage1.StageOne)
        obj.rule='candidates_argmax';obj.head=types.SimpleNamespace(with_null=logits);obj.diagnostics={}
        inputs=dict(name=' Lamp ',x=torch.zeros((2,58)))
        original=stage1.StageOne.select
        with restricted.restricted_context(None,ref,values):
            with restricted.w.Capture(stage1.StageOne,grounding) as cap:
                cap.by_name[' Lamp ']=record
                self.assertEqual(obj.select(inputs),0)
                self.assertEqual(record['selector']['eligible_indices'],[0])
                self.assertEqual(record['selector']['slots'],[1.,20.,100.])
                self.assertEqual(record['selected_masks'],record['candidates'][0]['masks'])
                values['lamp'][str(ref['source_indices'][0])]=None
                self.assertEqual(obj.select(inputs),-1)
        self.assertIs(stage1.StageOne.select,original)
        self.assertEqual([tuple(x.shape) for x in seen],[(2,58),(2,58)])

    def test_point_k1_floor_cap_and_stable_ties(self):
        import torch
        sys.path[:0]=[str(ROOT/'work/payload/b'),str(ROOT/'work/payload/tree')]
        from e2e_reader import stage1
        raw=dict(pred_logits=torch.tensor([[2.]*34+[-20.]]),presence_logit_dec=torch.tensor([2.]),
                 pred_masks=torch.ones(1,35,2,2))
        model=types.SimpleNamespace(backbone=types.SimpleNamespace(forward_text=lambda *a,**kw:{}),
              forward_grounding=lambda **kw:raw,geometry_encoder=types.SimpleNamespace(points_direct_project=object()))
        tower=types.SimpleNamespace(_load=lambda:None,device='cpu',_autocast=contextlib.nullcontext,
                                    _backend=types.SimpleNamespace(model=model,find_stage='same'))
        features=types.SimpleNamespace(frames=[dict(backbone_fpn=[torch.zeros(1)])]*32,sizes=[(2,2)]*32)
        result=socket.detect(tower,features,'lamp',[[.5,.5]]+[None]*31,real_prompt())
        self.assertEqual(len(result[0]['proposals']),stage1.K1_CONTRACT['cap'])
        self.assertEqual(result[0]['chosen'],0)
        raw['pred_logits'][:]=-20
        result=socket.detect(tower,features,'lamp',[[.5,.5]]+[None]*31,real_prompt())
        self.assertEqual(result[0]['proposals'],[]);self.assertIsNone(result[0]['chosen'])

    def test_full_three_arm_scoring_sparse_visibility_and_optional_t1(self):
        from gpkg.runtime.c import Writer
        from gpkg.score_ceiling import score,sparse_visibility
        root=temp();manifest=ROOT/'kit2/kit/rerun2/items544.json';refs=json.loads(manifest.read_text())['items']
        path=root/'capture.gz';writer=Writer(path)
        for pass_id,arm,selected in [(0,'points',refs),(2,'restricted_selector',refs),(1,'text_noise',[r for r in refs if r['calls']][:10])]:
            for ref in selected:
                writer.append(dict(schema='ground-capture-v1',item_id=ref['item_id'],capture=ref['capture'],source_indices=ref['source_indices'],
                              pass_index=pass_id,arm=arm,calls=ref['calls'],objects=[],geometry=None))
        writer.close();receipt=dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)
        result=score(manifest,path,receipt,path,receipt)
        self.assertEqual(result['denominator'],150);self.assertEqual(result['sparse_denominator'],93)
        self.assertEqual(result['statistics']['resampled_rooms'],46)
        self.assertEqual(result['statistics']['draws'],10000)
        self.assertEqual(result['statistics']['seed'],20261120)
        for group in result['statistics']['groups'].values():
            if not group['items']:continue
            for metric in ('point_minus_baseline','restricted_minus_baseline','T1_minus_baseline'):
                self.assertEqual(group['metrics'][metric]['ci95'],[0.,0.])
        self.assertEqual(len(result['text_noise']),10)
        self.assertEqual(result['statistics']['groups']['null_without_printed_sparse']['items'],7)
        ref=refs[0];scene=dict(source_indices=ref['source_indices'],valid=[True]*32,orientation={'status':'U'},targets={})
        target=dict(binding={'status':'bound'},instance_id=1,visible_pixels=[0]*32)
        scene['targets'][ref['item_id']+':lamp']=target
        for count,expected in ((0,'0'),(1,'1-2'),(2,'1-2'),(3,'>=3')):
            target['visible_pixels']=[1]*count+[0]*(32-count)
            self.assertEqual(sparse_visibility(ref,'lamp',{ref['capture']:scene})['group'],expected)
        self.assertEqual(sparse_visibility(ref,'lamp',{})['group'],'no GT')
        (root/'SYNTHETIC_SCORE.json').write_text(json.dumps(result,indent=2)+'\n')

    def test_real_deliveries_import_and_point_seals(self):
        root=temp();legacy=smoke(ROOT/'out/delivery.tgz','legacy')
        self.assertNotEqual(legacy['returncode'],0);self.assertIn("cannot import name 'parity'",legacy['stderr'])
        self.assertEqual(legacy['operator']['returncode'],0,legacy)
        t1=build.build(root/'t1');fixed=smoke(root/'t1/delivery.tgz')
        self.assertEqual(fixed['returncode'],0,fixed)
        point_file=Path('/scratch/jjyeung/orch_n30/nvkey1/work/c0/POINTS_gpt-6.2-astra.json')
        info=build.build(root/'points',points=point_file);self.assertNotEqual(info['token'],t1['token'])
        result=smoke(root/'points/delivery.tgz');self.assertEqual(result['returncode'],0,result)
        outer={m.name:d for m,d in build.read_tar((root/'points/delivery.tgz').read_bytes())}
        payload={m.name:d for m,d in build.read_tar(outer['0.tgz'])};plan=json.loads(payload['9.json'])
        for name,pin in plan['payload_pins'].items():self.assertEqual(pin['sha256'],build.sha(payload[name]))
        self.assertEqual(payload['g/2.json'],point_file.read_bytes())
        self.assertIn(b'from g.pw import run',payload['orchard_h10/entry.py'])
        self.assertIn(b'admit(runtime_settings',outer['a/6.py'])
        for name,raw in payload.items():
            if name.startswith('g/') and name.endswith('.py'):compile(raw,name,'exec')
        (root/'IMPORTS.json').write_text(json.dumps(dict(legacy=legacy,T1=fixed,points=result),indent=2)+'\n')

    def test_foreign_reader_refusal(self):
        from gpkg.runtime.w import assert_reader_root
        module=types.ModuleType('e2e_reader.bad');module.__file__='/tmp/foreign.py'
        with patch.dict(sys.modules,{'e2e_reader.bad':module}),self.assertRaises(ImportError):
            assert_reader_root(ROOT/'work/payload/b')


if __name__=='__main__':unittest.main()
