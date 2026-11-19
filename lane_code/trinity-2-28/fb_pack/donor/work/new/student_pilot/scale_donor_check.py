"""Compare real first-step exports on pinned K1 RGB without loading the LM.

This checks frozen tensors and grids, not scale accuracy. The denominator is a
fixed synthetic tower fixture; V2 uses the selected captures' recorded G3T FoV.
The caller supplies the native first-two-step export, not a fabricated update.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from torch import nn
from PIL import Image

from . import scale_donor as D
from .p3_provenance import load, pinned, sha256
from .tower_read import TowerState
from .tower_scale import estimate_scale


def captures(selection, config, image_side):
    """Pin every RGB byte and use an explicit fixture resolution and native packing."""
    from transformers.models.qwen3_vl.video_processing_qwen3_vl import Qwen3VLVideoProcessor
    from transformers.video_utils import VideoMetadata
    vision = config.vision_config
    unit = vision.patch_size * vision.spatial_merge_size
    if image_side < unit or image_side % unit:
        raise ValueError('Fixture image side must be a positive patch/merge multiple')
    processor = Qwen3VLVideoProcessor(patch_size=vision.patch_size,
        temporal_patch_size=vision.temporal_patch_size, merge_size=vision.spatial_merge_size)
    if len(selection['captures']) != 2:
        raise ValueError('Invariance requires exactly two pinned K1 training captures')
    result, inputs = [], {}
    for c in selection['captures']:
        if c['k1_split'] != 'train' or c['split'] != 'train' or len(c['anchor_slots']) != 32:
            raise ValueError('Invariance captures must have K1 train provenance and 32 anchors')
        fv = selection['fovs'][c['canonical']]
        capture_sha = hashlib.sha256(json.dumps(c, sort_keys=True, allow_nan=False).encode()).hexdigest()
        if fv['capture_sha256'] != capture_sha or fv['anchor_indices'] != c['anchor_indices']:
            raise ValueError('G3T FoV capture/anchor binding differs')
        images = []
        for index, slot in zip(c['anchor_indices'], c['anchor_slots']):
            frame = c['dense_frames'][slot]
            if frame['index'] != index:
                raise ValueError('K1 anchor mapping differs')
            path = pinned({k:frame[k] for k in ('path','sha256')})
            inputs[str(path)] = frame['sha256']
            with Image.open(path) as im:
                images.append(np.asarray(im.convert('RGB').resize((image_side,image_side), Image.Resampling.BICUBIC)))
        array = np.repeat(np.stack(images), vision.temporal_patch_size, axis=0)
        # Explicit normalisation avoids a torchvision dependency in CPU kits.
        array = (array.astype(np.float32)/255. - np.asarray(processor.image_mean, np.float32)) / np.asarray(processor.image_std, np.float32)
        count = len(array)
        batch = dict(processor(videos=[array], video_metadata=[VideoMetadata(total_num_frames=count,
            fps=2., frames_indices=list(range(count)))], do_sample_frames=False, do_resize=False,
            do_convert_rgb=False, do_normalize=False, do_rescale=False,
            input_data_format='channels_last', return_tensors='pt'))
        raw = np.zeros((32,9)); raw[:,0] = np.arange(32)*.1; raw[:,6] = 1; raw[:,7:9] = fv['fov_hw_rad']
        depth = np.broadcast_to(np.linspace(1,2,51)[None,None], (32,51,51)).copy()
        state = TowerState(raw, depth, np.arange(depth.size).reshape(depth.shape),
                           np.asarray(c['anchor_indices']), np.arange(32))
        batch.update(tower_frame_indices=torch.tensor(state.frame_indices.copy()),
                     tower_anchor_slots=torch.tensor(state.anchor_slots.copy()),
                     tower_lm_frame_indices=torch.tensor(state.frame_indices.copy()))
        result.append((c['canonical'], batch, state))
    return result, inputs


def private_model(config, preparation, state):
    from transformers.models.qwen3_5.modeling_qwen3_5 import Qwen3_5VisionModel
    from .carrier_c1 import PrivateDepth
    if preparation.get('frame_layout') != 'duplicate' or preparation.get('frame_count',32) != 32:
        raise ValueError('This export check requires the pinned N duplicate/32-frame preparation')
    visual = Qwen3_5VisionModel(config.vision_config).float()
    depth = PrivateDepth(config, visual, preparation['depth'], 32)
    depth.config.p3['frame_layout'] = 'duplicate'
    depth.load_state_dict({k.removeprefix('depth.'):v for k,v in state.items() if k.startswith('depth.')}, strict=True)
    depth.model.visual.requires_grad_(False).eval()
    model = nn.Module(); model.auxiliary_heads = nn.Module(); model.auxiliary_heads.depth = depth
    return model


@torch.no_grad()
def observe(model, cases):
    from .decoupled_v import features
    from .tower_read import GRID_UV
    model.eval(); donor = model.auxiliary_heads.scale_donor
    donor.train(False)
    depth = model.auxiliary_heads.depth
    axis=torch.as_tensor(GRID_UV.copy());yy,xx=torch.meshgrid(axis,axis,indexing='ij')
    uv=torch.stack((xx,yy),-1).reshape(1,-1,2).expand(32,-1,-1)
    values=[]
    for name,batch,state in cases:
        frozen=donor(batch,state)
        cap=features(depth,batch,allow_short=True)
        # Fix the conditioning FoV to isolate changes in the live point-depth head.
        fov=torch.tensor(state.raw_pose9[:,7:9],dtype=torch.float32)
        live=depth.auxiliary_heads.camera.point_depth(cap.grids[0],cap.vits[0],fov,uv).reshape(32,51,51)
        scale=estimate_scale(state.depth_grid,state.depth_conf_grid,frozen.double().numpy())[0]
        h=lambda t:hashlib.sha256(t.contiguous().numpy().tobytes()).hexdigest()
        values.append(dict(capture=name,donor_grid_sha256=h(frozen),live_grid_sha256=h(live),scale=scale,
                           scale_float64_sha256=hashlib.sha256(np.float64(scale).tobytes()).hexdigest()))
    return values


def _check(args):
    from transformers import Qwen3_5Config
    inputs={}
    def read(name):
        path=pinned(dict(path=str(Path(getattr(args,name)).resolve()),sha256=getattr(args,name+'_sha')))
        inputs[str(path)]=sha256(path);return load(path)
    initial,after,prep,raw,selection,binding=(read(n) for n in
        ('init_artifact','after_artifact','preparation','model_config','selection','binding'))
    if after.get('step') != 2:
        raise ValueError('Real-weight check requires the native step-2 export')
    config=Qwen3_5Config(**raw)
    for part in (config,config.vision_config,config.text_config):part._attn_implementation='sdpa'
    initial_path=pinned(initial['heads']);inputs[str(initial_path)]=initial['heads']['sha256']
    state=torch.load(initial_path,map_location='cpu',weights_only=True)
    model=private_model(config,prep,state)
    donor=D.attach(model,binding['scale_donor']);inputs.update(donor.source_pins)
    cases,frame_pins=captures(selection,config,args.image_side);inputs.update(frame_pins)
    before_pins=D.tensor_pins(donor.state_dict())
    live0=D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
    before=observe(model,cases)
    after_path=pinned(after['heads']);inputs[str(after_path)]=after['heads']['sha256']
    updated=torch.load(after_path,map_location='cpu',weights_only=True)
    metadata=updated.pop('_scale_donor',None)
    if metadata!=after.get('scale_donor'):raise ValueError('Donor export metadata differs')
    D.verify_export(model,updated,metadata)
    model.auxiliary_heads.depth.load_state_dict({k.removeprefix('depth.'):v for k,v in updated.items()
                                                if k.startswith('depth.')},strict=True)
    donor.load_state_dict({k.removeprefix(D.PREFIX):v for k,v in updated.items()
                          if k.startswith(D.PREFIX)},strict=True)
    final=observe(model,cases);after_pins=D.tensor_pins(donor.state_dict())
    live1=D.tensor_pins(model.auxiliary_heads.depth.auxiliary_heads.camera.point_depth.state_dict())
    assert before_pins==after_pins
    changed=[k for k in live0 if live0[k]!=live1[k]]
    if not changed:raise ValueError('Live point-depth head did not move')
    for a,b in zip(before,final):
        if any(a[k]!=b[k] for k in ('donor_grid_sha256','scale','scale_float64_sha256')):
            raise ValueError('Donor grid/scale drift: '+a['capture'])
        if a['live_grid_sha256']==b['live_grid_sha256']:raise ValueError('Live grid did not move: '+a['capture'])
    inputs[str(Path(__file__).resolve())]=sha256(__file__)
    for name in ('scale_donor.py','carrier_c1.py','tower_scale.py','tower_scale_rule.py',*D.FEATURE_FILES):
        p=Path(__file__).parent/name;inputs[str(p)]=sha256(p)
    result=dict(input_sha256=inputs,status='PASS',before=before,after=final,donor_tensors_before=before_pins,
        donor_tensors_after=after_pins,live_head_changed=changed,settings=donor.settings,
        image_side=args.image_side,steps=after['step'],
        weights=('fixture' if initial.get('fixture') or after.get('base_identity')=='fixture' else 'checkpoint_export'),
        private_visual_sha256=donor.metadata()['shared_visual_sha256'],
        scope='Export tensors at explicit fixture RGB resolution; synthetic frozen tower depth/confidence; recorded G3T FoV. Live grids use fixed tower FoV to isolate head updates.',
        command=__import__('shlex').join(__import__('sys').argv))
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    return result



def check(args):
    """Relocate supplied content pins without rewriting authenticated artifacts."""
    replicas, expected = getattr(args, 'replicas', None), getattr(args, 'replicas_sha', None)
    if bool(replicas) != bool(expected):
        raise ValueError('Replica mapping requires both a path and SHA256')
    if not replicas:
        return _check(args)
    path = pinned(dict(path=str(Path(replicas).resolve()), sha256=expected))
    mapping = load(path)
    if not isinstance(mapping, dict) or not isinstance(mapping.get('paths'), dict):
        raise ValueError('Replica mapping requires a SHA256-to-local-path dictionary in paths')
    for key, value in mapping['paths'].items():
        if (len(key) != 64 or any(c not in '0123456789abcdef' for c in key)
                or not isinstance(value, str) or not Path(value).is_absolute()):
            raise ValueError('Invalid replica mapping')
    from .r1_persisted import scope
    with scope(mapping['paths']):
        result = _check(args)
    result['input_sha256'][str(path)] = expected
    Path(args.output).write_text(json.dumps(result, indent=2)+'\n')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('init-artifact','after-artifact','preparation','model-config','selection','binding'):
        parser.add_argument('--'+name,required=True);parser.add_argument('--'+name+'-sha',required=True)
    parser.add_argument('--image-side',type=int,required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--replicas')
    parser.add_argument('--replicas-sha')
    args=parser.parse_args();torch.set_num_threads(16);check(args)


if __name__=='__main__':main()
