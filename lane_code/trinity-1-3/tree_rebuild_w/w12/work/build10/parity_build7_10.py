"""Replay original reader inputs and weights in place through the current reader."""
from pathlib import Path
from types import SimpleNamespace
import hashlib,json,sys,collections
L=Path(__file__).resolve().parents[2];N=L;B=L/'work/build10';T=L/'work/tree_r1'
sys.path[:0]=[str(B),str(T)]
from monitor9 import Monitor
monitor=Monitor(T)
import torch
from eat1.adapters.c8r_tiny import C8rTinyReader,ProgramPolicy
from eat1.adapters.gf1_tiny import GF1TinyReader
out=L/'work/build12/proofs/parity_build7';out.mkdir(exist_ok=True)
records=[];counts={};inputs=[]
for kind,cls in [('gf1',GF1TinyReader),('c8r',C8rTinyReader)]:
    root=N/'work/build7/proofs/eat1'/kind
    if kind=='gf1':
        from tests.test_gf1 import fixture
        from tests.test_batched_routed_decode import Tokenizer
        model,batch,_=fixture();model.trace_program_version=None
        processor=SimpleNamespace(tokenizer=Tokenizer(),_routing_tokens={'ids':{'<depth_at':40,'<move':45,'<turn':47,'<pose':33}})
    else:
        from tests.test_batched_routed_decode import fixture
        model,processor,batch=fixture()
    model.eat1_program_policy=ProgramPolicy()
    weights=root/'artifact/weights.pt'
    state=torch.load(weights,map_location='cpu',weights_only=True)
    result=model.load_state_dict(state,strict=False)
    assert not result.unexpected_keys,result
    assert all(k.startswith(('auxiliary_heads.depth_readout.','auxiliary_heads.heading.')) for k in result.missing_keys),result
    current=model.state_dict()
    assert all(torch.equal(current[k],v) for k,v in state.items())
    inputs.append(dict(reader=kind,weights=str(weights),sha256=hashlib.sha256(weights.read_bytes()).hexdigest(),
        missing_registered_buffers=result.missing_keys,all_original_tensors_identical=True))
    reader=cls.__new__(cls);reader.model=model.eval();reader.batch=batch;reader.processor=processor;reader.tokenizer=processor.tokenizer
    policy=model.eat1_program_policy
    model.model.register_forward_pre_hook(policy.see,with_kwargs=True)
    model.lm_head.register_forward_hook(lambda m,a,value:policy(value))
    before={v['id']:v for v in map(json.loads,(root/'run/ITEMS.jsonl').read_text().splitlines())}
    for row in map(json.loads,(root/'items.jsonl').read_text().splitlines()):
        frame=root/'frames'/Path(row['frames']).name
        previous=(before[row['id']].get('output') or {}).get('calls',[])
        record=dict(reader=kind,id=row['id'],frames=str(frame),frames_sha256=hashlib.sha256(frame.read_bytes()).hexdigest(),before=previous)
        try:
            actual=reader.generate(str(frame),row['question']);record['after']=actual['calls']
        except Exception as exc:
            record['error']=type(exc).__name__+': '+str(exc);record['after']=[]
        for call in previous:
            response=call['response'];name=call['call'].split()[0].lstrip('<')
            if not any(ch.isdigit() for ch in response):continue
            count=counts.setdefault(kind+'/'+name,dict(checked=0,identical=0,different=0,blocked=0))
            matches=[v for v in record['after'] if v['call']==call['call']]
            if not matches:count['blocked']+=1;continue
            same=matches[0]['response']==response
            count['checked']+=1;count['identical']+=same;count['different']+=not same
        records.append(record)
result=dict(status='FAIL' if any(v['different'] for v in counts.values()) else 'PASS_AVAILABLE_NUMERIC_RESPONSES',
    counts=counts,inputs=inputs,records=records,
    limitations=['Original tiny native LM and tower stand-ins remain CPU fixtures. The new artifact buffers use declared producer constants; every original weight tensor is identical.',
    'Out-of-range pose and empty ground have no numeric response to compare. No gap or heading-availability response input occurs in these reader items.'])
(out/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n');monitor.save(out)
print(json.dumps(dict(status=result['status'],counts=counts)))
