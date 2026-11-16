"""CPU regressions at the extraction, fitting, provider, and decision boundaries."""
import copy
import json
import sys
import unittest
import uuid
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import numpy as np
from PIL import Image
import torch
from torch import nn
from torch.nn import functional as F
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'work'),str(ROOT/'out')]
import extract,fit_t1,online_probe,card,probe_common as pc
from own_feats.core import pixels,pack_qwen,pool,readout_maps,FrozenEncoder,TAPS
from own_feats.providers import HFProvider,RadioProvider,SamProvider,quarter_layers
from provenance import sha256

def folder():
    p=ROOT/'out/R2_FIXTURES'/uuid.uuid4().hex;p.mkdir(parents=True);return p

def metric(v,lo=None,hi=None):return dict(value=v,lo=v if lo is None else lo,hi=v if hi is None else hi)

def fixture_records():
    train=pc.gate.read_manifest(ROOT/'out/b2_manifest.jsonl')
    scenes={split:next(r['scene'] for r in train if r['split']==split) for split in ('train','val')}
    return [dict(scene=scenes[split],slot=0,split=split,name=name,region_id=f'{split}/{i}') for split in scenes for i,name in enumerate(['chair','table'])]

class R2Features(unittest.TestCase):
    def test_reference_processor_packing(self):
        from transformers.models.qwen2_vl.image_processing_pil_qwen2_vl import Qwen2VLImageProcessorPil
        cfg=json.loads((ROOT.parent/'mdg_build/work/t0bundle/base/preprocessor_config.json').read_text())
        processor=Qwen2VLImageProcessorPil(patch_size=16,temporal_patch_size=2,merge_size=2,image_mean=cfg['image_mean'],image_std=cfg['image_std'])
        for hw in [(320,448),(480,640),(768,1024)]:
            im=Image.fromarray(np.random.default_rng(3).integers(0,256,(*hw,3),dtype=np.uint8))
            own,grid=pack_qwen(pixels([im],hw));ref=processor(images=[im],do_resize=False,return_tensors='pt')
            torch.testing.assert_close(own,torch.as_tensor(ref['pixel_values']),rtol=0,atol=0)
            self.assertTrue(torch.equal(grid,torch.as_tensor(ref['image_grid_thw'])))

    def test_quarter_taps_and_equal_head_capacity(self):
        from g3t_taps import TAPS as g3t
        from probe_heads import Selector,MaskProbe,PresenceProbe,IdentityProbe
        self.assertEqual(TAPS,(7,14,21,27));self.assertEqual(g3t,(5,11,17,23))
        self.assertEqual(quarter_layers(24),(6,12,18,24));self.assertEqual(quarter_layers(32),(8,16,24,32))
        counts={}
        for channels in (768,1024,1152,2048):
            maps=[torch.randn(1,2,3,channels)*(i+1)*100 for i in range(4)]
            for readout in ('four','final'):
                out=torch.cat(readout_maps(maps,readout),-1);self.assertEqual(out.shape[-1],1024)
                # Independent normalization and channel averaging oracle.
                selected=maps if readout=='four' else maps[-1:]
                expected=[F.adaptive_avg_pool1d(F.layer_norm(m,(channels,)).reshape(-1,1,channels),1024//len(selected)).reshape(1,2,3,-1) for m in selected]
                expected=[F.layer_norm(m,(m.shape[-1],)) for m in expected]
                torch.testing.assert_close(out,torch.cat(expected,-1))
                self.assertTrue(torch.allclose(out.square().mean(-1),torch.ones(out.shape[:-1]),atol=1e-3))
                for cls in (Selector,MaskProbe,PresenceProbe,IdentityProbe):
                    count=sum(p.numel() for p in cls(out.shape[-1]).parameters())
                    self.assertEqual(count,counts.setdefault(cls,count))

    def test_area_retains_one_pixel_regions_every_arm(self):
        for arm,(_,size) in pc.ARMS.items():
            patchsize=14 if arm in ('A4','A7','D2') else 16
            h,w=(s//patchsize for s in size)
            masks=torch.zeros(3,240,320);masks[0,0,0]=1;masks[1,113,157]=1;masks[2,-1,-1]=1
            feats=pool([torch.ones(1,h,w,3)],masks)
            self.assertTrue((feats.norm(dim=-1)>0).all(),arm)

    def test_output_cast_overflow_rejected(self):
        class Huge(nn.Module):
            def dense(self,frames,size):return [torch.full((1,1,1,2),70000.)]*4
        with self.assertRaisesRegex(ValueError,'overflow'):FrozenEncoder(Huge(),'stub').encode([Image.new('RGB',(2,2))],(2,2))

class ProviderTests(unittest.TestCase):
    def test_hf_layers_and_prefix_removal(self):
        class HF(nn.Module):
            def __init__(self):
                super().__init__();self.weight=nn.Parameter(torch.zeros(()));self.config=NS(patch_size=2,num_hidden_layers=8,num_register_tokens=4)
            def forward(self,pixel_values,output_hidden_states):
                self.seen=pixel_values;tokens=torch.cat([torch.full((1,5,1),-100.),torch.arange(6).reshape(1,6,1)],1)
                return NS(hidden_states=tuple(tokens+i*10 for i in range(9)))
        net=HF();p=HFProvider(net,NS(image_mean=[.5]*3,image_std=[.5]*3),'stub')
        maps=p.dense([Image.new('RGB',(6,4),(255,0,0))],(4,6))
        for m,k in zip(maps,[2,4,6,8]):torch.testing.assert_close(m[0,:,:,0],torch.arange(6).reshape(2,3).float()+k*10)
        self.assertEqual(net.seen[0,:,0,0].tolist(),[1.,-1.,-1.])

    def test_radio_four_backbone_taps(self):
        class Block(nn.Module):
            def forward(self,x):return x+1
        class Radio(nn.Module):
            def __init__(self):
                super().__init__();self.weight=nn.Parameter(torch.zeros(()));self.model=nn.Module();self.model.blocks=nn.ModuleList([Block() for _ in range(8)]);self.model.num_prefix_tokens=2;self.model.patch_embed=NS(patch_size=(16,16))
            def forward(self,x):
                self.seen=x;z=torch.cat([torch.full((1,2,1),-100.),torch.arange(8).reshape(1,8,1)],1)
                for b in self.model.blocks:z=b(z)
                return {'backbone':NS(features=z[:,2:]),'sam3':NS(features=z[:,2:])}
        net=Radio();maps=RadioProvider(net).dense([Image.new('RGB',(64,32),(255,0,0))],(32,64))
        for m,k in zip(maps,[2,4,6,8]):torch.testing.assert_close(m[0,:,:,0],torch.arange(8).reshape(2,4).float()+k)
        self.assertEqual(net.seen[0,:,0,0].tolist(),[1.,0.,0.])
        self.assertTrue(all(not b._forward_hooks for b in net.model.blocks))

    def test_sam_documented_input_and_taps(self):
        class Block(nn.Module):
            def forward(self,x):return x+1
        class Sam(nn.Module):
            def __init__(self):super().__init__();self.weight=nn.Parameter(torch.zeros(()));self.blocks=nn.ModuleList([Block() for _ in range(32)])
            def forward(self,x):
                self.seen=x;z=torch.arange(72*72).reshape(1,72,72,1).float()
                for b in self.blocks:z=b(z)
                return [z.permute(0,3,1,2)]
        self.assertEqual(pc.ARMS['A7'][1],(1008,1008))
        net=Sam();provider=SamProvider(net);maps=provider.dense([Image.new('RGB',(40,30))],(1008,1008))
        for m,k in zip(maps,[8,16,24,32]):torch.testing.assert_close(m[0,:,:,0],torch.arange(72*72).reshape(72,72).float()+k)
        self.assertEqual(tuple(net.seen.shape),(1,3,1008,1008));self.assertEqual(float(net.seen.max()),-1.)
        with self.assertRaises(ValueError):provider.dense([Image.new('RGB',(40,30))],(490,644))

class BoundaryTests(unittest.TestCase):
    def test_injected_tuning_and_evaluation_room_train_rows(self):
        authority=pc.gate.authority();scenes=[authority['tuning_scenes'][0]]
        scenes+= [s for s in authority['frames32_scenes'] if s not in authority['clean_scenes']][:1]
        for scene in scenes:
            # Isolate the semantic room guard from the independent path guard.
            with patch.object(pc.gate,'guard_path'),self.assertRaises(pc.gate.RoomViolation):pc.gate.check_row(dict(scene=scene,split='train'))

    def test_bootstrap_room_clustering_and_pairing(self):
        rooms=['room0']*40+['room1']*40
        a=pc.mean_ci([0]*40+[1]*40,rooms=rooms)
        self.assertEqual((a['lo'],a['hi'],a['rooms'],a['n']),(0.,1.,2,80))
        b=pc.mean_ci([0]*40+[1]*40,[0]*40+[1]*40,rooms=rooms)
        self.assertEqual((b['value'],b['lo'],b['hi']),(0.,0.,0.))
        with self.assertRaises(ValueError):pc.mean_ci([1,2],rooms=['one'])
        with self.assertRaises(ValueError):pc.mean_ci([1,2],[1],rooms=['one','two'])

    def test_card_thresholds_below_boundary_and_uncertainty(self):
        cfg=pc.rules();self.assertEqual(cfg['R1']['reference_max_deficit'],.03)
        self.assertEqual([cfg['R2']['iou_ratio_min'],cfg['R2']['small_iou_ratio_min'],cfg['R3']['auroc_min'],cfg['R3']['shortlist_recall_max_deficit']],[.8,.6,.95,.02])
        tasks={'T1':{'features':{k:metric(1.) for k in ['on_target','name_consistent','training_val_top1']},'fused':{'gain':metric(.06)}},'T3':{'metrics':{'auroc':metric(.96),'shortlist_delta':metric(0.)}},'T4':{'linear':{'retrieval_gain':metric(.06)}}}
        for key in ('name_consistent','training_val_top1'):
            t=copy.deepcopy(tasks);t['T1']['features'][key]=metric(.89)
            self.assertEqual(card.rules_for(t,{})['R1'],'FAIL',key)
        for delta,expected in [(metric(-.031),'FAIL'),(metric(-.03),'INCONCLUSIVE'),(metric(-.03,-.04,-.02),'INCONCLUSIVE'),(metric(-.029),'PASS')]:
            t=copy.deepcopy(tasks);t['T1']['predictions']=[{}]
            for key in ('name_consistent','training_val_top1'):t['T1']['features'][key]=metric(.89,.87,.91)
            with patch('card.paired_difference',return_value=delta):
                self.assertEqual(card.rules_for(t,{'T1':{'predictions':[{}]}})['R1'],expected)
        for task,key,rule,limit in [('T3','auroc','R3',.95),('T3','shortlist_delta','R3',-.02),('T4','retrieval_gain','R4',.05)]:
            t=copy.deepcopy(tasks);group='metrics' if task=='T3' else 'linear';t[task][group][key]=metric(limit-1e-5)
            self.assertNotEqual(card.rules_for(t,{})[rule],'PASS')
        t=copy.deepcopy(tasks);t['T1']['fused']['gain']=metric(.0499);self.assertEqual(card.rules_for(t,{})['R1+'],'FAIL')
        for all_iou,small_iou,expected in [(.8,.6,'PASS'),(.7999,.6,'FAIL'),(.8,.5999,'FAIL')]:
            with patch('card.paired_ratio',side_effect=[metric(all_iou),metric(small_iou)]):
                t=copy.deepcopy(tasks);t['T2']={'records':[{}]};self.assertEqual(card.rules_for(t,{'T2':{'records':[{}]}})['R2'],expected)

    def test_card_own_preference_and_low_pass_high_fail(self):
        scenes=pc.gate.authority()['tuning_scenes'][:4]
        def arm(values,verdict='PASS'):
            return dict(rules={k:verdict for k in ('R1','R2','R3','R1+','R4')},tasks={'T1':{'predictions':[dict(object_id=s+'::obj',scene=s,on_target=v) for s,v in zip(scenes,values)]}})
        arms={'A1':arm([1,0,1,0]),'A2':arm([0,1,0,1]),'A5':arm([0,1,1,0])}
        self.assertEqual(card.choose(arms)['keys'],'A1')
        arms['A2']['rules']['R1']='FAIL';self.assertEqual(card.choose(arms)['keys'],'A1')
        arms['A5']=arm([1,1,1,1]);arms['A1']=arm([0,0,0,0]);arms['A2']=arm([0,0,0,0])
        self.assertEqual(card.choose(arms)['keys'],'A5')
        arms={'A1':arm([0,0,0,0]),'A2':arm([1,1,1,1])};self.assertEqual(card.choose(arms)['keys'],'A2')
        arms['A2']['rules']['R2']='FAIL';self.assertEqual(card.choose(arms)['keys'],'A2')
        arms['A2']['rules']['R3']='FAIL';self.assertEqual(card.choose(arms)['keys'],'A1')

class EntryTests(unittest.TestCase):
    def test_t1_entry_training_budget_phrase_and_candidate_order(self):
        records=fixture_records();groups,labels,fits,pins=pc.candidate_inputs();g=next(g for g in groups if g['name']=='doors');groups=[g]
        ids=[c['candidate_id'] for c in g['candidates']];phrase=g['candidates'][0]['mask_ref']['phrase'];self.assertEqual(phrase,'door')
        tx=torch.eye(len(ids));tr=[dict(scene=g['scene'],split='tuning',object_id=g['object_id'],candidate_id=k,region_id=k,name='door') for k in ids]
        fake_names=NS(mean=torch.ones(3,4096),rows_sha256='test',tokenizer_sha256='test')
        class Scorer(nn.Module):
            def forward(self,x,name):return x[:,1]
        observed=[]
        def fake_fit(x,rs,names,steps,device):
            self.assertEqual(rs,records);self.assertEqual(steps,1200);self.assertIn('door',names);self.assertNotIn('doors',names)
            observed.append(steps);return Scorer(),metric(1.)
        def features(root,arm,purpose,readout):return (torch.randn(4,5),records,[]) if purpose=='training' else (tx,tr,[])
        results=[]
        for arm in ['A1','A2','A3','A4','A5','A6','A7','A8']:
            args=NS(arm=arm,feature_root='unused',out=str(folder()),device='cpu',fusion_rows=None)
            with patch('fit_t1.load_features',side_effect=features),patch('fit_t1.candidate_inputs',return_value=(groups,labels,fits,pins)),patch('fit_t1.NameEmbedder',return_value=lambda names:fake_names),patch('fit_t1.fit',side_effect=fake_fit),patch('fit_t1.torch.save'),patch('fit_t1.output_metrics',side_effect=lambda path,v,*rest:results.append(v)):
                fit_t1.run(args)
            self.assertEqual(results[-1]['predictions'][0]['candidate_id'],ids[1])
            self.assertEqual(results[-1]['predictions'][0]['on_target'],labels[g['object_id']]['candidates'][ids[1]]['on_target'])
        self.assertEqual(len(observed),8)

    def test_t1_fit_rejects_leak_and_learns(self):
        records=fixture_records();names={'chair':F.one_hot(torch.tensor(0),4096).float(),'table':F.one_hot(torch.tensor(1),4096).float()}
        x=torch.eye(2).repeat(2,1);torch.manual_seed(17)
        model,val=fit_t1.fit(x,records,names,60,'cpu');self.assertEqual(val['value'],1.)
        bad=copy.deepcopy(records);bad[0]['scene']=pc.gate.authority()['tuning_scenes'][0]
        with self.assertRaises(pc.gate.RoomViolation):fit_t1.fit(x,bad,names,1,'cpu')

    def test_extractor_entry_masks_match_frames_and_sam_candidates(self):
        root=folder();rows=pc.gate.read_manifest(ROOT/'out/b2_manifest.jsonl')[:2]
        rows=[dict(r,slot=i*4,instances=[dict(instance_id=1,name='chair',pixel_area=1)]) for i,r in enumerate(rows)]
        im=root/'rgb.png';Image.new('RGB',(4,4)).save(im)
        for r in rows:r.update(rgb_path=str(im),rgb_sha256=sha256(im),raster_path=str(im),raster_sha256=sha256(im))
        raster=np.zeros((32,4,4),bool);raster[0,0,0]=True;raster[4,-1,-1]=True;raster[1,1,1]=True;raster[5,1,1]=True
        maps=[torch.randn(1,4,4,8,generator=torch.Generator().manual_seed(17+i)) for i in range(4)]
        enc=NS(metadata={},encode=lambda images,size:[m.repeat(len(images),1,1,1) for m in maps])
        stats=dict(taps=[dict(mean=[0.]*8,std=[1.]*8) for m in maps])
        weights=root/'weights.json';weights.write_text(json.dumps({kind:{} for kind,size in pc.ARMS.values()}));saved=[]
        args=NS(arm='A1',train=str(im),tuning=str(im),weights=str(weights),device='cpu',feature_root=str(root/'feats'))
        for arm in pc.ARMS:
            if arm=='A8':continue  # A8 composes A2/A4; its composition has a separate test.
            args.arm=arm;saved=[]
            with self.subTest(arm=arm),patch('extract.calibrate',return_value=stats),patch('extract.gate.read_manifest',side_effect=[rows,[]]),patch('extract.raster_masks',return_value={1:raster}),patch('extract.candidate_inputs',return_value=([],{}, {},{})),patch('extract.load',return_value=enc),patch('extract.save_shard',side_effect=lambda *a:saved.append(a)),patch('extract.write_json'):
                extract.run(args)
            self.assertEqual([r['slot'] for r in saved[0][2]],[0,4])
            selected=[]
            for m in maps:
                normalized=F.layer_norm(m.float(),(8,))
                reduced=F.adaptive_avg_pool1d(normalized.reshape(-1,1,8),256).reshape(1,4,4,256)
                selected.append(F.layer_norm(reduced,(256,)))
            expected=pool(selected,torch.from_numpy(raster[[0,4]]));torch.testing.assert_close(saved[0][1],expected)
        args.arm='A1'
        groups,_,_,_=pc.candidate_inputs();g=groups[0];c=g['candidates'][0];member=c['members'][0];slot=member['slot']
        tuning=next(r for r in pc.gate.read_manifest(ROOT/'out/tuning_manifest.jsonl','tuning') if r['scene']==g['scene'] and r['slot']==slot)
        g=copy.deepcopy(g);g['candidates']=[copy.deepcopy(c)];g['candidates'][0]['members']=[member]
        payload=extract.load_payload(member['mask_ref']['path']);sam=extract.candidate_mask(member,payload);tuning=dict(tuning,rgb_path=str(im),rgb_sha256=sha256(im))
        saved=[]
        with patch('extract.calibrate',return_value=stats),patch('extract.gate.read_manifest',side_effect=[[],[tuning]]),patch('extract.candidate_inputs',return_value=([g],{}, {},{})),patch('extract.load',return_value=enc),patch('extract.save_shard',side_effect=lambda *a:saved.append(a)),patch('extract.write_json'),patch('eval_data.gt_mask',return_value=np.zeros((4,4),bool)):
            extract.run(args)
        torch.testing.assert_close(saved[0][1][0],pool(readout_maps(maps),torch.from_numpy(sam[None]))[0])

    def test_online_first_tuning_scene_end_to_end_both_tasks(self):
        groups,labels,fits,pins=pc.candidate_inputs();scene=groups[0]['scene'];self.assertEqual(scene,'scannet/scene0011_00')
        groups=[g for g in groups if g['scene']==scene];self.assertIn('doors',[g['name'] for g in groups])
        tune=[r for r in pc.gate.read_manifest(ROOT/'out/tuning_manifest.jsonl','tuning') if r['scene']==scene]
        train=pc.gate.read_manifest(ROOT/'out/b2_manifest.jsonl')[:4];root=folder();labelpath=root/'labels.json';labelpath.write_text('{}')
        class Online:
            def __init__(self,*a):self.calls=0;self.pins={};self.encoders={}
            def __call__(self,row):self.calls+=1;return torch.ones(1,2,2,4)
        def names(ns):return NS(mean=torch.randn(len(ns),4096),rows_sha256='stub',tokenizer_sha256='stub')
        cfg=copy.deepcopy(pc.rules());cfg['fit']['T2_steps']=1;cfg['fit']['T3_steps']=1;cfg['bootstrap']['draws']=30
        for task in ['T2','T3']:
            examples=[(row,'door',np.ones((4,4),bool) if task=='T2' else float(i%2)) for i,row in enumerate(train)]
            args=NS(arm='A1',out=str(root/task),train='train',tuning='tune',labels=str(labelpath),weights='unused',device='cpu')
            results=[]
            with patch('online_probe.gate.read_manifest',side_effect=[train,tune]),patch('online_probe.training_examples',return_value=examples),patch('online_probe.candidate_inputs',return_value=(groups,labels,fits,pins)),patch('online_probe.NameEmbedder',return_value=names),patch('online_probe.OnlineFeatures',Online),patch('online_probe.rules',return_value=cfg),patch('probe_common.rules',return_value=cfg),patch('online_probe.torch.save'),patch('online_probe.output_metrics',side_effect=lambda p,v,*a:results.append(v)):
                online_probe.run(task,args)
            self.assertEqual(len(results[0]['records']),len(groups));self.assertEqual(results[0]['encoder_calls'],37)
            self.assertEqual(results[0]['batch_size'],4)
            for r in results[0]['records']:self.assertEqual(len(r['frames'] if task=='T2' else r['scores']),32)

    def test_shuffle_is_global_and_reproducible(self):
        a=list(online_probe.shuffled_batches(40,10,4));b=list(online_probe.shuffled_batches(40,10,4))
        self.assertEqual(a,b);self.assertEqual(sorted(sum(a,[])),list(range(40)));self.assertNotEqual(sum(a,[]),list(range(40)))
        self.assertTrue(any(len({i//10 for i in batch})>1 for batch in a))


class HandoffTests(unittest.TestCase):
    def test_missing_arm_records_skip(self):
        import run_arm
        root=folder();weights=root/'weights.json';weights.write_text(json.dumps({'sam3_pe':{'path':str(root/'absent.pt'),'source_root':str(root/'absent_source')}}))
        a=NS(arm='A7',train='unused',tuning='unused',weights=str(weights),results=str(root/'results'),readout='four')
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run') as launch:run_arm.run(a)
        launch.assert_not_called();value=json.loads((root/'results/A7/SKIPPED.json').read_text());self.assertIn('absent.pt',value['reason']);self.assertIn('absent_source',value['reason'])

    def test_final_control_reuses_extraction_with_same_steps(self):
        import run_arm
        from test_resume import ResumeTests
        root,a=ResumeTests().fixture();a.readout='final'
        def completed(command,**kwargs):
            self.assertIn('--readout',command);self.assertIn('final',command)
            path=Path(a.results)/'A1/final/T1.json';path.write_text('{}');return NS(returncode=0)
        with patch('run_arm.gate.read_manifest',return_value=[]),patch('run_arm.subprocess.run',side_effect=completed):run_arm.run(a)
        self.assertTrue((Path(a.results)/'A1/final/T1.done.json').exists())
        self.assertFalse((Path(a.results)/'A1/final/extract.done.json').exists())

    def test_download_metadata_requires_exact_published_weight_fields(self):
        from resolve_download_metadata import resolve
        metadata={'id':'org/model','sha':'a'*40,'siblings':[{'rfilename':'model.safetensors','size':123,'lfs':{'sha256':'b'*64}}]}
        value=resolve(metadata);self.assertEqual(value['files'][0]['size'],123);self.assertIn('/'+'a'*40+'/',value['files'][0]['url'])
        metadata['siblings'][0]['lfs']={}
        with self.assertRaises(ValueError):resolve(metadata)

    def test_feature_writer_rejects_non_ram_disk(self):
        with self.assertRaisesRegex(ValueError,'RAM disk'):extract.save_shard(ROOT/'out/forbidden.pt',torch.ones(1,2),[],{},'scene','training','train',final_features=torch.ones(1,2))

if __name__=='__main__':unittest.main()
