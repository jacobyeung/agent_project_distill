"""Concrete local CarrierC1 adapter for run_live_parity.py; no downloads.

Inputs require carrier_config, carrier_manifest, carrier_receipt and artifact
{path,sha256} pins, hf_checkpoint, and audit_dir. Each item names a pinned row
JSON. Routed items also name geometry and a SAM frame_manifest/raw_dir/scene
or a mask_export pin. Labels and score_mask are read only by score functions.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import numpy as np

_inputs = None
_cfg = None


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def local(path):
    path=Path(path).resolve()
    if not str(path).startswith('/scratch/'):
        raise ValueError('Parity assets and outputs must be staged on /scratch')
    return path


def pinned(pin):
    path=local(pin['path'])
    if sha(path)!=pin['sha256']:raise ValueError('Input pin differs: '+str(path))
    return path


def document(pin):
    return json.loads(pinned(pin).read_text())


def load_processor(inputs):
    global _inputs, _cfg
    from student_pilot.carrier_c1_run import processor_for_receipt
    _inputs=deepcopy(inputs);_cfg=document(inputs['carrier_config'])
    manifest=document(inputs['carrier_manifest']);receipt=document(inputs['carrier_receipt'])
    local(manifest['root']);local(inputs['hf_checkpoint']);local(inputs['audit_dir'])
    return processor_for_receipt(manifest,receipt)


def load(inputs, device):
    import torch
    from transformers import GenerationConfig
    from student_pilot.carrier_c1_run import load_model, load_artifact
    processor=load_processor(inputs)
    manifest=document(inputs['carrier_manifest']);receipt=document(inputs['carrier_receipt'])
    # load_model authenticates the base files, and load_artifact authenticates
    # every selected student component. The kit loads its HF export separately.
    model=load_model(manifest,receipt,processor)
    pinned(inputs['artifact'])
    artifact=load_artifact(model,inputs['artifact'])
    if artifact['base_identity']!=_cfg['base_identity']:
        raise ValueError('Artifact and carrier config have different base identities')
    model.generation_config=GenerationConfig.from_pretrained(local(inputs['hf_checkpoint']),local_files_only=True)
    model.to(torch.device(device)).eval().requires_grad_(False)
    return model,processor


def _source_row(row):
    source=document(row['row'])
    inputs=source['student_input']
    allowed=('frames','frame_indices','timestamps','fps','total_num_frames','question','options',
             'video_sha256','partner_frames','anchor_slots','recording_id')
    return dict(qid=str(row['id']),student_input={k:inputs[k] for k in allowed if k in inputs},
                routing=dict(category='route',question_type=row.get('type','addressing')))


def _batch(row,model,processor,question=None):
    from PIL import Image
    from student_pilot.carrier_c1_canary import prompt_batch
    import torch
    source=_source_row(row)
    if question is not None:source['student_input']['question']=question
    inputs=source['student_input'];frames={};hashes=[]
    if len(inputs['frames'])!=32 or len(inputs['frame_indices'])!=32:
        raise ValueError('Parity requires exactly 32 source frames')
    for k,pin in enumerate(inputs['frames'],1):
        with Image.open(pinned(pin)) as image:frames[k]=image.convert('RGB')
        if frames[k].size!=(640,480):raise ValueError('Expected native 640x480 RGB')
        hashes.append(hashlib.sha256(np.asarray(frames[k]).tobytes()).hexdigest())
    batch=prompt_batch(processor,source,_cfg)
    batch.update(video_sha256=inputs['video_sha256'],frame_indices=inputs['frame_indices'],
                 hrp_frame_indices=inputs['frame_indices'],frame_rgb_sha256=hashes,ground_frames=frames)
    device=next(model.parameters()).device
    return {k:v.to(device) if isinstance(v,torch.Tensor) else v for k,v in batch.items()},frames


def _backend(row,batch):
    import ofs
    from ofs import core as O
    from rk.programs import load_heads
    from rk.sam3mask import tower
    from student_pilot.geometry_profiles import legacy_from_heads,scaled_from_heads
    from student_pilot.scene_state import FrameMap,SceneState
    from student_pilot.ground_sources import CachedSAM3,MaskBatch,MaskProvider,OwnProposals
    from student_pilot.ground_v3 import GroundV3
    mapping=FrameMap(tuple(batch['frame_indices']),rgb_sha256=tuple(batch['frame_rgb_sha256']))
    profile=row.get('geometry_profile','legacy_v3122');path=pinned(row['geometry'])
    if profile=='legacy_v3122':geo=legacy_from_heads(path,mapping,load_heads)
    elif profile=='scaled_g3t_depth':geo=scaled_from_heads(path,mapping)
    else:raise ValueError('Unknown depth profile')
    mask_source=row.get('mask_source','svp_sam3')
    if mask_source=='svp_sam3':
        manifest=pinned(row['frame_manifest'])
        source=CachedSAM3(local(row['raw_dir']),row['scene'],mapping,tower(),manifest,names=row.get('names',()))
        if source.identity!=row['source_identity']:raise ValueError('SAM source identity differs')
    elif mask_source in ('mdg','svp_own'):
        from student_pilot.mdg_eval import read_npz
        path=pinned(row['mask_export']);names,values,metadata=read_npz(path)
        mapping.require(metadata['frame_indices']);lookup={n:i for i,n in enumerate(names)}
        def masks(name):
            i=lookup.get(name)
            m=np.zeros_like(values['mask'][0]) if i is None else values['mask'][i]
            p=np.zeros(32) if i is None else values['prob'][i]
            return MaskBatch(m,p,mapping.source_indices)
        if mask_source=='mdg':source=MaskProvider(masks,row['mask_export']['sha256'])
        else:
            codec=tower()
            def proposals(name,geometry,selector,grids):
                mb=masks(name);phrase=codec.phrase(name)
                cache=dict(phrases=[phrase],frames={str(k):dict(phrases={phrase:dict(presence=1.,
                    instances=[dict(score=float(mb.probabilities[k]),mask=codec.rle_encode(mb.masks[k]))])}) for k in range(32)})
                return selector.lift(cache,name,geometry,grids=grids)
            source=OwnProposals(proposals,mapping,row['mask_export']['sha256'])
    else:raise ValueError('Live parity supports svp_sam3, svp_own or mdg')
    return GroundV3(SceneState(batch['video_sha256'],mapping,geo.identity),geo,source,
        mask_source=mask_source,geometry_profile=profile,selector=ofs,selector_identity=sha(O.__file__),
        audit_dir=local(_inputs['audit_dir']),rule=row.get('rule','native_selector'))


def routed(row,model,processor):
    from student_pilot.verify_pass import Config
    batch,_=_batch(row,model,processor);backend=_backend(row,batch)
    return batch,Config(backend),dict(ground_backend=backend,mask_source=backend.mask_source,
                                    max_new_tokens=_inputs.get('max_new_tokens',16384))


def score_routed(row,baseline,enabled):
    from student_pilot.carrier_c1_canary import answer_of,agree
    a,b=answer_of(baseline['text']),answer_of(enabled['text'])
    label=row['label']
    return dict(type=row['type'],video_answer=a,verify_answer=b,label=label,
                video_correct=agree(a,label),verify_correct=agree(b,label),changed=a!=b)


def addressing(row,model,processor):
    from student_pilot.hrp_reread import Config
    batch,frames=_batch(row,model,processor)
    slot=row['anchor_slot'];image=frames[slot]
    if batch['frame_indices'][slot-1]!=row['source_index']:
        raise ValueError('Addressing source index differs')
    if hashlib.sha256(np.asarray(image).tobytes()).hexdigest()!=row['frame_rgb_sha256']:
        raise ValueError('Addressing RGB differs')
    config=Config({slot:image},tuple(batch['frame_indices']))
    return image,batch,config,dict(max_new_tokens=_inputs.get('max_new_tokens',16384))


def video_address(row,model,processor,batch):
    from student_pilot import carrier_c1_decode as D
    from student_pilot.hrp_reread import parse_point
    question=(f"Point to the {row['name']} in Frame {row['anchor_slot']} of this video. "
              'Output JSON {"point_2d": [x, y]} with integer coordinates on a 0-1000 grid. '
              'If the object is absent, output {"point_2d": null}.')
    video,_=_batch(row,model,processor,question)
    record=D.generate(model,processor,video,max_new_tokens=48)
    raw=record['text'].split('</think>')[-1].strip()
    point,status=parse_point(raw)
    if record['finish']!='eos':point,status=None,'capped'
    return dict(raw_output=raw,point_2d=point,parse_status=status,record=record)


def score_addressing(row,image_only,video_only,reread):
    # Score masks are never opened by _batch, _backend, addressing, or inference.
    from PIL import Image
    with Image.open(pinned(row['score_mask'])) as image:mask=np.asarray(image.convert('L'))>0
    h,w=mask.shape
    def score(value):
        status=value['parse_status'];point=value.get('point_2d');hit=False
        if status=='point' and point is not None:
            x,y=np.asarray(point,float)
            if np.isfinite([x,y]).all() and 0<=x<=1000 and 0<=y<=1000:
                hit=bool(mask[min(h-1,int(y*h/1000)),min(w-1,int(x*w/1000))])
        return dict(hit=hit,null=status=='null',invalid=status in ('invalid','multiple'),capped=status=='capped')
    return dict(image_only=score(image_only),video_only=score(video_only),reread=score(reread),
                small_object=bool(row['small_object']),same_class=bool(row['same_class']))
