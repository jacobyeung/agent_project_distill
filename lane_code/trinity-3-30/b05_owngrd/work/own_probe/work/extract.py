"""Extract bounded region features; dense maps never reach disk. Resumes by scene and arm."""
import argparse
import collections
import io
import hashlib
import json
import sys
import time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F

from own_feats import load, pool
from own_feats.core import readout_maps
from own_feats.standardize import ChannelMoments,EnergyAudit
from probe_common import ROOT,O,ARMS,gate,rules,RULES_PATH,candidate_inputs,normalize_name
from provenance import sha256,digest,write_json,receipt
from eval_data import tuning_gt,identity_for


def decode_rle(rle):
    h,w=rle['size'];counts=rle['counts']
    if isinstance(counts,str):raise ValueError('Compressed COCO RLE is not the cached SAM format')
    out=np.zeros(h*w,dtype=bool);offset=0
    for i,count in enumerate(counts):
        if count<0 or offset+count>len(out):raise ValueError('Bad RLE count')
        if i%2:out[offset:offset+count]=True
        offset+=count
    if offset!=len(out):raise ValueError('Incomplete RLE')
    return out.reshape((h,w),order='F')


def load_payload(path):
    gate.guard_path(path)
    with np.load(path,allow_pickle=False) as z:
        payload=z['payload']
        if payload.dtype==np.uint8:raw=payload.tobytes().decode()
        else:raw=str(payload.item())
    return json.loads(raw)


def candidate_mask(member,payload):
    ref=member['mask_ref'];gate.guard_path(ref['path'])
    pred=payload['frames'][str(ref['slot'])]['phrases'][ref['phrase']]
    return decode_rle(pred['instances'][ref['instance_index']]['mask'])


def raster_masks(row):
    gate.check_row(row,'training')
    p=Path(row['raster_path'])
    if sha256(p)!=row['raster_sha256']:raise ValueError('Raster changed')
    with np.load(p,allow_pickle=False) as z:
        if row['raster_encoding']=='inst':
            inst=z['inst'];return {x['instance_id']:inst==x['instance_id'] for x in row['instances']}
        if row['raster_encoding']=='packbits':
            shape=tuple(z['shape']);count=int(np.prod(shape))
            return {x['instance_id']:np.unpackbits(z['i'+str(x['instance_id'])])[:count].reshape(shape).astype(bool)
                    if 'i'+str(x['instance_id']) in z.files else np.zeros(shape,bool) for x in row['instances']}
    raise ValueError('Unknown raster encoding')


def chosen_instances(row):
    items=[x for x in row['instances'] if x['pixel_area']>0 and normalize_name(x['name'])]
    items.sort(key=lambda x:digest([17,row['scene'],row['slot'],x['instance_id']]))
    return items[:rules()['sampling']['max_regions_per_frame']]


def cache_bytes(root):
    return sum(p.stat().st_size for p in Path(root).rglob('*') if p.is_file())


def save_shard(path,features,records,binding,scene,purpose,split,source_pins=None,final_features=None,unstandardized_features=None):
    if not path.resolve().is_relative_to('/dev/shm'):
        raise ValueError('Bulk feature shards must stay on the GPU node RAM disk')
    value=dict(features=features.half(),final_features=final_features.half(),
               unstandardized_features=unstandardized_features.half(),records=records)
    buf=io.BytesIO();torch.save(value,buf);data=buf.getvalue()
    if cache_bytes(path.parents[1])+len(data)>rules()['feature_cache_bytes_max']:
        raise ValueError('Total feature cache would exceed 2 GB; no partial shard was written')
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(data)
    write_json(str(path)+'.json',dict(scene=scene,split=split,sha256=sha256(path),binding=binding,
               rules_sha256=sha256(RULES_PATH),authority_sha256=gate.authority_sha256(),
               purpose=purpose,records=len(records),feature_dim=int(features.shape[-1]),input_sha256=source_pins or {}))


def calibrate(encoder,kind,size,train,binding,path,arm):
    """Fit once on train only; val/tuning never affect the channel transform."""
    if path.exists():
        saved=json.loads(path.read_text())
        if saved['binding']!=binding or saved['arm']!=arm:raise ValueError('Calibration resume binding differs')
        if saved['statistics_sha256']!=digest(saved['statistics']):raise ValueError('Calibration checksum differs')
        return saved['statistics']
    groups=collections.defaultdict(list)
    for row in train:
        if row['split']=='train':
            gate.check_row(row,'training');groups[row['scene']].append(row)
    moments=ChannelMoments();pins={};calls=0;selected=[]
    for scene,rows in sorted(groups.items()):
        rows=sorted(rows,key=lambda r:r['slot'])
        chosen=[r for r in rows if r['slot']%rules()['sampling']['training_frame_stride']==0]
        chunks=[rows] if kind=='g3t' else [[r] for r in chosen]
        for chunk in chunks:
            images=[]
            for row in chunk:
                raw=Path(row['rgb_path']).read_bytes();pin=hashlib.sha256(raw).hexdigest()
                if row.get('rgb_sha256',pin)!=pin:raise ValueError('Calibration RGB changed')
                pins[row['rgb_path']]=pin
                with Image.open(io.BytesIO(raw)) as im:images.append(im.convert('RGB'))
            maps=encoder.encode(images,size);calls+=1
            ids=[i for i,r in enumerate(chunk) if r['slot']%rules()['sampling']['training_frame_stride']==0]
            moments.update([m[ids] for m in maps]);selected.extend([dict(scene=scene,slot=chunk[i]['slot'],split='train') for i in ids])
    statistics=moments.finish()
    write_json(path,dict(arm=arm,binding=binding,statistics=statistics,statistics_sha256=digest(statistics),
        rows=selected,input_sha256=pins,encoder=encoder.metadata,size=list(size),calls=calls,
        rules_sha256=sha256(RULES_PATH),training_only=True))
    return statistics


def run(args):
    cfg=rules();torch.set_num_threads(4)
    if args.arm=='A8':raise ValueError('A8 concatenates aligned A2/A4 region records during fit; no encoder pass')
    train=gate.read_manifest(args.train,'training');tune=gate.read_manifest(args.tuning,'tuning')
    groups,_,_,input_pins=candidate_inputs()
    by_scene=collections.defaultdict(list)
    for row in train+tune:by_scene[row['scene']].append(row)
    candidates=collections.defaultdict(list)
    for g in groups:candidates[g['scene']].append(g)
    kind,size=ARMS[args.arm]
    weights=json.loads(Path(args.weights).read_text())[kind]
    encoder=load(kind,weights,args.device)
    binding=digest(dict(arm=args.arm,weights=weights,encoder=encoder.metadata,size=size,rules=sha256(RULES_PATH),
                        train=sha256(args.train),tuning=sha256(args.tuning),candidates=input_pins,
                        code=receipt([],list((ROOT/'work').rglob('*.py')),{})['code']))
    stats_path=Path(args.feature_root)/args.arm/'CHANNEL_STATS.json'
    statistics=calibrate(encoder,kind,size,train,binding,stats_path,args.arm)
    binding=digest(dict(extraction=binding,statistics=statistics))
    energy=EnergyAudit()
    start=time.monotonic();calls=0
    for scene,rows in sorted(by_scene.items()):
        purpose='tuning' if rows[0]['split']=='tuning' else 'training'
        path=Path(args.feature_root)/args.arm/(scene.replace('/','__')+'.pt')
        if path.exists():
            old=json.loads(Path(str(path)+'.json').read_text())
            if old['binding']!=binding or old['sha256']!=sha256(path):raise ValueError('Resume binding differs')
            if not Path(str(path)+'.energy.json').exists():raise ValueError('Shard energy audit is incomplete; use a new feature root')
            continue
        rows=sorted(rows,key=lambda r:r['slot']);all_rows=rows
        if purpose=='training':rows=[r for r in rows if r['slot']%cfg['sampling']['training_frame_stride']==0]
        source_rows=all_rows if kind=='g3t' else rows
        for row in source_rows:gate.check_row(row,purpose)
        masks=raster_masks(rows[0]) if purpose=='training' else None
        payloads={};source_pins={};gt=None;centers={}
        if purpose=='tuning':
            gt=tuning_gt(scene);source_pins[gt['path']]=gt['sha256']
            linked_path=O/'ofs_e1/out/e1/candidates'/(scene.replace('/','__')+'.json')
            linked=json.loads(linked_path.read_text());source_pins[str(linked_path)]=sha256(linked_path)
            for name,cs in linked['candidates'].items():
                for c in cs:
                    for prop in c['proposals']:centers[(c['id'],prop['frame']-1)]=prop['center']
            for g in candidates[scene]:
                for c in g['candidates']:
                    for m in c['members']:
                        p=m['mask_ref']['path']
                        if p not in payloads:
                            payloads[p]=load_payload(p);source_pins[p]=sha256(p)
        else:
            source_pins[rows[0]['raster_path']]=rows[0]['raster_sha256']
        features=[];final_features=[];unstandardized_features=[];records=[]
        # G3T sees an entire 32-frame clip. Other arms run one frame at a time.
        chunks=[source_rows] if kind=='g3t' else [[r] for r in rows]
        for chunk in chunks:
            images=[]
            for row in chunk:
                raw=Path(row['rgb_path']).read_bytes();pin=hashlib.sha256(raw).hexdigest()
                if row.get('rgb_sha256',pin)!=pin:raise ValueError('RGB input changed')
                source_pins[row['rgb_path']]=pin
                with Image.open(io.BytesIO(raw)) as im:images.append(im.convert('RGB'))
            raw_maps=encoder.encode(images,size);calls+=1
            energy.update(raw_maps,statistics,rows[0]['split'])
            maps=readout_maps(raw_maps,statistics=statistics);final_maps=readout_maps(raw_maps,'final',statistics)
            unstandardized_maps=readout_maps(raw_maps,'unstandardized')
            del raw_maps
            positions={r['slot']:i for i,r in enumerate(chunk)}
            for row in rows:
                slot=row['slot']
                if slot not in positions:continue
                one=[m[positions[slot]:positions[slot]+1] for m in maps]
                one_final=[m[positions[slot]:positions[slot]+1] for m in final_maps]
                one_unstandardized=[m[positions[slot]:positions[slot]+1] for m in unstandardized_maps]
                if purpose=='training':
                    items=chosen_instances(row)
                    if not items:continue
                    local_masks=np.stack([masks[x['instance_id']][slot] for x in items])
                    pooled=pool(one,torch.from_numpy(local_masks))
                    final=pool(one_final,torch.from_numpy(local_masks))
                    if (pooled.norm(dim=-1)==0).any() or (final.norm(dim=-1)==0).any():
                        raise ValueError('A nonempty training region pooled to zero')
                    final_features.extend(final)
                    unstandardized_features.extend(pool(one_unstandardized,torch.from_numpy(local_masks)))
                    for x,feat in zip(items,pooled):
                        records.append(dict(scene=scene,split=row['split'],slot=slot,instance_id=x['instance_id'],
                            name=normalize_name(x['name']),area=x['pixel_area']/(240*320),
                            region_id=f'{scene}/{slot}/{x["instance_id"]}'))
                        features.append(feat)
                else:
                    for g in candidates[scene]:
                        for c in g['candidates']:
                            for m in c['members']:
                                if m['slot']!=slot:continue
                                mask=candidate_mask(m,payloads[m['mask_ref']['path']])
                                feat=pool(one,torch.from_numpy(mask[None]))[0]
                                final_features.append(pool(one_final,torch.from_numpy(mask[None]))[0])
                                unstandardized_features.append(pool(one_unstandardized,torch.from_numpy(mask[None]))[0])
                                records.append(dict(scene=scene,split='tuning',slot=slot,name=g['name'],
                                  object_id=g['object_id'],candidate_id=c['candidate_id'],peak=c['peak'],
                                  region_id=digest([g['object_id'],c['candidate_id'],m]),area=float(mask.mean()),
                                  gt_instance_id=identity_for(mask,gt,slot),centroid=centers.get((c['candidate_id'],slot))))
                                features.append(feat)
            del maps
        if not features:raise ValueError(f'No regions: {scene}')
        save_shard(path,torch.stack(features),records,binding,scene,purpose,rows[0]['split'],source_pins,torch.stack(final_features),torch.stack(unstandardized_features))
        write_json(str(path)+'.energy.json',dict(arm=args.arm,statistics_sha256=digest(statistics),energy=energy.finish()))
        energy=EnergyAudit()
        print(json.dumps(dict(arm=args.arm,scene=scene,regions=len(records),calls=calls,elapsed_seconds=time.monotonic()-start)),flush=True)
    write_json(Path(args.feature_root)/args.arm/'COMPLETE.json',dict(binding=binding,encoder=encoder.metadata,
               calls_this_run=calls,seconds_this_run=time.monotonic()-start,rules_sha256=sha256(RULES_PATH),statistics_sha256=digest(statistics)))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--arm',choices=ARMS,required=True)
    p.add_argument('--weights',required=True);p.add_argument('--device',default='cuda:0')
    p.add_argument('--train',default=str(ROOT/'out/b2_manifest.jsonl'))
    p.add_argument('--tuning',default=str(ROOT/'out/tuning_manifest.jsonl'))
    p.add_argument('--feature-root',default='/dev/shm/jjyeung_probe_p0/feats')
    run(p.parse_args())


if __name__=='__main__':main()
