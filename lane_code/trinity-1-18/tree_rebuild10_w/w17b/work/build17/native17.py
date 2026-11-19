"""Native RGB builder/encoder/forward boundary probe; not a mode-q admission."""
from pathlib import Path
from unittest.mock import patch
import json,os,sys,traceback
L=Path(__file__).resolve().parents[2];B=L/'work/build17';T=L/'work/tree_r1'
O=B/'proofs/native';O.mkdir(parents=True,exist_ok=True)
sys.path[:0]=[str(T),str(B),str(L/'work/n1fix2')]
import tempfile
tempfile.tempdir=str(L/'work/tmp')
from monitor9 import Monitor
m=Monitor(T)
from native_assets17 import assets,PatchGridProcessor
from student_pilot.p3_provenance import file_pin,load
from tests.test_r2_build_n1 import write
import torch
from PIL import Image,ImageDraw
from student_pilot import carrier_c1_data as D
from student_pilot.carrier_c1 import CarrierC1
from student_pilot import carrier_c1_run as C
result=dict(status='INCOMPLETE',GO=False,complete_native_fixture=False,
    stages={},stand_ins=['synthetic RGB frame host','tiny native model dimensions',
        'PatchGridProcessor: HF image/video constructor substitute with real persisted HF tokenizer, 2x2 patches, temporal pairs and merge size 2'])
before=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
assert before<=200_000_000
try:
    base=assets(O/'model')
    processor=PatchGridProcessor(O/'model');processor._student_pilot_student='qwen35'
    from student_pilot.carrier_c1_routing import add_routing_tokens
    add_routing_tokens(processor)
    im=Image.new('RGB',(32,32),'white');draw=ImageDraw.Draw(im)
    draw.rectangle((2,10,10,20),fill='red');draw.rectangle((20,10,28,20),fill='blue')
    im.save(O/'f.png');f=file_pin(O/'f.png')
    row=dict(qid='fixture',dataset='d1',scene='scene9997_00',canonical='scannet/scene9997_00',
        question_type='object_rel_direction_easy',target='<think>The red square is left of the blue square in the frames.</think>\n\nA',
        student_input=dict(question='Is the red square left or right of the blue square?',options=['A. left','B. right'],
            frames=[f]*32,frame_indices=list(range(32)),timestamps=[i/10 for i in range(32)],fps=10,total_num_frames=32))
    source=O/'rows.jsonl';source.write_text(json.dumps(row)+'\n')
    division=write(O/'division.json',dict(schema='diagnostic-whole-scene-division-v1',training_only=True,
        train_scenes=['d1/scene9997_00'],heldout_scenes=['d1/scene9998_00']))
    target=O/'vqa'
    if not (target/'receipt.json').exists():D.build_stream(file_pin(source),division,target,'vqa',training_mode='final')
    result['stages']['native_store_builder']=file_pin(target/'receipt.json')
    processor.tokenizer._c1_frame_markers=True
    processor.tokenizer._c1_frame_count=32
    processor._b7_layout=dict(frame_count=32,frame_layout='duplicate',max_pixels=16,min_pixels=16)
    camera=dict(embed_dim=16,num_heads=2,trunk_depth=1,refine_iterations=1,
        weight_gravity=.05,weight_scale=.04,supervision={'path':'fixture','sha256':'a'*64})
    depth=dict(weight=.05,d_proj=16,mlp_hidden=16,num_heads=2,context_depth=1,vit_layers=[1,2,3])
    model=CarrierC1(base,camera,depth,2,'append_after_temporal_group_video_tokens_v1',
        'final',True,frame_layout='duplicate')
    model.trace_program_version='3.13'
    receipt=dict(streams={'vqa':dict(database=load(target/'receipt.json')['database'],count=1)},
        carrier_placement='append_after_temporal_group_video_tokens_v1',training_mode='final',
        frame_layout='duplicate',frame_count=32,frame_markers=True)
    reader=C.Rows(receipt,processor)
    batch,targets,audit=reader.get('vqa',0)
    result['stages']['native_RGB_reader_encoder']=dict(tokens=batch['input_ids'].shape[-1],
        video_grid=batch['video_grid_thw'].tolist(),pixel_shape=list(batch['pixel_values_videos'].shape),
        video_tokens=int((batch['input_ids']==processor.video_token_id).sum()))
    with torch.no_grad():output=model(batch,targets,stream='vqa')
    loss=float(output['loss']);assert torch.isfinite(output['loss'])
    result['stages']['native_full_forward']=dict(loss=loss)
    reader.close()
except Exception as e:
    result['refusal']=type(e).__name__+':'+str(e);result['traceback']=traceback.format_exc()
result['not_demonstrated']=['one complete native mode-q admission','native prepared population and all-rank resumed losses at 400 and 600 in that invocation']
after=sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file())
assert after<=200_000_000
result['temporary_bytes']=dict(before=before,after=after)
write(O/'RESULT.json',result);m.save(O)
print(json.dumps(result,indent=2))
