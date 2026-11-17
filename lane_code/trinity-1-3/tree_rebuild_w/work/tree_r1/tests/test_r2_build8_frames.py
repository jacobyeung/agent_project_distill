"""Visible frame dimensions through native tiny forward and row producers."""
import copy,json,os
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import numpy as np
import torch
from tests.test_r2_build8 import folder
from tests import test_r2_data_path as D
from student_pilot.p3_provenance import file_pin

class FrameCounts(unittest.TestCase):
    def test_preservation_producer_sqlite_reader_and_rgb_forward(self):
        from tests.test_carrier_c1 import fixture
        from tests.test_r2_build7 import settings
        from student_pilot import carrier_c1_data as data,carrier_c1_run as run
        from student_pilot.carrier_c1 import CarrierC1
        from transformers import Qwen3_5ForConditionalGeneration
        p=folder('preservation_frames');original,_,_=fixture(depth_enabled=False)
        for count in (32,64):
            root=p/str(count);root.mkdir();row=D.fixture(root)
            row['student_input'].update(frames=[file_pin(root/'frames'/f'{i}.png') for i in range(count)],frame_indices=list(range(count)),timestamps=[i/10 for i in range(count)])
            source=root/'rows.jsonl';source.write_text(json.dumps(row)+'\n')
            division=root/'division.json';division.write_text(json.dumps(dict(schema='diagnostic-whole-scene-division-v1',
                training_only=True,train_scenes=['d1/fixture_clean'],heldout_scenes=[])))
            with patch.dict(os.environ,STUDENT_FRAME_ROOT_MAP='{}',STUDENT_ORCHARD='1'):
                receipt=data.build_stream(file_pin(source),file_pin(division),root/'store','vqa',training_mode='final')
                processor=D.TinyProcessor();processor.tokenizer._c1_frame_count=count
                processor._b7_layout={**settings(),'frame_count':count}
                rows=run.Rows(dict(streams={'vqa':receipt},training_mode='final',frame_layout='duplicate'),processor)
                try:batch,_,_=rows.get('vqa',0)
                finally:rows.close()
            cfg=copy.deepcopy(original.config);cfg.text_config.vocab_size=512
            model=CarrierC1(Qwen3_5ForConditionalGeneration(cfg).float(),dict(embed_dim=64,num_heads=4,
                trunk_depth=4,refine_iterations=4,weight_gravity=1.,weight_scale=1.,
                supervision={'path':'/fixture','sha256':'a'*64}),{},5,training_mode='final',depth_enabled=False,
                frame_layout='duplicate',frame_count=count)
            with torch.no_grad():output=model(batch,stream='vqa')
            self.assertTrue(torch.isfinite(output['loss']))
            self.assertEqual(batch['video_grid_thw'][0,0],count)
            self.assertEqual(batch['aux_camera_positions'].shape[1],count)

    def test_camera_rows_queries_and_tiny_forward(self):
        from tests.test_carrier_c1 import fixture,Tokenizer
        from student_pilot.carrier_c1_data import insert_frame_carriers
        from student_pilot.carrier_c1 import CarrierC1
        from student_pilot import carrier_c1_routing as R
        from transformers import Qwen3_5ForConditionalGeneration
        from generator.derivgen_v7.derivgen import camera_rows as C
        p=folder('frame_counts');original,_,_=fixture(depth_enabled=False);measurements=[]
        for count in (32,64):
            with self.subTest(frame_count=count):
                root=p/str(count);root.mkdir()
                raw=D.fixture(root,stream='pose')
                rgb=[file_pin(root/'frames'/f'{i}.png') for i in range(count)]
                raw['student_input'].update(frames=rgb,frame_indices=list(range(count)),total_num_frames=count)
                cameras=np.repeat(np.eye(4)[None],count,axis=0);cameras[:,0,3]=np.arange(count)*.04
                intrinsics=np.array([[30.,0.,16.],[0.,30.,16.],[0.,0.,1.]])
                poses=dict(c2w=cameras,intrinsics=intrinsics,raster_hw=[32,32],world_up=[0.,-1.,0.])
                raw['pose_sample']={'recording':{}}
                clip=C.from_pose_row(raw,poses=poses,manifest_dir=root/'metadata')
                sample=dict(metric=True,gravity_mask=True,anchors=list(range(1,count+1)),camera=clip['gt_pose9'],
                    camera_mask=[True]*count,gravity=clip['gt_up'])
                actual=C.from_pose_row({**raw,'pose_sample':sample},rgb_manifest=clip['rgb_manifest'])
                self.assertEqual(actual['gt_pose9'],clip['gt_pose9'])
                values=C._Geometry(clip).pair(1,count)
                rows=[C._row(clip,'camera_displacement',1,count,values)]
                self.assertEqual(len(rows),1)
                row=rows[0];self.assertIn(f'of {count}',row['question'])
                produced=C._row(clip,'camera_displacement',1,count,values,source=row)
                self.assertEqual(produced['target'],row['target'])
                for kind in C.TYPES:
                    example=C._row(clip,kind,1,count,values)
                    self.assertIn(f'of {count}',example['question'])
                    self.assertEqual(R.render(example['events'],example['answer'])[0],example['target'])
                packed=R.c1_row(row,dict(frames=clip['frames'],fps=clip['fps'],total_num_frames=clip['total_num_frames']))
                self.assertEqual(len(packed['student_input']['frames']),count)
                uv,slots=R.query_tensor([(count,[500.,500.])],frame_count=count)
                self.assertEqual(uv.shape,(count,25,2));self.assertEqual(slots,[(count,0)])
                tok=Tokenizer();tok._c1_frame_count=count
                ids=torch.tensor([[2]+[v for _ in range(count) for v in (62,61,63)]+[10,11]])
                batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=torch.full_like(ids,-100),
                    mm_token_type_ids=torch.where(ids==61,2,0),video_grid_thw=torch.tensor([[count,2,2]]),
                    pixel_values_videos=torch.randn(count*4,24))
                batch=insert_frame_carriers(batch,tok,frame_layout='duplicate')
                model=CarrierC1(Qwen3_5ForConditionalGeneration(original.config).float(),
                    dict(embed_dim=64,num_heads=4,trunk_depth=4,refine_iterations=4,weight_gravity=1.,weight_scale=1.,
                    supervision={'path':'/fixture','sha256':'a'*64}),{},5,training_mode='final',depth_enabled=False,
                    frame_layout='duplicate',frame_count=count)
                with torch.no_grad():readout=model(batch,{'uv':uv},stream='readout')
                geometry=R.own_geometry(readout,[],[])
                rotation,centre=geometry.camera(count)
                self.assertTrue(np.isfinite(rotation).all() and np.isfinite(centre).all())
                measurements.append(dict(frame_count=count,query_shape=list(uv.shape),pose_shape=list(readout['pose'].shape),
                    target_sha256=__import__('hashlib').sha256(row['target'].encode()).hexdigest()))
        with self.assertRaisesRegex(R.RenderError,'unsupported_frame_count'):R.query_tensor([],frame_count=48)
        with self.assertRaisesRegex(R.RenderError,'frame_out_of_range'):R.query_tensor([(65,[0.,0.])],frame_count=64)
        (Path(os.environ['R2_PROOFS'])/'FRAME_COUNTS.json').write_text(json.dumps(measurements,indent=2))

    def test_mask_tower_boundary_and_native_candidate_reader(self):
        from student_pilot import ground_sources as S
        from ofs import core as O
        from student_pilot.sam3_tower import FrameDetections
        from scripts.sam3_validate import rle_encode,rle_decode
        from student_pilot.phrases import normalize_phrase
        codec=SimpleNamespace(rle_encode=rle_encode,rle_decode=rle_decode,phrase=normalize_phrase)
        # Only the unavailable frozen mask tower stands in. The producer cache
        # and candidate reader execute unchanged on its frame-bound outputs.
        class Tower:
            def encode(self,frames):return frames
            def detect(self,frames,name):
                return [FrameDetections(1.,torch.tensor([.9]),torch.tensor([.9]),
                    torch.tensor([[0.,0.,1.,1.]]),torch.ones(1,8,8,dtype=torch.bool),
                    torch.tensor([0]),torch.tensor([.9])) for f in frames]
        for count in (32,64):
            source=S.TowerSAM3(Tower(),[np.zeros((8,8,3),np.uint8)]*count,
                SimpleNamespace(source_indices=tuple(range(count))),'synthetic-boundary',codec)
            cache=source._detect('chair')
            candidates=S.native_candidates(cache,'chair',codec)
            self.assertEqual(len(candidates),count)
            self.assertEqual(candidates[-1].frame,count)
            bad={**cache,'frames':dict(cache['frames'])};bad['frames']['99']=bad['frames']['0']
            with self.assertRaisesRegex(ValueError,'cache_frame_count_or_order'):S.native_candidates(bad,'chair',codec)
            with self.assertRaisesRegex(ValueError,'tower_requires_32_or_64_frames_and_identity'):
                S.TowerSAM3(Tower(),source.frames,SimpleNamespace(source_indices=()),'synthetic-boundary',codec)
