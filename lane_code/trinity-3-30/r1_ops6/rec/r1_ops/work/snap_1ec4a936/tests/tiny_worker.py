"""Native tiny-model all-rank checks; synthetic pixels never certify production RGB."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--tree',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
p.add_argument('--out',type=Path,required=True);p.add_argument('--audit',type=Path);a=p.parse_args()
sys.path[:0]=[str(a.tree),str(a.tree/'generator/derivgen_v7')]
import torch
from student_pilot import carrier_c1_run as run,carrier_c1_data as data
from student_pilot.carrier_c1 import parameter_groups
from tests.test_carrier_c1 import fixture
cfg=json.loads(a.config.read_text());torch.set_num_threads(1)
class Tokens:
    _c1_frame_markers=True
    def encode(self,text,**kw):
        if text=='<|fim_middle|>':return [5]
        return [6+int.from_bytes(hashlib.sha256(w.encode()).digest()[:2],'big')%50 for w in text.split()] or [6]
    def convert_tokens_to_ids(self,text):return {'<|fim_middle|>':5,'<|video_pad|>':61,'<|vision_start|>':62,'<|vision_end|>':63}[text]

# Tiny tokens cover the full supplied text; images and non-VQA rows are fixtures.
def batch_for(model,target,rank,index,text='fixture answer',question='fixture question'):
    tok=Tokens();q=tok.encode(question);tail=tok.encode(text);prefix=[2]+[v for _ in range(32) for v in (62,61,63)]+q
    ids=torch.tensor([prefix+tail]);labels=torch.full_like(ids,-100);labels[0,len(prefix):]=ids[0,len(prefix):]
    g=torch.Generator().manual_seed(10000+rank*100+index%100)
    batch=dict(input_ids=ids,attention_mask=torch.ones_like(ids),labels=labels,
        mm_token_type_ids=torch.where(ids==61,2,0),video_grid_thw=torch.tensor([[32,2,2]]),
        pixel_values_videos=torch.randn(128,24,generator=g))
    return data.insert_frame_carriers(batch,tok,carrier_placement=cfg['carrier_placement'],frame_layout='duplicate')

counts=dict(pose=101,vqa=103,pointing=107,routing=109)
plan=list(data.mixed_indices(counts,1,seed=17,training_mode='final',mix=cfg['recipe']['mix'],world=4))[0]
real={};audit=None
if a.audit:
    import sqlite3
    audit=json.loads(a.audit.read_text());plan=audit['first_step']
    source=audit['source_streams']['vqa'];ids=json.loads(Path(source['indices']['path']).read_text())
    db=sqlite3.connect(Path(source['database']['path']).as_uri()+'?mode=ro&immutable=1',uri=True)
    for stream,indices in plan:
        if stream=='vqa':
            for index in indices:
                r=json.loads(db.execute('SELECT row FROM rows WHERE i=?',(ids[index],)).fetchone()[0]);real[index]=r
    db.close();counts={s:v['count'] for s,v in audit['source_streams'].items()}
reports=[]
for rank in range(4):
    model,_,targets=fixture(16,training_mode='final');model.frame_layout='duplicate'
    model.auxiliary_heads.depth.config.p3['frame_layout']='duplicate'
    model.depth_fov_source=cfg['depth_fov_source'];model.recipe=copy.deepcopy(cfg['recipe'])
    class Rows:
        h1=cfg.get('h1',{})
        def count(self,stream):return counts[stream]
        def get(self,stream,index):
            row=real.get(index) if stream=='vqa' else None
            batch=batch_for(model,targets,rank,index,row['target'] if row else 'fixture answer',row['student_input']['question'] if row else 'fixture question')
            return batch,targets if stream=='pose' else None,dict(qid=row['qid'] if row else 'fixture',index=index)
    rows=Rows()
    if a.audit:
        records=run.check_plan_rows(model,rows,[plan],[rank])
        assert len(records)==72 and all(r.get('finite') for r in records),[r for r in records if not r.get('finite')][:2]
        reports.append(dict(rank=rank,rows=len(records),real_vqa=sum(r['stream']=='vqa' for r in records),records=records))
    else:
        optimizer=torch.optim.AdamW(parameter_groups(model,model.recipe),weight_decay=model.recipe['weight_decay'])
        report,_=run.optimize_step(model,optimizer,rows,plan,rank,torch.device('cpu'),1)
        h=hashlib.sha256()
        for name,value in sorted(model.state_dict().items()):
            h.update(name.encode());h.update(value.detach().cpu().contiguous().numpy().tobytes())
        reports.append(dict(rank=rank,state_sha256=h.hexdigest(),components=report.get('components'),rows=len(plan)))
a.out.write_text(json.dumps(dict(status='PASS',ranks=reports,config_identity=run.identity(cfg),production_admission=False,
    scope='Native tiny model; all 72 microsteps per rank; synthetic pixels and auxiliary streams; real VQA targets where audit supplied.'),sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','ranks':len(reports),'output':str(a.out)}))
