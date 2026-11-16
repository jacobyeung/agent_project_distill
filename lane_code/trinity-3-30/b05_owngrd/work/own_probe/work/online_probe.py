"""Online T2/T3 fitting. Only compact head checkpoints and object records are saved."""
import argparse
import collections
import io
import json
import time
from pathlib import Path
import numpy as np
from PIL import Image
import torch
from torch.nn import functional as F
from own_feats import load,NameEmbedder
from own_feats.core import readout_maps,channel_reduce
from probe_common import *
from probe_heads import MaskProbe,PresenceProbe,parameter_gate
from eval_data import tuning_gt,gt_mask
from extract import decode_rle,load_payload


def resize_mask(mask,size):
    return np.asarray(Image.fromarray(np.asarray(mask,dtype=bool)).resize((size[1],size[0]),Image.Resampling.NEAREST),bool)


def iou(a,b):
    a=np.asarray(a,dtype=bool);b=np.asarray(b,dtype=bool);u=(a|b).sum()
    return float((a&b).sum()/u) if u else 1.


def teacher_mask(row):
    if 'mask_rle' in row:return decode_rle(row['mask_rle'])
    ref=row.get('mask_ref')
    if not isinstance(ref,dict):raise ValueError('O5 POS rows need mask_rle or mask_ref')
    gate.guard_path(ref['path'],'training')
    if not ref.get('sha256') or sha256(ref['path'])!=ref['sha256']:raise ValueError('Unpinned O5 mask')
    if {'phrase','slot','instance_index'}<=set(ref):
        payload=load_payload(ref['path'])
        pred=payload['frames'][str(ref['slot'])]['phrases'][ref['phrase']]
        return decode_rle(pred['instances'][ref['instance_index']]['mask'])
    with np.load(ref['path'],allow_pickle=False) as z:
        x=z[ref.get('key','mask')]
        if 'index' in ref:x=x[int(ref['index'])]
    return np.asarray(x,dtype=bool)


class OnlineFeatures:
    def __init__(self,arm,weights,rows,device,readout='four',feature_root=None):
        self.readout=readout
        self.arm=arm;self.device=device;self.scene=None;self.clip_maps=None;self.pins={}
        self.rows=collections.defaultdict(list)
        for row in rows:self.rows[row['scene']].append(row)
        for scene in self.rows:self.rows[scene].sort(key=lambda r:r['slot'])
        cfg=json.loads(Path(weights).read_text());self.cfg=cfg
        self.encoders={};self.statistics={}
        for a in (['A2','A4'] if arm=='A8' else [arm]):
            kind,size=ARMS[a];self.encoders[a]=load(kind,cfg[kind],device)
            if feature_root is None:raise ValueError('Online features require extraction channel statistics')
            path=Path(feature_root)/a/'CHANNEL_STATS.json';saved=json.loads(path.read_text())
            if saved['arm']!=a or saved['rules_sha256']!=sha256(RULES_PATH) or saved['encoder']!=self.encoders[a].metadata or saved['size']!=list(size):raise ValueError('Channel statistics provenance differs')
            if not saved['training_only'] or any(r['split']!='train' for r in saved['rows']):raise ValueError('Statistics contain non-training rows')
            for row in saved['rows']:gate.check_row(row,'training')
            if saved['statistics_sha256']!=digest(saved['statistics']):raise ValueError('Statistics checksum differs')
            self.statistics[a]=saved['statistics'];self.pins[str(path)]=sha256(path)
        self.calls=0

    def read_image(self,row):
        purpose='tuning' if row['split']=='tuning' else 'training';gate.check_row(row,purpose)
        raw=Path(row['rgb_path']).read_bytes();import hashlib
        pin=hashlib.sha256(raw).hexdigest()
        if row.get('rgb_sha256',pin)!=pin:raise ValueError('RGB pin differs')
        self.pins[row['rgb_path']]=pin
        with Image.open(io.BytesIO(raw)) as im:return im.convert('RGB')

    def __call__(self,row):
        arrays=[]
        for arm,encoder in self.encoders.items():
            if arm=='A4':
                if self.scene!=row['scene']:
                    frames=self.rows[row['scene']]
                    if [r['slot'] for r in frames]!=list(range(32)):raise ValueError('G3T needs all 32 ordered frames')
                    self.clip_maps=encoder.encode([self.read_image(r) for r in frames],ARMS[arm][1]);self.scene=row['scene'];self.calls+=1
                maps=[m[row['slot']:row['slot']+1] for m in self.clip_maps]
            else:
                maps=encoder.encode([self.read_image(row)],ARMS[arm][1]);self.calls+=1
            maps=readout_maps(maps,self.readout,self.statistics[arm])
            arrays.append(torch.cat(maps,-1))
        size=arrays[0].shape[1:3]
        arrays=[F.interpolate(m.permute(0,3,1,2).float(),size=size,mode='bilinear',align_corners=False).permute(0,2,3,1)
                if m.shape[1:3]!=size else m.float() for m in arrays]
        result=channel_reduce(torch.cat(arrays,-1))
        return F.layer_norm(result,(result.shape[-1],)).to(self.device)


def training_examples(task,path,manifest):
    rows=gate.read_manifest(path,'training')
    frames={(r['scene'],r['slot']):r for r in manifest if r['split']=='train'}
    allowed=('POS',) if task=='T2' else ('POS','ABSENT')
    grouped=collections.defaultdict(list)
    for r in rows:
        if r['split']!='train' or r.get('status') not in allowed:continue
        if (r['scene'],r['slot']) not in frames:raise ValueError('O5 row outside admitted training manifest')
        if r['status']=='POS' and float(r.get('joint_score',0))<=.5:raise ValueError('POS below native teacher gate')
        if r['status']=='ABSENT' and (float(r.get('presence',1))>=.2 or r.get('gt_visible') is not False):
            raise ValueError('ABSENT does not certify GT/teacher agreement')
        grouped[(r['scene'],r['slot'],normalize_name(r['name']))].append(r)
    by_frame=collections.defaultdict(list)
    for (s,k,n),rs in grouped.items():by_frame[s,k].append((n,rs))
    keys=sorted(by_frame,key=lambda k:digest([17,*k]))[:rules()['sampling']['mask_frames']]
    if task=='T2' and len(keys)<rules()['sampling']['mask_frames']:
        raise ValueError(f'T2 needs 1500 eligible training frames; found {len(keys)}')
    examples=[]
    for key in sorted(keys):
        name,rs=min(by_frame[key],key=lambda x:digest([17,*key,x[0]]))
        if task=='T2':
            targets=[teacher_mask(r) for r in rs];target=np.logical_or.reduce(targets)
        else:
            labels={r['status']=='POS' for r in rs}
            if len(labels)!=1:raise ValueError('Contradictory O5 presence labels')
            target=float(labels.pop())
        examples.append((frames[key],name,target))
    if not examples:raise ValueError('No admissible online fitting examples')
    if task=='T3' and {float(x[2]) for x in examples}!={0.,1.}:raise ValueError('T3 requires both agreement classes')
    return examples


def summarize_t2(records):
    output={}
    for target in ('sam','gt'):
        for label,lo,hi in [('all',0,2),('small',0,.01),('1_2pct',.01,.02),('2_5pct',.02,.05),('large',.05,2)]:
            selected=[]
            for r in records:
                vals=[v[target+'_iou'] for v in r['frames'] if lo<=v['area']<hi and v[target+'_valid']]
                if vals:selected.append(dict(values=vals,scene=r['scene']))
            output[target+'_'+label]=object_bootstrap(selected,lambda rs:float(np.mean([np.mean(r['values']) for r in rs]))) if selected else None
    return output


def summarize_t3(records):
    def auc(rs):return auroc([v for r in rs for v in r['labels']],[v for r in rs for v in r['scores']])
    rooms=[gate.room(*r['scene'].split('/')) for r in records]
    return dict(auroc=object_bootstrap(records,auc),shortlist_recall=mean_ci([r['shortlist_hit'] for r in records],rooms=rooms),
                sam_shortlist_recall=mean_ci([r['sam_shortlist_hit'] for r in records],rooms=rooms),
                shortlist_delta=mean_ci([r['shortlist_hit'] for r in records],[r['sam_shortlist_hit'] for r in records],rooms=rooms))


def shuffled_batches(count,steps,batch_size):
    rng=np.random.default_rng(rules()['fit']['shuffle_seed']);order=[];cursor=0
    for _ in range(steps):
        batch=[]
        while len(batch)<batch_size:
            if cursor==len(order):order=rng.permutation(count).tolist();cursor=0
            take=min(batch_size-len(batch),len(order)-cursor)
            batch.extend(order[cursor:cursor+take]);cursor+=take
        yield batch


def run(task,a):
    seed_all();out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    train=gate.read_manifest(a.train);tune=gate.read_manifest(a.tuning,'tuning')
    if not a.labels or not Path(a.labels).exists():
        output_metrics(out/(task+'.json'),dict(arm=a.arm,readout=getattr(a,'readout','four'),task=task,status='pending',reason='O5 agreement labels are absent'),
                       [RULES_PATH,Path(__file__)],vars(a));return
    examples=training_examples(task,a.labels,train)
    groups,labels,_,pins=candidate_inputs();names=sorted({n for _,n,_ in examples}|{candidate_phrase(g) for g in groups})
    nb=NameEmbedder()(names);emb=dict(zip(names,nb.mean));online=OnlineFeatures(a.arm,a.weights,train+tune,a.device,getattr(a,'readout','four'),getattr(a,'feature_root',None))
    sample=online(examples[0][0]);head=(MaskProbe if task=='T2' else PresenceProbe)(sample.shape[-1]).to(a.device)
    count=parameter_gate(head);optimizer=torch.optim.AdamW(head.parameters(),lr=rules()['fit']['mask_learning_rate'])
    steps=rules()['fit'][task+'_steps'];start=time.monotonic()
    batch_size=rules()['fit']['online_batch_size']
    schedule=shuffled_batches(len(examples),steps,batch_size)
    for step,indices in enumerate(schedule):
        optimizer.zero_grad();losses=[]
        for index in indices:
            row,name,target=examples[index];features=online(row)
            q=emb[name][None].to(a.device)
            if task=='T2':
                hw=tuple(max(1,int(x)//4) for x in row['image_size_hw'])
                logits=head(features,q,hw);y=torch.from_numpy(resize_mask(target,hw).copy()).float().to(a.device)[None]
                prob=logits.sigmoid();dice=1-(2*(prob*y).sum()+1)/(prob.sum()+y.sum()+1)
                loss=F.binary_cross_entropy_with_logits(logits,y)+dice
            else:loss=F.binary_cross_entropy_with_logits(head(features,q),torch.tensor([target],device=a.device))
            # Microbatching keeps dense-map memory constant; one update per four examples.
            (loss/batch_size).backward();losses.append(float(loss.detach()))
        optimizer.step()
        if (step+1)%100==0:print(json.dumps(dict(task=task,step=step+1,loss=float(np.mean(losses)),seconds=time.monotonic()-start)),flush=True)
    head.eval();by_scene=collections.defaultdict(list);frames=collections.defaultdict(dict)
    for g in groups:by_scene[g['scene']].append(g)
    for row in tune:frames[row['scene']][row['slot']]=row
    records=[];input_pins=dict(pins)
    with torch.inference_mode():
        for scene,gs in sorted(by_scene.items()):
            gt=tuning_gt(scene);input_pins[gt['path']]=gt['sha256']
            paths={c['mask_ref']['path'] for g in gs for c in g['candidates']}
            if len(paths)!=1:raise ValueError('A tuning scene must use one native SAM cache')
            path=next(iter(paths));payload=load_payload(path);input_pins[path]=sha256(path)
            objects={g['object_id']:dict(object_id=g['object_id'],scene=scene,frames=[],scores=[],labels=[],strict=[],sam_scores=[]) for g in gs}
            for slot in range(32):
                row=frames[scene][slot];features=online(row)
                for g in gs:
                    name=g['name'];r=objects[g['object_id']];truth=gt_mask(gt,name,slot)
                    raw=payload['frames'][str(slot)]['phrases'][candidate_phrase(g)]
                    masks=[decode_rle(x['mask']) for x in raw['instances'] if float(x['score'])*float(raw['presence'])>.5]
                    sam=np.logical_or.reduce([resize_mask(m,truth.shape) for m in masks]) if masks else np.zeros_like(truth)
                    strict=any(iou(resize_mask(m,truth.shape),truth)>.5 for m in masks) and bool(truth.any())
                    q=emb[candidate_phrase(g)][None].to(a.device)
                    if task=='T2':
                        pred=head(features,q,(120,160))[0].sigmoid().cpu().numpy()>.5;pred=resize_mask(pred,truth.shape)
                        r['frames'].append(dict(slot=slot,sam_iou=iou(pred,sam),gt_iou=iou(pred,truth),
                                          sam_valid=bool(sam.any()),gt_valid=bool(truth.any()),
                                          area=float(truth.mean()) if truth.any() else float(sam.mean())))
                    else:
                        r['scores'].append(float(head(features,q).sigmoid()[0]));r['labels'].append(bool(labels[g['object_id']]['frame_presence'][slot]))
                        r['strict'].append(strict)
                        r['sam_scores'].append(max([float(x['score'])*float(raw['presence'])*float(decode_rle(x['mask']).mean()) for x in raw['instances']],default=0.))
            for r in objects.values():
                if task=='T3':
                    ours=sorted(range(32),key=lambda k:(-r['scores'][k],k))[:4]
                    sam=sorted(range(32),key=lambda k:(-r['sam_scores'][k],k))[:4]
                    r.update(shortlist=ours,sam_shortlist=sam,shortlist_hit=float(any(r['strict'][k] for k in ours)),
                             sam_shortlist_hit=float(any(r['strict'][k] for k in sam)))
                records.append(r)
    torch.save(dict(state_dict={k:v.cpu() for k,v in head.state_dict().items()},feature_dim=sample.shape[-1],arm=a.arm,
                    rules_sha256=sha256(RULES_PATH),name_rows_sha256=nb.rows_sha256),out/(task.lower()+'_head.pt'))
    summary=summarize_t2(records) if task=='T2' else summarize_t3(records)
    output_metrics(out/(task+'.json'),dict(arm=a.arm,readout=getattr(a,'readout','four'),task=task,status='complete',metrics=summary,records=records,
                    fit_steps=steps,batch_size=batch_size,shuffle='global frame permutation each epoch, seed 17; all arms including G3T',training_frames=len(examples),parameters=count,encoder_calls=online.calls,
                    input_pins={**input_pins,**online.pins},name_rows_sha256=nb.rows_sha256,
                    encoders={k:v.metadata for k,v in online.encoders.items()},tokenizer_sha256=nb.tokenizer_sha256,
                    strict_definition='At least one native-gate SAM mask in the top four frames has GT IoU >0.5'),
                    [a.labels,a.train,a.tuning,a.weights,RULES_PATH,Path(__file__)],vars(a))


def main(task):
    p=argparse.ArgumentParser();p.add_argument('--arm',choices=ARMS,required=True);p.add_argument('--weights',required=True)
    p.add_argument('--readout',choices=['four','final','unstandardized'],default='four');p.add_argument('--labels');p.add_argument('--out',required=True);p.add_argument('--device',default='cuda:0')
    p.add_argument('--feature-root',required=True)
    p.add_argument('--train',default=str(ROOT/'out/b2_manifest.jsonl'));p.add_argument('--tuning',default=str(ROOT/'out/tuning_manifest.jsonl'))
    run(task,p.parse_args())
