import json, sys, torch, math
from owngrd.train import *
from owngrd.train import DEFAULT_WEIGHTS, DEFAULT_BUNDLE
from owngrd.data import GroundingDataset
from owngrd.head import GroundingHead, Config, pooled_name
from owngrd.losses import mask_iou, compute_losses, at_points
from owngrd.vit import FrozenViT
torch.set_num_threads(8)
S='/dev/shm/jjyeung/b05/pilot'; W='/scratch/jjyeung/orch_n30/b05_owngrd/work'
run=json.load(open(S+'/RUN.json'))
val=GroundingDataset(W+'/manifests/TRAIN_K1_113.json', W+'/labels_k1', W+'/teacher_k1_full/teacher_k1','train_val',(480,640),seed=42)
train=GroundingDataset(W+'/manifests/TRAIN_K1_113.json', W+'/labels_k1', W+'/teacher_k1_full/teacher_k1','train',(480,640),seed=42)
vit=FrozenViT(DEFAULT_WEIGHTS, DEFAULT_BUNDLE, 'cpu')
model=GroundingHead(Config()); st=torch.load(S+'/resume.pt',map_location='cpu',weights_only=False)
model.load_state_dict(st['model']); print('loaded step', st['cursor']['step'])
def stats(tag, ds, idxs, mode):
    model.train(mode=='train')
    n=0
    for index in idxs:
        item=ds[index]
        if item['target']['role']!='gt': continue
        with torch.no_grad():
            batch=encode_item(vit,item)
            out=model(**batch)
            loss,det=compute_losses(out,[item['target']],model.cfg)
        print(tag,mode,index,item['name'],'pix',tuple(batch['pixels'].shape),'masks',tuple(out['masks'].shape),'dice_loss',round(float(loss['mask_dice']),3),'cands',len(out['candidates'][0]),'maxscore',round(float(out['scores'][0].max()),3))
        for f,m in enumerate(det['matches'][0]):
            for q,t in m:
                p=out['masks'][0,f,q]; g=t['mask']
                prob=p.sigmoid(); hard=prob>.5
                sd=float(2*(prob*g).sum()/(prob.sum()+g.sum()+1))
                print('   f',f,'q',q,t['cls'],'gtshape',tuple(g.shape),'iou',round(float(mask_iou(prob,g)),3),'softdice_full',round(sd,3),'pred_area',round(float(hard.float().mean()),3),'gt_area',round(float(g.mean()),3),'prob_mean',round(float(prob.mean()),3),'logit_range',round(float(p.min()),1),round(float(p.max()),1))
            gm=item['target']['decoder'][f]['gt_masks']
            for i,g in gm.items():
                best=max(float(mask_iou(out['masks'][0,f,qq].sigmoid(),g)) for qq in range(out['masks'].shape[2]))
                print('   f',f,'gtraster',i,'area',round(float(g.mean()),3),'best_query_iou',round(best,3))
        n+=1
        if n>=3: break
vi=run['validation_indices']
stats('VAL',val,vi[:40],'eval')
stats('VAL',val,vi[:40],'train')
stats('TRN',train,list(range(0,400,7)),'eval')
