"""Regression checks for dense encoding, donor identity, export loading and harm stops."""
import copy
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F
from student_pilot import gf1, gf1_config, g3t_online as gx, carrier_c1_run as run, carrier_c1_data as data
from student_pilot.p3_provenance import file_pin
from tests.test_gf1 import fixture, TinyEncoder, logits, equal
from tests.test_gf1_trainer import collectives, Rows
from tests.test_carrier_c1 import Tokenizer

BASE = Path(os.environ.get('GF1_BASE_TREE', '/scratch/jjyeung/orch_cd/integ_v3/work/tree'))

def directory():
    return Path(tempfile.mkdtemp(prefix='gf1_review_', dir=os.environ['LANE_TEST_OUTPUT']))


class CharacterTokenizer:
    """Lossless test text vocabulary; visual tokens retain the tiny native model IDs."""
    pad_token_id=0
    eos_token='<eos>'
    eos_token_id=1
    def encode(self,text,**kwargs):
        return [ord(c)+100 for c in text.removesuffix(self.eos_token)] + ([1] if text.endswith(self.eos_token) else [])
    def decode(self,ids,**kwargs):
        return ''.join(self.eos_token if int(i)==1 else (chr(int(i)-100) if int(i)>=100 else '<visual>') for i in ids)


class NativeVideoProcessor:
    """Tiny text template around the real Qwen video processor, without pretrained files."""
    video_token_id=61
    def __init__(self):
        from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
        self.tokenizer=CharacterTokenizer()
        self.video_processor=Qwen3VLVideoProcessor(patch_size=16,temporal_patch_size=2,merge_size=2)
    def apply_chat_template(self,messages,**kwargs):
        prefix='Question: where?\nAnswer: '
        return prefix if len(messages)==1 else prefix+messages[-1]['content']+'<eos>\n'
    def __call__(self,text,videos,video_metadata,**kwargs):
        # The frame is already 320x416, inside the production pixel budget.
        packed=self.video_processor(videos=videos,video_metadata=video_metadata,**kwargs)
        ids=self.tokenizer.encode(text[0])
        t,h,w=map(int,packed['video_grid_thw'][0])
        for i in range(t):
            ids += self.tokenizer.encode(f'<{video_metadata[0].frames_indices[2*i]/video_metadata[0].fps:.1f} seconds>')
            ids += [62]+[61]*(h*w//4)+[63]
        packed['input_ids']=torch.tensor([ids])
        packed['mm_token_type_ids']=torch.where(packed['input_ids']==61,2,0)
        return packed


class ReviewRegression(unittest.TestCase):
    def test_unpatched_dense64_non_square_impulse_to_input_id(self):
        root=directory()
        # One retained non-square PNG, 64 distinct source indices. No loader or encoder patch.
        raw=np.zeros((320,416,3),dtype=np.uint8);raw[...,0]=np.arange(416,dtype=np.uint16)%256
        Image.fromarray(raw).save(root/'frame.png');pin=file_pin(root/'frame.png')
        dense=dict(frames=[pin]*64,frame_indices=list(range(64)),timestamps=list(map(float,range(64))),fps=1,total_num_frames=64)
        sparse={**dense,**{k:v[::2] for k,v in dense.items() if k in ('frames','frame_indices','timestamps')},
                'geometry_dense':dense,'question':'where?','options':[]}
        processor=NativeVideoProcessor()
        batch,audit=data.encode_layout_row(processor,dict(student_input=sparse,target='A'),'duplicate',None,
                                          gf1=gf1.normalize({}))
        self.assertEqual(batch['aux_g3t_images'].shape,(1,64,3,518,518))
        self.assertEqual(batch['video_grid_thw'].tolist(),[[32,20,26]])
        self.assertEqual(audit['visual_tokens'],4160)
        roi=batch['aux_g3t_coords'][0,0]
        torch.testing.assert_close(roi,torch.tensor([0.,48*1024/416,1024.,368*1024/416]))
        model,_,_=fixture();config=copy.deepcopy(model.config)
        config.vision_config.patch_size=16;config.text_config.vocab_size=512
        from transformers import Qwen3_5ForConditionalGeneration
        native=Qwen3_5ForConditionalGeneration(config).eval()
        fusion=gf1.Fusion(32,dict(layers=[0],hidden=1,checkpointing=False),input_dim=1)
        fusion.norms[0]=torch.nn.Identity()
        with torch.no_grad():
            fusion.projections[0].weight.fill_(1);fusion.projections[0].bias.zero_();fusion.outputs[0].weight.fill_(.01)
        # Tower cell (19,18) lies wholly within merger cell (5,6). Dense frame 14 is LM frame 7.
        bank=torch.zeros(1,64,37,37,1);bank[0,14,19,18,0]=1
        model.geometry_online['gf1']=fusion.settings
        batch['aux_gf1_shared']=gf1.SharedHeadFeatures(model.auxiliary_heads.geometry_encoder,[0],
            torch.zeros(64,2058),bank.flatten(2,3))
        cameras,clips=gf1.geometry_features(model,batch)
        self.assertIsNone(cameras)
        captured=[]
        class Captured(Exception):pass
        def capture(module,args,kwargs):
            captured.append(kwargs['inputs_embeds'].detach().clone());raise Captured
        handle=native.model.language_model.register_forward_pre_hook(capture,with_kwargs=True)
        native_batch={k:v for k,v in batch.items() if not k.startswith('aux_') and k!='labels'}
        try:
            with torch.no_grad(),self.assertRaises(Captured):native(**native_batch)
            with torch.no_grad(),fusion.inject(native,clips,batch,{}),self.assertRaises(Captured):native(**native_batch)
        finally:handle.remove()
        delta=captured[1]-captured[0]
        visual=(batch['input_ids'][0]==61).nonzero().flatten()
        expected=7*130+5*13+6
        self.assertEqual(delta.abs().sum(-1).nonzero()[:,1].tolist(),[int(visual[expected])])
        expected_value=(1024/37)**2/((1024/13)*(320*1024/416/10))*.01
        torch.testing.assert_close(delta[0,visual[expected]],torch.full((32,),expected_value),rtol=1e-4,atol=1e-7)
        (root/'alignment.json').write_text(json.dumps(dict(dense_frame=14,lm_frame=7,merger_token=expected,
            input_id_position=int(visual[expected]),roi=roi.tolist(),grid=[37,37,10,13])))

    def test_nonzero_camera_base_tree_step_zero_logits(self):
        # Import the read-only base as a distinct package: no toggling the GF1 model as a baseline.
        package='_gf1_pristine_student'
        if package not in sys.modules:
            spec=importlib.util.spec_from_file_location(package,BASE/'student_pilot/__init__.py',
                submodule_search_locations=[str(BASE/'student_pilot')])
            module=importlib.util.module_from_spec(spec);sys.modules[package]=module;spec.loader.exec_module(module)
        base_c1=importlib.import_module(package+'.carrier_c1');base_gx=importlib.import_module(package+'.g3t_online')
        self.assertEqual(base_gx.vendor_digest(),gx.vendor_digest())
        # The identical vendored teacher is a singleton package in this serial process.
        self.enterContext(patch.object(base_gx,'VENDOR',gx.VENDOR))
        class DonorEncoder(base_gx.G3TEncoder):
            def __init__(self,block):
                super().__init__(block,dict(aggregator=dict(img_size=28,patch_size=14,embed_dim=16,depth=3,num_heads=2,
                    patch_embed='conv'),head=dict(dim_in=32,trunk_depth=1,num_heads=2)),image_size=28,verify_full=False)
            def forward(self,images,coords=None):
                self.assert_no_grad=not torch.is_grad_enabled()
                cam,local,global_=super().forward(images,coords)
                return F.pad(cam,(0,2048-cam.shape[-1])),local,global_
        for injection in ('pre_lm','lm_012'):
            model,batch,_=fixture(1,injection);model.eval()
            with torch.no_grad():
                model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.normal_(std=.01)
                model.auxiliary_heads.pose.cam_token_connector.mlp[2].bias.fill_(.02)
                model.auxiliary_heads.pose.cam_token_connector.rms_cam.fill_(.7)
            geometry=copy.deepcopy(model.geometry_online);geometry.pop('gf1')
            from transformers import Qwen3_5ForConditionalGeneration
            with patch.object(base_gx,'G3TEncoder',DonorEncoder):
                donor=base_c1.CarrierC1(Qwen3_5ForConditionalGeneration(copy.deepcopy(model.config)),
                    model.auxiliary_heads.pose.settings,{},5,training_mode='final',depth_enabled=False,
                    frame_layout='duplicate',depth_fov_source='pose_head',recipe=model.recipe,
                    geometry_online=geometry,geometry_runtime=model.geometry_runtime).eval()
            donor.load_state_dict({k:v for k,v in model.state_dict().items() if not k.startswith('auxiliary_heads.gf1.')})
            gf1.check_camera_context(model,dict(geometry_online=geometry))
            with torch.no_grad():
                expected=logits(donor,batch);actual=logits(model,batch)
            self.assertTrue(torch.equal(expected,actual),float((expected-actual).abs().max()))
            self.assertTrue(donor.auxiliary_heads.geometry_encoder.assert_no_grad)
            self.assertEqual(model.auxiliary_heads.geometry_encoder.calls,2)
            # The nonzero donor is observable, not a fixture with a dead camera path.
            with torch.no_grad():
                donor.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.zero_()
                donor.auxiliary_heads.pose.cam_token_connector.mlp[2].bias.zero_()
                self.assertFalse(torch.equal(expected,logits(donor,batch)))

    def test_export_round_trip_evaluator_loader_and_missing_init_refusal(self):
        from safetensors.torch import save_file
        from transformers import Qwen3_5ForConditionalGeneration
        from student_pilot import trained_groups
        model,batch,cfg=fixture();root=directory()
        model.model.to(torch.bfloat16);model.lm_head.to(torch.bfloat16);model.eval()
        with torch.no_grad():
            model.auxiliary_heads.gf1.outputs[0].weight.normal_(std=.003)
            model.auxiliary_heads.pose.cam_token_connector.mlp[2].weight.normal_(std=.01)
            model.auxiliary_heads.pose.cam_token_connector.rms_cam.fill_(.7)
        def train_groups():
            trained_groups.capture(model)
            parameters=[value for group in trained_groups.parameters(model).values() for value in group.values()]
            optimizer=torch.optim.SGD(parameters,lr=.1)
            sum(value.square().sum() for value in parameters).backward()
            trained_groups.observe(model)
            optimizer.step()
            optimizer.zero_grad(set_to_none=True)
        train_groups()
        save_file(model.auxiliary_heads.geometry_encoder.state_dict(),root/'tower.safetensors')
        (root/'tower.json').write_text(json.dumps(dict(embed_dim=1024,enable_depth=True,enable_gravity_camera_heads=True,
            enable_point=True,img_size=518,patch_size=14)))
        geometry=model.geometry_online
        geometry['encoder']['weights']=file_pin(root/'tower.safetensors');geometry['encoder']['config']=file_pin(root/'tower.json')
        cfg.update(geometry_online=geometry,base_identity='native-tiny-fixture')
        with collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
            run.export(root/'export',model,model,cfg,1)
        artifact=file_pin(root/'export/artifact.json')
        receipt={**cfg,'camera':model.auxiliary_heads.pose.settings,'depth':{},
            'init_artifact':dict(artifact=artifact,lm='full',heads=['pose','gf1'])}
        processor=SimpleNamespace(tokenizer=Tokenizer(),video_processor=SimpleNamespace(image_mean=[.5]*3,image_std=[.25]*3),
                                  _routing_tokens=dict(ids={'fixture':10},constituents={'fixture':[10]}))
        def fresh(*a,**kw):return Qwen3_5ForConditionalGeneration(copy.deepcopy(model.config)).to(torch.bfloat16)
        # Native evaluate/probe loader: only assets/preparation resolve to tiny local fixtures.
        with patch.object(run,'prepared',return_value=(receipt,dict(root=str(root),files={}))),\
             patch.object(run,'processor_for_receipt',return_value=processor),\
             patch.object(Qwen3_5ForConditionalGeneration,'from_pretrained',side_effect=fresh),\
             patch.object(gx,'G3TEncoder',TinyEncoder):
            restored,_,_,_=run.inference(cfg,artifact,torch.device('cpu'))
            self.assertTrue(equal(model.auxiliary_heads.gf1.state_dict(),restored.auxiliary_heads.gf1.state_dict()))
            with torch.no_grad():self.assertTrue(torch.equal(logits(model,batch),logits(restored,batch)))
            receipt['init_artifact']['heads'].remove('gf1')
            with self.assertRaisesRegex(ValueError,'GF1 export requires gf1'):run.inference(cfg,artifact,torch.device('cpu'))
        # Binder demands a trained connector, unless zero is an explicit stage decision.
        stage=json.loads((Path(__file__).resolve().parents[1]/'configs/gf1_stage2.json').read_text())
        # Match tiny architecture for the donor.
        stage['gf1'].update(layers=[0,1,2],hidden=16)
        source={**cfg,'init_artifact':dict(artifact=artifact,lm='full',heads=['pose','gf1'])}
        bound=gf1_config.bind(source,stage,root/'run',root/'prep')
        self.assertEqual(bound['geometry_online']['gf1']['gf1_init'],'warm')
        source['init_artifact']['heads'].remove('gf1')
        with self.assertRaisesRegex(ValueError,'Stage 2 requires'):gf1_config.bind(source,stage,root/'run',root/'prep')
        stage['gf1']['gf1_init']='zero'
        gf1_config.bind(source,stage,root/'run',root/'prep')
        cold_model,_,_=fixture(2)
        cold_model.geometry_online['encoder']=copy.deepcopy(geometry['encoder'])
        cold_model.geometry_online['gf1']['gf1_init']='zero'
        run.init_from_artifact(cold_model,source['init_artifact'])
        self.assertEqual(int(torch.count_nonzero(cold_model.auxiliary_heads.gf1.outputs[0].weight)),0)
        cold_artifact=root/'cold.json';cold=json.loads((root/'export/artifact.json').read_text());cold['geometry_online'].pop('gf1')
        cold_artifact.write_text(json.dumps(cold));source['init_artifact']=dict(artifact=file_pin(cold_artifact),lm='full',heads=['pose','gf1'])
        stage['gf1'].pop('gf1_init')
        with self.assertRaisesRegex(ValueError,'donor does not carry'):gf1_config.bind(source,stage,root/'run',root/'prep')

        # An explicitly cold training start still exports trained tensors for evaluation.
        geometry['gf1']=gf1.normalize(stage['gf1'] | dict(gf1_init='zero'))
        cfg.update(steps=stage['steps'],milestones=stage['milestones'])
        cfg['recipe']=gf1_config.recipe_for(cfg);model.recipe=cfg['recipe']
        model.requires_grad_(True)
        gf1.configure_trainables(model)
        train_groups()
        with collectives(),patch('student_pilot.fsdp_training.publication_state',return_value=model.state_dict()):
            run.export(root/'zero_export',model,model,cfg,1)
        artifact=file_pin(root/'zero_export/artifact.json')
        receipt.update(cfg)
        receipt['init_artifact']=dict(artifact=artifact,lm='full',heads=['pose','gf1'])
        with self.assertRaisesRegex(ValueError,'zero init conflicts'):
            run.init_from_artifact(model,receipt['init_artifact'])
        with patch.object(run,'prepared',return_value=(receipt,dict(root=str(root),files={}))),\
             patch.object(run,'processor_for_receipt',return_value=processor),\
             patch.object(Qwen3_5ForConditionalGeneration,'from_pretrained',side_effect=fresh),\
             patch.object(gx,'G3TEncoder',TinyEncoder):
            restored,_,_,_=run.inference(cfg,artifact,torch.device('cpu'))
            self.assertTrue(equal(model.auxiliary_heads.gf1.state_dict(),restored.auxiliary_heads.gf1.state_dict()))
            with torch.no_grad():self.assertTrue(torch.equal(logits(model,batch),logits(restored,batch)))
            receipt['init_artifact']['heads'].remove('gf1')
            with self.assertRaisesRegex(ValueError,'GF1 export requires gf1'):
                run.inference(cfg,artifact,torch.device('cpu'))

    def test_dense_failures_are_fatal_in_both_fetch_paths_and_all_ranks(self):
        model,_,_=fixture()
        class Missing:
            count=lambda self,stream:10
            def get(self,*a):raise ValueError('GF1 missing geometry_dense')
        for nominal in (False,True):
            for distributed in (False,True):
                with patch.object(run.dist,'all_reduce') as reduction,self.assertRaisesRegex(ValueError,'forbids substitution'):
                    if nominal:run.fetch_nominal(Missing(),'vqa',[0,1],model,distributed=distributed)
                    else:run.fetch(Missing(),'vqa',0,model,distributed=distributed)
                self.assertEqual(reduction.call_count,int(distributed))

    def test_harm_stops_and_unknown_settings(self):
        gf1.harm_guard(.5,1.,1.02)
        for args in ((.5001,None,None),(.1,1.,1.0201),(float('nan'),None,None)):
            with self.assertRaisesRegex(ValueError,'harm stop'):gf1.harm_guard(*args)
        def peer_harm(flags,**kw):flags[1]=1
        with patch.object(run.dist,'all_reduce',side_effect=peer_harm),self.assertRaisesRegex(ValueError,'step-1'):
            gf1.harm_guard(.1,1.,1.,distributed=True)
        with self.assertRaisesRegex(ValueError,'Unknown'):gf1.normalize(dict(unread=True))
        with self.assertRaisesRegex(ValueError,'actual LM rate'):gf1.normalize(dict(stage=2,learning_rate=1e-5))
        for key in ('lm_frames','stall_seconds','startup_seconds','unknown'):
            stage=json.loads((Path(__file__).resolve().parents[1]/'configs/gf1_stage1.json').read_text());stage[key]=32
            with self.assertRaisesRegex(ValueError,'Unknown'):gf1_config.bind({},stage,'unused','unused')

    def test_native_trainer_invokes_harm_guards_and_averages_only_connector(self):
        from student_pilot.carrier_c1 import parameter_groups
        from student_pilot.carrier_c1_data import mixed_indices
        model,batch,cfg=fixture();model.train()
        optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
        plan=next(mixed_indices(dict(pose=40,vqa=40,pointing=40,routing=40),1,
            training_mode='final',mix=cfg['recipe']['mix'],world=4))
        before={n:p.detach().clone() for n,p in model.named_parameters() if not p.requires_grad}
        # Mimic four equal ranks without sockets; run the actual attached-gradient reduction.
        class Wrapped(torch.nn.Module):
            def __init__(self,m):super().__init__();self._fsdp_wrapped_module=m
            @property
            def module(self):return self._fsdp_wrapped_module
            def forward(self,*a,**kw):return self.module(*a,**kw)
        reduced=[]
        def reduction(tensor,op=None,**kwargs):
            if op is None:reduced.append(tensor);tensor.mul_(4)
        with patch.object(run.dist,'get_world_size',return_value=4),patch.object(run.dist,'all_reduce',side_effect=reduction):
            record,_=run.optimize_step(Wrapped(model),optimizer,Rows(batch),plan,0,torch.device('cpu'),1,True)
        self.assertIsNotNone(record['gf1_harm_screen'])
        self.assertTrue(all(torch.equal(before[n],p) for n,p in model.named_parameters() if n in before))
        self.assertTrue(all(p.grad is None for p in model.parameters() if not p.requires_grad))
        self.assertTrue(all(any(t is p.grad for t in reduced) for p in model.auxiliary_heads.gf1.parameters()))
        # A real optimizer call must stop automatically on an unsafe fixed-row readout.
        model,batch,cfg=fixture();optimizer=torch.optim.AdamW(parameter_groups(model,cfg['recipe']),foreach=False)
        with patch.object(gf1,'screen_loss',side_effect=[(1.,0.),(1.03,0.)]),self.assertRaisesRegex(ValueError,'step-1'):
            run.optimize_step(model,optimizer,Rows(batch),plan,0,torch.device('cpu'),1)
        with torch.no_grad():model.auxiliary_heads.gf1.outputs[0].weight.fill_(100.)
        with self.assertRaisesRegex(ValueError,'patch_delta_ratio'):
            run.optimize_step(model,optimizer,Rows(batch),plan,0,torch.device('cpu'),2)

if __name__=='__main__':unittest.main()
