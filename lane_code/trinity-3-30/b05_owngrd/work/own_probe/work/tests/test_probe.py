import ast
import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.nn import functional as F

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work'),str(ROOT/'out')]
from own_feats import pack_qwen,unpack_qwen,pool,FrozenEncoder,NameEmbedder
from own_feats.core import pixels
from probe_heads import Selector,listwise_loss,IdentityProbe,contrastive_loss,MaskProbe,PresenceProbe,parameter_gate
from probe_common import gate,mean_ci,auroc,rules
from card import rules_for,choose
torch.set_num_threads(4)


class RoomTests(unittest.TestCase):
    def test_parsing(self):
        self.assertEqual(gate.room('d1','scene0400_01'),'scannet/scene0400')
        self.assertEqual(gate.room('scannetppv2','09c1414f1b'),'scannetpp/09c1414f1b')
        self.assertEqual(gate.room('d3','41159521'),'arkitscenes/venue381879')
        self.assertEqual(gate.room('arkitscenes','43649472'),'arkitscenes/43649472')
        with self.assertRaises(gate.RoomViolation):gate.room('d3','9999999999')

    def test_all_frames_excluded(self):
        for s in gate.authority()['frames32_scenes']:self.assertTrue(gate.is_evaluation_room(*s.split('/')))

    def test_nested_paths_and_aliases(self):
        clean=gate.authority()['clean_scenes'][0].split('/')[1]
        paths=[f'/scratch/prefix{clean}suffix/0.jpg', '/scratch/frames32/scannetpp__09c1414f1b/0.jpg',
               '/scratch/frames32/SCANNETPP__09c1414f1b/0.jpg','/scratch/frames32/scannet++__09c1414f1b/0.jpg',
               '/scratch/frames32/arkitscenes__41069025/0.jpg']
        for path in paths:
            for extra in [dict(mask_ref=path),dict(paths=[path]),dict(nested=dict(unusual=path))]:
                with self.subTest(path=path,extra=extra),self.assertRaises(gate.RoomViolation):
                    gate.check_row(dict(scene='scannet/scene0400_01',split='train',**extra))

    def test_manifest_and_injection(self):
        rows=gate.read_manifest(ROOT/'out/b2_manifest.jsonl')
        self.assertEqual(len(rows),6560)
        with self.assertRaises(gate.RoomViolation):gate.read_manifest(ROOT/'out/tuning_manifest.jsonl')
        self.assertEqual(len(gate.read_manifest(ROOT/'out/tuning_manifest.jsonl','tuning')),992)
        row=dict(rows[0]);row['scene']='scannet/scene0019_00';row['dataset']='scannet';row['scan']='scene0019_00'
        row['room']='scannet/scene0019'
        with self.assertRaises(gate.RoomViolation):gate.check_row(row)
        row=dict(rows[0]);row['authority_sha256']='0'*64
        with self.assertRaises(gate.RoomViolation):gate.check_row(row)


class FeatureTests(unittest.TestCase):
    def test_pack_row_major_and_duplicate(self):
        x=torch.arange(2*3*8*12).reshape(2,3,8,12).float()
        packed,grid=pack_qwen(x,patch=2,temporal=2,merge=2)
        p=packed.reshape(2,2,3,2,2,3,2,2,2)
        recovered=p.permute(0,6,5,1,3,7,2,4,8).reshape(2,2,3,8,12)
        self.assertTrue(torch.equal(recovered[:,0],x));self.assertTrue(torch.equal(recovered[:,1],x))
        raster=torch.arange(48).reshape(2,4,6,1)
        grouped=raster.reshape(2,2,2,3,2,1).permute(0,1,3,2,4,5).reshape(48,1)
        self.assertTrue(torch.equal(unpack_qwen(grouped,grid),raster))

    def test_pool_onehot_empty_and_bilinear(self):
        m=torch.eye(4).reshape(1,2,2,4);masks=torch.eye(4).reshape(4,2,2)
        self.assertTrue(torch.equal(pool([m],masks),torch.eye(4)))
        self.assertTrue(torch.equal(pool([m],torch.zeros(1,2,2)),torch.zeros(1,4)))
        # Uniform weights at a different resolution average every basis equally.
        self.assertTrue(torch.allclose(pool([m,m],torch.ones(1,4,4)),torch.full((1,8),.5)))
        with self.assertRaises(ValueError):pool([m],torch.full((1,2,2),-1.))

    def test_tiny_vit_hooks_and_mdg_grid(self):
        from transformers.models.qwen3_5.configuration_qwen3_5 import Qwen3_5VisionConfig
        from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
        cfg=Qwen3_5VisionConfig(depth=4,hidden_size=32,intermediate_size=64,num_heads=4,patch_size=2,
                              temporal_patch_size=2,spatial_merge_size=2,out_hidden_size=32,num_position_embeddings=16)
        cfg._attn_implementation='sdpa';torch.manual_seed(17);model=Qwen3_5VisionModel(cfg).eval()
        enc=FrozenEncoder(model,'qwen_vit',taps=(1,2,3,4))
        im=Image.fromarray(np.arange(16*24*3,dtype=np.uint8).reshape(16,24,3))
        maps=enc.encode([im],(16,24),cpu_dtype=torch.float32)
        store={};hooks=[model.blocks[k].register_forward_hook(lambda m,a,o,k=k:store.setdefault(k,o)) for k in range(4)]
        x,grid=pack_qwen(pixels([im],(16,24)),patch=2)
        with torch.no_grad():model(x,grid)
        for hook in hooks:hook.remove()
        # Execute the unchanged reference utility, not a duplicate implementation.
        p=ROOT.parent/'mdg_build/work/c1mix_mdg/student_pilot/point_depth_head.py'
        node=next(n for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef) and n.name=='vit_grids_by_row')
        ns={'torch':torch};exec(compile(ast.Module(body=[node],type_ignores=[]),str(p),'exec'),ns)
        for k,m in enumerate(maps):
            self.assertEqual(m.shape,(1,8,12,32))
            self.assertTrue(torch.equal(m,ns['vit_grids_by_row'](store[k],grid,2)[0]))
        self.assertFalse(any(p.requires_grad for p in enc.model.parameters()))

    def test_name_rows_deterministic(self):
        embed=NameEmbedder();a=embed(['chair','kitchen cabinet']);b=embed(['chair','kitchen cabinet'])
        self.assertTrue(torch.equal(a.tokens,b.tokens));self.assertTrue(torch.equal(a.mean,b.mean))
        self.assertEqual(a.rows_sha256,b.rows_sha256);self.assertEqual(a.tokens.shape[-1],4096)


class ProbeTests(unittest.TestCase):
    def test_separable_t1_and_shuffle_chance(self):
        torch.manual_seed(17);model=Selector(8,name_dim=8,dim=32)
        x=torch.eye(8);opt=torch.optim.Adam(model.parameters(),lr=.03)
        for _ in range(180):
            opt.zero_grad();loss=torch.stack([listwise_loss(model(x,x[j].expand(8,-1)),torch.arange(8)==j) for j in range(8)]).mean()
            loss.backward();opt.step()
        pred=torch.tensor([model(x,x[j].expand(8,-1)).argmax() for j in range(8)])
        self.assertTrue(torch.equal(pred,torch.arange(8)))
        shuffled=Selector(8,name_dim=8,dim=32);opt=torch.optim.Adam(shuffled.parameters(),lr=.03)
        targets=torch.randperm(8,generator=torch.Generator().manual_seed(51))
        for _ in range(180):
            opt.zero_grad();loss=torch.stack([listwise_loss(shuffled(x,x[j].expand(8,-1)),torch.arange(8)==targets[j]) for j in range(8)]).mean()
            loss.backward();opt.step()
        changed=torch.tensor([shuffled(x,x[j].expand(8,-1)).argmax() for j in range(8)])
        self.assertTrue(torch.equal(changed,targets));self.assertLessEqual(float((changed==torch.arange(8)).float().mean()),.375)

    def test_t4_separable_and_shuffle(self):
        torch.manual_seed(17);x=torch.eye(16);truth=torch.arange(8)
        slots=torch.tensor([0]*8+[16]*8)
        permutation=torch.randperm(8,generator=torch.Generator().manual_seed(51))
        outcomes=[]
        for labels in [truth.repeat(2),torch.cat([truth,permutation])]:
            model=IdentityProbe(16);opt=torch.optim.Adam(model.parameters(),lr=.03)
            for _ in range(100):
                opt.zero_grad();loss=contrastive_loss(model(x),labels,slots);loss.backward();opt.step()
            z=model(x+.001*torch.randn_like(x));pred=(z[:8]@z[8:].T).argmax(-1)
            outcomes.append(float((pred==truth).float().mean()))
        self.assertEqual(outcomes[0],1.);self.assertLessEqual(outcomes[1],.375)

    def test_mask_presence_gradients_and_sizes(self):
        x=torch.randn(2,3,4,12);name=torch.randn(2,4096)
        for cls in (MaskProbe,PresenceProbe):
            model=cls(12);parameter_gate(model)
            y=model(x,name,(12,16)) if cls==MaskProbe else model(x,name)
            self.assertEqual(y.shape,(2,12,16) if cls==MaskProbe else (2,))
            y.square().mean().backward();self.assertTrue(all(p.grad is not None for p in model.parameters()))
        for cls in (Selector,MaskProbe,PresenceProbe,IdentityProbe):parameter_gate(cls(12800))

    def test_bootstrap_and_auroc(self):
        a=mean_ci([1,0,1,1],[0,1,0,1],rooms=['a','a','b','b']);self.assertEqual(a,mean_ci([1,0,1,1],[0,1,0,1],rooms=['a','a','b','b']))
        self.assertEqual(auroc([0,1],[0,1]),1.);self.assertEqual(auroc([0,1],[1,1]),.5)
        self.assertIsNone(auroc([1,1],[0,1]))

    def test_unmatched_identity_rows_have_finite_gradients(self):
        model=IdentityProbe(4);x=torch.eye(4)
        loss=contrastive_loss(model(x),torch.tensor([0,0,1,2]),torch.tensor([0,16,0,0]))
        loss.backward()
        self.assertTrue(torch.isfinite(loss))
        self.assertTrue(all(torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_real_tuning_adapter_and_labels(self):
        from probe_common import candidate_inputs
        from extract import load_payload,candidate_mask
        from eval_data import tuning_gt,gt_mask
        groups,labels,_,_=candidate_inputs()
        self.assertTrue(all(len(labels[g['object_id']]['frame_presence'])==32 for g in groups))
        group=groups[0];member=group['candidates'][0]['members'][0]
        payload=load_payload(member['mask_ref']['path']);mask=candidate_mask(member,payload)
        gt=tuning_gt(group['scene']);truth=gt_mask(gt,group['name'],member['slot'])
        self.assertEqual(mask.shape,(480,640));self.assertEqual(truth.shape,(240,320))
        self.assertEqual(list(gt['frame_indices']),group['frame_indices'])

    def test_fusion_rejects_validation_scene_before_fit(self):
        from fit_t1 import fit_fusion
        from unittest.mock import patch
        rows=[dict(scene='scannet/scene0400_01',split='train')]
        with patch('fit_t1.gate.read_manifest',return_value=rows):
            with self.assertRaisesRegex(ValueError,'outside this training split'):
                fit_fusion('unused.jsonl',None,'cpu',{'scannet/scene0999_00'})

    def test_missing_rules_never_pass(self):
        self.assertEqual(rules_for({}, {})['R1'],'PENDING')
        self.assertIsNone(choose({})['keys'])


if __name__=='__main__':unittest.main()
