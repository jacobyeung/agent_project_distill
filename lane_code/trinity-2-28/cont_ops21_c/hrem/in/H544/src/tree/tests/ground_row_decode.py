"""Drive real generate() from independent row tokens and forced tool bodies.

The decoder handles framing, call detection and token insertion. Only model
numerics and response bodies are stubbed. QueryStream itself runs on each
separate query pass. Ordinary routing tokens must never open the adapter gate.
"""
import argparse
from contextlib import contextmanager, nullcontext
import json
from pathlib import Path
import re
from types import SimpleNamespace as NS
from unittest import mock
import numpy as np
import torch
from transformers import PreTrainedTokenizerFast
from student_pilot import carrier_c1_decode as D, mdg_decode as M, mdg_features as F, mdg_lora
from tests.test_mdg_features import fixture

TOK='/scratch/jjyeung/orch_cd/derivgen/inputs/tokenizer_01/tokenizer.json'
PILOT='/scratch/jjyeung/orch_cd/ground_rows/out/pilot_delivery/candidates.jsonl'
PRODUCTION='/scratch/jjyeung/orch_cd/ground_rows/out/training_delivery/balanced_training_rows.jsonl'


class Logits:
    def __getitem__(self, key): return self
    def __setitem__(self, key, value): pass
    def float(self): return self


class Cache:
    def __init__(self, n): self.n=n
    def get_seq_length(self): return self.n


class Capture:
    def __init__(self, model):
        self.states={'layer':torch.zeros(1,1,2), 'norm':torch.zeros(1,1,2)}
    def __enter__(self): return self
    def __exit__(self,*exc): pass


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--limit',type=int);ap.add_argument('--out',required=True);ap.add_argument('--revision3122',action='store_true')
    args=ap.parse_args()
    torch.set_num_threads(1)
    t=PreTrainedTokenizerFast(tokenizer_file=TOK)
    from student_pilot.carrier_c1_routing import add_routing_tokens
    p=NS(tokenizer=t);add_routing_tokens(p,include_ground=True)
    eos=t.convert_tokens_to_ids('<|im_end|>'); t.eos_token_id=eos
    model,batch=fixture(); model.config.text_config.max_position_embeddings=32768
    model.mdg_head=object();model.mdg_meta={'tau':.5}; model.mdg_lora_config={'rank':2}
    prompt=batch['input_ids'].shape[1]
    native=NS()
    class Native:
        def __init__(self,cfg): self.generation_config=NS(eos_token_id=eos)
        def __call__(self,**kw):
            model.model.language_model.norm(torch.zeros(1,1,model.config.text_config.hidden_size))
            return NS(logits=Logits(),past_key_values=Cache(prompt))
    prefix=NS(taps=[],vit=[],pixels=None,grid=None,hidden=None)
    class Prefix:
        def __init__(self,*a): pass
        def __enter__(self): return self
        def __exit__(self,*a): pass
        def finish(self): return prefix
    class Heads:
        def __init__(self,*a,**kw):
            self.grounding_features=prefix;self.pose9=np.zeros((32,9));self.gravity=None;self.queries=[]
            self.grounding_head=None
        def geometry(self): return None
    reports=[]
    for source in (PILOT,PRODUCTION,'/scratch/jjyeung/orch_cd/ground_rows/out/training_v2_review/balanced_training_rows.jsonl'):
        count=0
        with open(source) as handle:
            for line in handle:
                if args.limit and count>=args.limit: break
                row=json.loads(line);target=row.get('target',row['suffix']); expected=t.encode(target,add_special_tokens=False)
                if args.revision3122:
                    target=re.sub(r', p [0-9]+\.[0-9]{2}\)',')',target)
                    row['events']=[dict(e,response=re.sub(r', p [0-9]+\.[0-9]{2}\)',')',e['response'])) for e in row['events']]
                    expected=t.encode(target,add_special_tokens=False)
                queries=[];events=iter(row['events'])
                # Compare the archived row unchanged; revision 3.12.2 conversion
                # is checked separately without changing the source fixture.
                def respond(call,*a,**kw):
                    e=next(events);assert call==e['call'],(row['qid'],call,e['call'])
                    body=e['response'][len('<tool_response>\n'):-len('\n</tool_response>')]
                    return body,{'kind':'ground' if call.startswith('<ground') else 'gap' if call.startswith('<gap') else 'calculator'}
                def force(ids, logits):
                    # Injected bytes must match the independent training target
                    # before the next model token can be chosen.
                    assert ids==expected[:len(ids)], (row['qid'],len(ids),t.decode(ids[-12:]),t.decode(expected[max(0,len(ids)-12):len(ids)]))
                    token=expected[len(ids)] if len(ids)<len(expected) else eos
                    return NS(argmax=lambda dim: torch.tensor(token))
                def consume(native,ids,attention,cache,**kw):
                    assert kw.get('observer') is None,'main routing stream opened the query gate'
                    cache.n=ids.shape[1]
                    return NS(logits=Logits(),past_key_values=cache),cache
                def query(backend,name):
                    ids,_=F.suffix_tokens(t,name)
                    # Independent training-format tokenization via offsets.
                    encoding=t(f'<ground obj="{name}">',add_special_tokens=False,return_offsets_mapping=True)
                    assert ids==encoding['input_ids']
                    stream=M.QueryStream(model,t);gates=[]
                    @contextmanager
                    def gate(model_,mask):
                        gates.extend(mask.flatten().tolist());yield
                    with mock.patch.object(mdg_lora,'suffix_mask',side_effect=gate),mock.patch.object(F,'_SuffixCapture',Capture):
                        for token in ids:
                            with stream.token(torch.tensor([[token]])): pass
                    stream.finish(name)
                    assert gates==[True]*len(ids),(name,gates)
                    queries.append(dict(name=name,ids=ids,gates=gates))
                    return None
                model.model.rope_deltas=torch.zeros(1,1,dtype=torch.long)
                with mock.patch('transformers.Qwen3_5ForConditionalGeneration',Native), \
                     mock.patch.object(D,'HeadState',Heads),mock.patch.object(M,'PrefixCapture',Prefix), \
                     mock.patch.object(F,'expand_cache',side_effect=lambda c,n:c), \
                     mock.patch.object(D,'consume_cache_tokens',side_effect=consume), \
                     mock.patch.object(D,'respond',side_effect=respond),mock.patch.object(M.Backend,'query',query):
                    record=D.generate(model,p,batch,logits_processor=force)
                assert record['tokens'][:-1]==expected
                assert record['text']==target+t.decode([eos])
                # An independent character-span oracle verifies archived gate
                # positions. The active ORCH contract closes those trace gates;
                # each corresponding separate query is checked above.
                spans=[m.span() for m in re.finditer(r'<ground obj="[^"<>\n]+">',target)]
                offsets=t(target,add_special_tokens=False,return_offsets_mapping=True)['offset_mapping']
                oracle=[i for i,(a,b) in enumerate(offsets) if any(a<end and start<b for start,end in spans)]
                if not args.revision3122: assert oracle==row['mdg_gate_token_positions']
                # Recover absolute call spans from generated IDs, independently
                # of training offsets. No side reuses the other's positions.
                decoded=t.decode(record['tokens'][:-1]);actual=[];cursor=0
                for i,token in enumerate(record['tokens'][:-1]):
                    before=t.decode(record['tokens'][:i]);after=t.decode(record['tokens'][:i+1])
                    if any(len(before)<end and start<len(after) for start,end in spans):actual.append(i)
                assert actual==oracle,(row['qid'],actual,oracle)
                count+=1
                if count%100==0:print(source,count,flush=True)
        reports.append(dict(source=source,revision='3.12.2' if args.revision3122 else 'archived',rows=count,text_equal=True,token_ids_equal=True,call_positions_equal=True,
                            main_adapter_gate='closed',query_gate='all call tokens'))
    Path(args.out).write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(reports))


if __name__=='__main__':main()
