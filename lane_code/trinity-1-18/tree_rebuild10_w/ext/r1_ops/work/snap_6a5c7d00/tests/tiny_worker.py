"""Native tiny-model all-rank checks; synthetic pixels never certify production RGB."""
import argparse,copy,hashlib,json,sys
from pathlib import Path
from unittest.mock import patch
p=argparse.ArgumentParser();p.add_argument('--tree',type=Path,required=True);p.add_argument('--config',type=Path,required=True)
p.add_argument('--out',type=Path,required=True);p.add_argument('--audit',type=Path);a=p.parse_args()
sys.path[:0]=[str(a.tree),str(a.tree/'generator/derivgen_v7')]
import torch
from student_pilot import carrier_c1_run as run,carrier_c1_data as data
from student_pilot import carrier_c1_routing as routing
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
        seen=[]
        routing_count=0
        def count(self,stream):return counts[stream]
        def get(self,stream,index):
            row=real.get(index) if stream=='vqa' else None
            batch=batch_for(model,targets,rank,index,row['target'] if row else 'fixture answer',row['student_input']['question'] if row else 'fixture question')
            if a.audit and stream=='routing':
                # Exercise H1's actual Rows.get target path, replacing only RGB/token
                # encoding with the existing tiny-model fixture boundary.
                kind=(*routing.CAMERA_MOTION,'absolute_distance_object','absolute_distance_object')[self.routing_count%5]
                unit=self.routing_count%5==4;self.routing_count+=1
                frames=[rank*1000+self.routing_count*64+2*i for i in range(32)]
                pose=[[i*.01,self.routing_count*.01,0.,0.,0.,0.,1.,1.,1.] for i in range(32)]
                events=[dict(kind='plan',text='Measure the requested geometry.')]
                target,spans=routing.render(events,'2')
                raw=dict(schema='derivgen-row-v2',form='spec-v3.8-calculator-v2',infrastructure_only=False,
                    qid='fixture_r%d_%d'%(rank,self.routing_count),question_type=kind,question='How far?',
                    events=events,answer='2',gt_answer='2',target=target,tool_output_spans=spans,
                    gt_pose9=pose,gt_up=[0.,-1.,0.],
                    provenance=dict(canonical='scannet/fixture',frame_indices=frames,source_row_sha256='1'*64))
                rgb=dict(frames=[dict(path='fixture/%d.png'%i,sha256='0'*64,source_index=i) for i in frames],
                         fps=1,total_num_frames=max(frames)+1)
                converted=routing.c1_row(raw,rgb)
                if unit:
                    # Use the actual bound feet row and its production-equal frame pins.
                    unit_path=a.config.parent/'units/packed.jsonl'
                    if not unit_path.exists():unit_path=a.config.parent.parent/'out/units/packed.jsonl'
                    with unit_path.open() as handle:unit_row=json.loads(next(handle))
                    inputs=unit_row['student_input']
                    unit_rgb=dict(frames=[{**pin,'source_index':i} for pin,i in zip(inputs['frames'],inputs['frame_indices'],strict=True)],
                                  fps=inputs['fps'],total_num_frames=inputs['total_num_frames'])
                    converted=routing.c1_row(unit_row,unit_rgb)
                native=object.__new__(run.Rows)
                native.processor=None
                native.h1=self.h1;native.placement=cfg['carrier_placement'];native.mode='final'
                native.layout='duplicate';native.gap=None;native.geometry_online=None;native.mixes={}
                native.row=lambda stream,index:(converted,None)
                with patch.object(routing,'encode',return_value=(batch,dict(qid=converted['qid']))):
                    batch,pose_targets,audit=run.Rows.get(native,stream,index)
                supervised=kind in routing.CAMERA_MOTION and self.h1['routing_pose_targets']
                assert type(self.h1['routing_pose_targets']) is bool and self.h1['faithful_own_camera_rows'] is False
                assert bool(pose_targets is not None and pose_targets['aux_camera_mask'].all())==supervised
                assert bool(pose_targets is not None and pose_targets['aux_gravity_mask'].all())==supervised
                if supervised:
                    assert torch.equal(pose_targets['aux_camera_target'][0],torch.tensor(raw['gt_pose9']))
                    assert converted['student_input']['frame_indices']==frames
                self.seen.append(dict(stream=stream,question_type=converted['routing']['question_type'],
                    family='units/ft' if unit else kind,supervised_frames=int(pose_targets['aux_camera_mask'].sum()) if pose_targets is not None else 0,
                    s2_supervised=supervised,target_matches_own_frames=supervised,
                    h1_pose=audit.get('h1_pose'),frame_indices=converted['student_input']['frame_indices']))
                return batch,pose_targets,audit
            if a.audit:self.seen.append(dict(stream=stream,s2_supervised=False))
            return batch,targets if stream=='pose' else None,dict(qid=row['qid'] if row else 'fixture',index=index)
    rows=Rows()
    if a.audit:
        records=run.check_plan_rows(model,rows,[plan],[rank])
        assert len(records)==72 and all(r.get('finite') for r in records),[r for r in records if not r.get('finite')][:2]
        assert len(rows.seen)==len(records)
        for record,observed in zip(records,rows.seen,strict=True):
            record['s2']=observed
            if observed['s2_supervised']:assert record['components']['pose']>0
            elif record['stream']!='pose':assert record['components']['pose']==0
        reports.append(dict(rank=rank,rows=len(records),real_vqa=sum(r['stream']=='vqa' for r in records),records=records))
    else:
        optimizer=torch.optim.AdamW(parameter_groups(model,model.recipe),weight_decay=model.recipe['weight_decay'])
        report,_=run.optimize_step(model,optimizer,rows,plan,rank,torch.device('cpu'),1)
        h=hashlib.sha256()
        for name,value in sorted(model.state_dict().items()):
            h.update(name.encode());h.update(value.detach().cpu().contiguous().numpy().tobytes())
        reports.append(dict(rank=rank,state_sha256=h.hexdigest(),components=report.get('components'),rows=len(plan)))
extra={}
if a.audit:
    extra['s2_pose_targets']=dict(status='PASS',camera_rows=sum(r['s2']['s2_supervised'] for rank in reports for r in rank['records']),
        s2_enabled=bool(cfg.get('h1',{}).get('routing_pose_targets')),
        non_camera_routing_rows=sum(r['stream']=='routing' and r['s2'].get('family') not in routing.CAMERA_MOTION for rank in reports for r in rank['records']),
        unsupervised_routing_rows=sum(r['stream']=='routing' and not r['s2']['s2_supervised'] for rank in reports for r in rank['records']),
        native_rows_get=True,own_32_frame_targets_exact=True if cfg.get('h1',{}).get('routing_pose_targets') else None,non_camera_pose_loss_zero=True,
        pose_stream_unchanged=True,encoding='Synthetic pixels/tokens; native c1_row, Rows.get, h1.pose_targets, full forward and losses.')
a.out.write_text(json.dumps(dict(status='PASS',ranks=reports,config_identity=run.identity(cfg),production_admission=False,**extra,
    scope='Native tiny model; 72 microsteps per rank; synthetic pixels/camera GT/pose/pointing, bound feet rows and real VQA targets. Native S2 target and loss path; no production RGB or complete routing store.'),sort_keys=True,indent=2)+'\n')
print(json.dumps({'status':'PASS','ranks':len(reports),'output':str(a.out)}))
