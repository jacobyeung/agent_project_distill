"""Deterministic pool from N's prepared native reader, never from unadmitted slices."""
import argparse
import copy
import hashlib
from . import provenance as P

# Model-visible fields are explicit. Scoring labels live only in prompt.gt_answer.
ROW_FIELDS=('qid','dataset','scene','canonical','question_type','category',
            'mask_source','uses_mask_cache')
INPUT_FIELDS=('question','options','frame_indices','timestamps','fps','total_num_frames',
              'anchor_slots','recording_id','video_sha256')
FRAME_FIELDS=('path','sha256','frame_index','timestamp','recording_id','timestamp_seconds')


def clean_inputs(inputs):
    clean={k:copy.deepcopy(inputs[k]) for k in INPUT_FIELDS if k in inputs}
    for key in ('frames','partner_frames'):
        if key in inputs:
            clean[key]=[{k:copy.deepcopy(f[k]) for k in FRAME_FIELDS if k in f} for f in inputs[key]]
    if 'video_identity' in inputs:
        clean['video_identity']={k:copy.deepcopy(inputs['video_identity'][k])
                                 for k in ('video_sha256',) if k in inputs['video_identity']}
    if 'geometry_dense' in inputs:clean['geometry_dense']=clean_inputs(inputs['geometry_dense'])
    return clean


def clean_row(row):
    clean={k:copy.deepcopy(row[k]) for k in ROW_FIELDS if k in row}
    clean['student_input']=clean_inputs(row['student_input'])
    if isinstance(row.get('routing'),dict):
        clean['routing']={k:copy.deepcopy(row['routing'][k])
                          for k in ('question_type','category') if k in row['routing']}
    # Preserve only phrase strings, never arbitrary cache/manifest dictionaries.
    for key in ('batch_cache_phrases','candidate_phrases','cache_phrases'):
        if key in row:
            value=row[key].get('phrases') if isinstance(row[key],dict) else row[key]
            if not isinstance(value,(list,tuple)) or not all(isinstance(x,str) for x in value):
                raise ValueError('Invalid phrase input: '+key)
            clean[key]=list(value)
    return clean

def assert_prompt_equal(raw,clean,prompt_encoder):
    import torch
    before=prompt_encoder(raw)['input_ids']
    after=prompt_encoder(clean)['input_ids']
    if not torch.equal(torch.as_tensor(before),torch.as_tensor(after)):
        raise ValueError('Cleaned row changes native prompt ids: '+str(raw.get('qid')))


class RoomGate:
    def __init__(self,cfg):
        from student_pilot.r1_rooms import Rooms
        from student_pilot.r2_withheld import Withheld
        from student_pilot.r0_exclusion import reserve
        from student_pilot.row_removals import Removals
        from student_pilot.s1_exclusions import Exclusions
        for p in cfg['r1_training']['room_authority'].values(): P.checked(p)
        for p in cfg['remove_files']: P.checked(p)
        P.checked(cfg['dev_scene_exclusions']); P.checked(cfg['benchmark_scene_exclusions'])
        self.rooms=Rooms(cfg['r1_training']['room_authority'])
        self.withheld=Withheld(); self.reserve=reserve(); self.removals=Removals(cfg['remove_files'])
        self.exclusions=Exclusions(cfg['dev_scene_exclusions'],cfg['benchmark_scene_exclusions'])
    def admit(self,row):
        self.rooms.admit(row); self.reserve.check(row,'rl')
        self.removals.assert_clean(row)
        canonical,_=self.rooms.canonical(row)
        if self.withheld.touches(row,{'names':[canonical]}): raise ValueError('RL_WITHHELD_ROOM_REFUSED')
        if self.exclusions.excluded(row): raise ValueError('RL_DEV_OR_BENCHMARK_REFUSED')


def build(rows,gate,route_table,seed=17,limit=None,*,prompt_encoder):
    result={}
    for stream,index,row in rows:
        gate.admit(row)
        qid=str(row['qid']); typ=row.get('question_type') or row.get('routing',{}).get('question_type')
        if typ not in route_table: raise ValueError('Unknown question type: '+str(typ))
        si=row['student_input']
        if len(si['frame_indices']) not in (32,64): raise ValueError('Invalid native frame count')
        answer=row.get('answer',row.get('routing',{}).get('answer'))
        if answer is None: raise ValueError('MISSING ground truth answer for '+qid)
        # Copy only model inputs and metadata needed by native prompt_batch/backend.
        clean=clean_row(row)
        assert_prompt_equal(row,clean,prompt_encoder)
        value=dict(prompt_id=qid,type=typ,gt_answer=str(answer),options=si.get('options') or [],
                   row=clean,source_stream=stream,source_offset=index,
                   source_row_sha256=hashlib.sha256(P.canonical(row).encode()).hexdigest())
        if qid in result:
            # An item represented in two streams is not silently counted twice.
            raise ValueError('Duplicate prompt ID: '+qid)
        result[qid]=value
    ordered=sorted(result.values(),key=lambda p:(hashlib.sha256(f'{seed}|{p["prompt_id"]}'.encode()).hexdigest(),p['prompt_id']))
    return ordered if limit is None else ordered[:limit]


def from_prepared(cfg,seed=17,limit=None):
    from student_pilot.carrier_c1_run import prepared,Rows
    from student_pilot.r1_training import training_components
    from student_pilot.r1_rooms import verify_audit
    from student_pilot.s1_route_policy import validate
    validate(cfg); training_components(cfg['r1_training']['registry'],cfg)
    verify_audit(cfg,cfg['r1_training']['room_audit'])
    receipt,manifest=prepared(cfg,admission=True)
    from student_pilot.carrier_c1_run import processor_for_receipt
    from evalpath.runtime import prompt_batch
    processor=processor_for_receipt(manifest,receipt)
    if not receipt.get('r2_membership'): raise ValueError('MISSING native admitted row membership')
    reader=Rows(receipt,None); gate=RoomGate(cfg)
    def rows():
        for stream in ('vqa','routing'):
            for i in range(reader.count(stream)):
                row,_=reader.row(stream,i)
                yield stream,i,row
    try: return build(rows(),gate,cfg['route_table'],seed,limit,
                      prompt_encoder=lambda row:prompt_batch(processor,row,cfg,'routed'))
    finally: reader.close()

def main():
    p=argparse.ArgumentParser(); p.add_argument('--tree',required=True); p.add_argument('--config',required=True)
    p.add_argument('--out',required=True); p.add_argument('--limit',type=int); a=p.parse_args()
    P.tree(a.tree); cfg=P.load(a.config)
    prompts=from_prepared(cfg,limit=a.limit)
    P.write(a.out,dict(schema='rl-on-n-pool-v1',status='ADMITTED',prompts=prompts,seed=17,source_config=P.pin(a.config)))
if __name__=='__main__': main()
