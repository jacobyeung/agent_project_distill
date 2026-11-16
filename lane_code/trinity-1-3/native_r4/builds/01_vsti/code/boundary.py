"""Deterministic CPU model boundary; the production token/response loop stays live."""
from types import SimpleNamespace as NS
import numpy as np

class Tokenizer:
    eos_token_id=0
    pad_token_id=0
    def encode(self,text,add_special_tokens=False):
        pieces=text.split('</think>');result=[]
        for i,piece in enumerate(pieces):
            if i:result.append(1050)
            result.extend(ord(c)+1 for c in piece)
        return result
    def decode(self,ids,skip_special_tokens=False):return ''.join('</think>' if i==1050 else chr(i-1) if 0<i<1024 else '' for i in ids)
    def convert_tokens_to_ids(self,text):return {'<tool_response>':1100,'</tool_response>':1101}.get(text,1102)
    def convert_ids_to_tokens(self,ids):return [self.decode([i]) for i in ids] if isinstance(ids,list) else self.decode([ids])
    def __len__(self):return 1200

class Boundary:
    synthetic=True
    def __init__(self):self.info=dict(synthetic=True,boundary='model load, prefill and sampled token logits')
    def prefill(self,state):return np.full((32,51,51),2.),np.array([0.,-1.,0.])
    def generate(self,task,row,geo):
        from adapter import CAMERA
        from policy import camera_only
        import perception as P
        import reader_policy as Q
        from student_pilot import trace_format313 as F
        from student_pilot.carrier_c1_batch_decode import Row
        import torch
        torch.set_num_threads(4)
        tok=Tokenizer();processor=NS(tokenizer=tok)
        pair=task.get('pair',[1,2])
        call=f'<move from={pair[0]} to={pair[1]}>' if task['question_type'] in CAMERA else '<ground obj="chair" mode="box">'
        text='<think>\n'+call+'\n<depth_at frame=1 x=500 y=500>\n</think>\n'+('A' if task['options'] else '1.0')
        return drive(text,geo,processor=processor,budget=Q.DECODE_BUDGET)

def drive(text,geo,processor=None,budget=None):
    import torch
    import perception as P
    import reader_policy as Q
    from policy import camera_only
    from student_pilot import trace_format313 as F
    from student_pilot.carrier_c1_batch_decode import Row
    tok=Tokenizer() if processor is None else processor.tokenizer
    processor=processor or NS(tokenizer=tok)
    @F.bind_generate
    def generate(model,processor,batch):
        heads=NS(mdg_states=None,mdg_backend=None,grounding_head=None,queries=[])
        state=NS(heads=heads,geometry=None,geometry_error=None,tool_context=NS(),ground_backend=None,
                 mdg=None,verify_session=None,rereader=None,native=NS(generation_config=NS(eos_token_id=0)),
                 cap=20000,openers=set(),prompt_length=1)
        F.bind_state(state)
        guard=Q.ThinkingBudget(tok,budget,openers=[]) if budget else None
        r=Row(state,processor,model,mode='own',pose_source='own',max_calls=200,max_new_tokens=20000,logits_processor=guard)
        candidates=iter(tok.encode(text)+[0]);count=0
        while r.finish is None:
            token=next(candidates,0) if not r.forced else 0
            logits=torch.full((1,len(tok)),-100.);logits[0,token]=100.
            r.step(logits);count+=1
            if count>20000:raise ValueError('fixture token loop did not finish')
        decoded=r.record()
        return Q.apply_budget(decoded,guard) if guard else decoded
    with camera_only():
        return generate(NS(trace_program_version='3.14',carrier_id=1103),processor,{},trace_session=P.session(geo))
