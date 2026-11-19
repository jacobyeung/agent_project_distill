"""A4 real.generate_real with a sampler after its unchanged ThinkingBudget."""
from contextlib import contextmanager
import torch
from .choice import align

class MaxCalls(Exception):
    """The cap-reaching call is recorded without invoking its server."""



class SamplingProcessor:
    def __init__(self, budget, *, seed, temperature=.7, greedy=False, prefix_ids=(), test_sample_cap=None):
        self.budget=budget; self.temperature=temperature; self.greedy=greedy
        self.generator=torch.Generator().manual_seed(seed)
        self.prefix=list(prefix_ids);self.test_sample_cap=test_sample_cap
        self.chosen=[];self.kinds=[];self.logp_tempered=[];self.logp_raw=[]

    def __call__(self, ids, logits):
        before=self.budget.forced_tokens
        scores=self.budget(ids,logits)
        kind='s'
        if self.budget.forced_tokens>before:
            token=int(scores.argmax(-1));kind='b'
        elif len(self.chosen)<len(self.prefix):
            token=self.prefix[len(self.chosen)];kind='f'
        elif self.test_sample_cap is not None and self.kinds.count('s')>=self.test_sample_cap:
            token=self.budget.eos;kind='b'
        elif self.greedy:
            token=int(scores.argmax(-1))
        else:
            probs=torch.softmax(scores[0]/self.temperature,-1)
            token=int(torch.multinomial(probs.cpu(),1,generator=self.generator))
        self.chosen.append(token);self.kinds.append(kind)
        self.logp_tempered.append(float(torch.log_softmax(logits[0]/self.temperature,-1)[token]))
        self.logp_raw.append(float(torch.log_softmax(logits[0],-1)[token]))
        forced=scores.new_full(scores.shape,-float('inf'));forced[:,token]=0
        return forced


def capped_hook(processor, question_type):
    from e2e_reader.callhook import CallHook,call_family
    from .serving import call_caps
    caps=call_caps()
    class CappedHook(CallHook):
        def respond(self, call):
            cap=caps.get(question_type)
            if cap is not None and sum(self.counts.values())+1>=cap:
                family=call_family(call);self.counts[family]+=1;self.unserved[family]+=1
                self.records.append(dict(call=call,family=family,served=False,at_token=len(self.ids)))
                raise MaxCalls()
            return super().respond(call)
    return CappedHook(processor.tokenizer,processor._routing_tokens['ids'].values())


@contextmanager
def capped_decode():
    from e2e_reader import real
    original=real.decode_loop
    def decode(*args,**kwargs):
        try:return original(*args,**kwargs)
        except MaxCalls:return 'max_calls'
    real.decode_loop=decode
    try:yield
    finally:real.decode_loop=original


def sample(model,processor,batch,*,seed=17,temperature=.7,decode,greedy=False,
           prefix='',test_sample_cap=None):
    from .serving import reader_runtime
    # Preserve caller exception classes as well as the sealed helper classes.
    from student_pilot.carrier_c1_batch_decode import RowRefusal
    from student_pilot.tower_errors import TowerError
    try:
        with reader_runtime():
            return _sample(model,processor,batch,seed=seed,temperature=temperature,
                    decode=decode,greedy=greedy,prefix=prefix,test_sample_cap=test_sample_cap)
    except (RowRefusal,TowerError) as exc:return refused(exc)


def _sample(model,processor,batch,*,seed,temperature,decode,greedy,prefix,test_sample_cap):
    from e2e_reader.real import generate_real
    from student_pilot.tower_errors import TowerError
    from .serving import budget
    choice=SamplingProcessor(budget(processor),seed=seed,temperature=temperature,greedy=greedy,
            prefix_ids=processor.tokenizer.encode(prefix,add_special_tokens=False),test_sample_cap=test_sample_cap)
    model.eval()
    # A4's perception build raises plain ValueErrors (no_scale_points, GeometryError) outside its
    # call guard; they refuse this draw. align stays outside, so kit misalignment still raises.
    try:
        with capped_decode():
            record=generate_real(model,processor,batch,budget=choice,max_new_tokens=16384,**decode)
    except (TowerError,ValueError) as exc:return refused(exc)
    record['call_report']=record['calls'];record['calls']=record['calls']['records']
    kinds,tempered,raw=align(record,choice)
    record.update(kinds=kinds,logp_tempered=tempered,logp_raw=raw,temperature=temperature,top_p=1.,
            budget_hit=choice.budget.trigger is not None,seed=seed,
            decode_budget=choice.budget.receipt(len(record['tokens'])),
            errors=sum(c.get('kind')=='error' for c in record['calls']),
            strict_no_answer=record['finish']=='max_calls')
    return record


def native_kwargs(processor,prompt,batch,reader):
    memo=getattr(reader['perception'],'memo',None)
    if memo is not None:memo.item_id=str(prompt['prompt_id'])
    return dict(reader,frames=reader_frames(prompt['row'],batch),hook=capped_hook(processor,prompt['type']))


def reader_frames(row,batch):
    from student_pilot.tower_errors import tower_guard
    return tower_guard(_reader_frames)(row,batch)


def _reader_frames(row,batch):
    from PIL import Image
    from student_pilot.r2_frames import verify_frame
    source=row['student_input'].get('geometry_dense',row['student_input'])
    indices=source['frame_indices']
    if len(indices)!=len(source['frames']) or len(indices) not in (32,64):
        raise ValueError('MISSING complete native dense frame selection')
    anchors=batch['frame_indices']
    if len(set(indices))!=len(indices) or any(i not in indices for i in anchors):
        raise ValueError('Native LM/dense frame indices disagree')
    images=[]
    for pin in source['frames']:
        with Image.open(verify_frame(pin)) as im:
            if im.mode!='RGB':raise ValueError('Native frame must be RGB')
            images.append(im.copy())
    return dict(native_frames=images,dense_indices=list(indices),
                anchor_slots=[indices.index(i) for i in anchors],anchor_indices=list(anchors))


def refused(exc):
    return dict(text='',tokens=[],calls=[],kinds=[],logp_tempered=[],logp_raw=[],
                finish='refused',refusal=type(exc).__name__+': '+str(exc))
