"""Exercise the shipped adapter and renderer without loading GPU weights."""
from pathlib import Path
from types import SimpleNamespace as NS
from unittest.mock import patch
import hashlib
import importlib.util
import json
import unittest
import uuid
import numpy as np
from PIL import Image
import torch
from tests.test_ground_r2 import ROOT,TMP,production
from tests.test_verify_r2 import integration_fixture,PixelModel,TinyProcessor


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def pin(path):return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class LiveAdapter(unittest.TestCase):
    def test_all_twenty_crops_materialize_from_source(self):
        root=Path('/scratch/jjyeung/orch_cd/gv_fix')
        driver=module('r3_driver',root/'out/run_live_parity.py')
        manifest=json.loads(Path('/scratch/jjyeung/orch_cd/verify_gen/out/PARITY_CROPS_20.json').read_text())
        images,checks=driver.materialize_check(manifest,manifest['crops'])
        self.assertEqual(len(images),20);self.assertTrue(all(c['equal'] for c in checks))
        (ROOT/'out/MATERIALIZE_PARITY_R3.json').write_text(json.dumps(checks,indent=1)+'\n')

    def test_adapter_loads_native_entrypoints_and_builds_real_backend(self):
        A=module('staged_live_adapter',Path(__file__).resolve().parents[3]/'inputs/gv_fix/live_parity_adapter.py')
        from student_pilot.carrier_c1_run import move
        folder=TMP/('adapter_'+uuid.uuid4().hex);folder.mkdir()
        def doc(name,value):
            path=folder/name;path.write_text(json.dumps(value));return pin(path)
        cfg=doc('config.json',dict(base_identity='base',carrier_placement='fixture'))
        manifest=doc('manifest.json',dict(root=str(folder)))
        receipt=doc('receipt.json',dict(training_mode='final'))
        artifact=doc('artifact.json',dict(base_identity='base'))
        inputs=dict(carrier_config=cfg,carrier_manifest=manifest,carrier_receipt=receipt,
                    artifact=artifact,hf_checkpoint=str(folder),audit_dir=str(folder/'audits'))
        model,processor,prompt=integration_fixture();g=production()
        image=Image.new('RGB',(640,480),(123,37,51));path=folder/'frame.png';image.save(path)
        rgb=hashlib.sha256(np.asarray(image).tobytes()).hexdigest()
        source=doc('row.json',dict(student_input=dict(frames=[pin(path)]*32,frame_indices=list(g.frame_map.source_indices),
            timestamps=list(range(32)),fps=1,total_num_frames=100,question='Where is the chair?',video_sha256='a'*64),
            label='must not enter prompt',target='must not enter prompt'))
        from student_pilot.mdg_eval import save_npz
        from ofs.core import empty_values
        values=empty_values(1);values['mask'][0,0,20:50,30:60]=True;values['prob'][0,0]=.9
        values['frame_prob']=values['prob'].copy();values['area']=values['mask'].mean(axis=(-1,-2))
        export=folder/'masks.npz'
        save_npz(export,['chair'],values,dict(frame_indices=list(g.frame_map.source_indices)))
        # Production geometry's source identity names its generated NPZ.
        from tests.test_ground_r2 import synthetic
        geometry_path=folder/'geometry.npz';np.savez(geometry_path,**synthetic())
        row=dict(id='one',type='absolute_distance',row=source,geometry=pin(geometry_path),mask_source='mdg',
                 mask_export=pin(export),name='chair',anchor_slot=1,source_index=g.frame_map.source_indices[0],
                 frame_rgb_sha256=rgb,label='2',small_object=False,same_class=True)
        with patch('student_pilot.carrier_c1_run.processor_for_receipt',return_value=processor) as lp, \
             patch('student_pilot.carrier_c1_run.load_model',return_value=model) as lm, \
             patch('student_pilot.carrier_c1_run.load_artifact',return_value=dict(base_identity='base')) as la, \
             patch('transformers.GenerationConfig.from_pretrained',return_value=NS(eos_token_id=1)):
            loaded,proc=A.load(inputs,'cpu')
        self.assertIs(loaded,model);self.assertIs(proc,processor)
        lp.assert_called_once();lm.assert_called_once();la.assert_called_once()
        with patch('student_pilot.carrier_c1_canary.prompt_batch',return_value=prompt) as pb:
            b,config,kwargs=A.routed(row,model,processor)
            addressed,ab,hrp,ak=A.addressing(row,model,processor)
        clean=pb.call_args.args[1]
        self.assertNotIn('label',clean);self.assertNotIn('target',clean)
        self.assertEqual(config.backend.config['rule'],'native_selector')
        self.assertEqual(kwargs['mask_source'],'mdg');self.assertEqual(config.backend.geometry_error,None)
        self.assertEqual(hrp.frame_indices,g.frame_map.source_indices);self.assertEqual(set(hrp.frames),{1})
        self.assertEqual(np.asarray(addressed).shape,(480,640,3))
        self.assertEqual(A.score_routed(row,{'text':'2'},{'text':'3'})['video_correct'],True)
        score=folder/'score.png';Image.new('L',(640,480),255).save(score);row['score_mask']=pin(score)
        read=dict(parse_status='point',point_2d=[500,500])
        result=A.score_addressing(row,read,dict(parse_status='null'),read)
        self.assertTrue(result['image_only']['hit']);self.assertTrue(result['video_only']['null'])
        with patch('student_pilot.carrier_c1_canary.prompt_batch',return_value=prompt) as pb, \
             patch('student_pilot.carrier_c1_decode.generate',return_value=dict(text='{"point_2d": [500, 500]}',finish='eos')) as generate:
            result=A.video_address(row,model,processor,b)
        self.assertEqual(result['point_2d'],[500,500])
        self.assertIn('Frame 1',pb.call_args.args[1]['student_input']['question'])
        self.assertEqual(generate.call_args.kwargs,dict(max_new_tokens=16384))
        with self.assertRaisesRegex(ValueError,'pin differs'):
            A.document(dict(path=source['path'],sha256='0'*64))

    def test_hrp_uses_native_wrapper_keyword_batch_and_restores_offset(self):
        from student_pilot.hrp_reread import read_image,Config
        native=PixelModel();processor=TinyProcessor();rope=native.model.rope_deltas
        calls=[]
        def generate(**kw):
            calls.append(kw)
            self.assertEqual(kw['max_new_tokens'],48)
            self.assertIsNone(native.model.rope_deltas)
            native.model.rope_deltas=torch.tensor([-7])
            return torch.cat((kw['input_ids'],torch.tensor([[50,63]])),1)
        native.generate=generate;carrier=NS()
        image=Image.new('RGB',(640,480));config=Config({1:image},tuple(range(32)))
        with patch('student_pilot.verify_pass.native_view',return_value=native) as wrapper:
            result=read_image(carrier,processor,image,'chair',config)
        wrapper.assert_called_once_with(carrier)
        self.assertIs(native.model.rope_deltas,rope);self.assertEqual(result['parse_status'],'null')
        self.assertIn('pixel_values',calls[0]);self.assertNotIn('video_grid_thw',calls[0])


if __name__=='__main__':unittest.main()
