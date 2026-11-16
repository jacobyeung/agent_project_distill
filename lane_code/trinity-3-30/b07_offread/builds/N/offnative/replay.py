"""CPU forced-token proof of the recorded decode protocol, with independent camera responses."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
import hashlib
from .paths import RET544, TOKENIZER
from .proof import select, compare, CAMERA
from .io import dump, sha

def replay_row(row, tok, openers, *, changed_response=False):
    import torch
    from e2e_reader.callhook import CallHook, decode_loop
    from e2e_reader.servers import ReadServers
    from e2e_reader.geometry import from_npz
    dec = row['decode']; tokens = dec['tokens']; calls = dec['calls']
    cursor = {'token':0,'call':0}
    independent = row['question_type'] in CAMERA
    servers = None
    if independent:
        geometry = from_npz(RET544/'native/geometry'/(row['perception']['clip']+'.npz'))
        servers = ReadServers(geometry).mapping()
    from e2e_reader.callhook import call_family
    def serve(call):
        i = cursor['call']; cursor['call'] += 1
        want = calls[i]
        if want['call'] != call:
            raise ValueError('detected call differs from recorded call')
        if independent:
            text, info = servers[call_family(call)](call)
            if text.encode() != want['response'].encode():
                raise ValueError('independently served camera response differs')
        else:
            text, info = want['response'], {'kind':want.get('kind','ground')}
        if changed_response and i==0: text += ' changed'
        return text, info
    hook = CallHook(tok, openers.values(), ground_layout=True, error_suffix=True)
    hook.begin({family:serve for family in ('move','turn','pose','ground','gap','room','depth_at','other')})
    def logits():
        if cursor['token'] >= len(tokens):
            raise ValueError('reference token stream exhausted')
        x = torch.full((1,1,len(tok)), -1e9)
        x[0,0,tokens[cursor['token']]] = 0
        return NS(logits=x)
    def step(consumed):
        i = cursor['token']
        if consumed != tokens[i:i+len(consumed)]:
            raise ValueError('forced response token ids differ')
        cursor['token'] += len(consumed)
        return logits()
    finish = decode_loop(step, logits(), hook, eos_ids={248046,tok.eos_token_id},
                         cap=max(len(tokens),1)+1)
    raw = tok.decode(hook.ids, skip_special_tokens=False)
    reference_raw = tok.decode(tokens, skip_special_tokens=False)
    if raw != reference_raw or raw != dec['text']:
        raise ValueError('replayed decoded bytes differ')
    if len(hook.records) != len(calls):
        raise ValueError('call count differs')
    for got,want in zip(hook.records,calls):
        for field in ('call','response','at_token','forced_tokens'):
            if got.get(field) != want.get(field):
                raise ValueError('call record differs: '+field)
    return dict(key=row['key'],question_type=row['question_type'],decode=dict(tokens=hook.ids,
        text=raw,calls=hook.records,finish=finish),independent_responses=independent,
        token_text_equal=True)

def run(out):
    import torch
    from transformers import AutoTokenizer
    from student_pilot.carrier_c1_routing import add_routing_tokens
    torch.set_num_threads(1)
    path = RET544/'native/paired/results/items.jsonl'
    selected = select(path)
    dump(out/'PROOF_KEYS.json',dict(selection='Five camera and five distance items, ascending SHA256 of key, unflagged arm.',
        source_sha256=sha(path),keys=[dict(key=r['key'],question_type=r['question_type'],
        key_sha256=hashlib.sha256(r['key'].encode()).hexdigest()) for r in selected]))
    tok = AutoTokenizer.from_pretrained(TOKENIZER,local_files_only=True)
    openers = add_routing_tokens(NS(tokenizer=tok))['ids']
    actual = [replay_row(r,tok,openers) for r in selected]
    result = compare(selected,actual,'harness')
    try:
        replay_row(selected[0],tok,openers,changed_response=True)
    except ValueError as exc:
        mutation = dict(rejected=True,reason=str(exc))
    else:
        mutation = dict(rejected=False)
    result.update(cpu_forced_token_protocol=True, mutation=mutation,
        independent_camera_items=5, recorded_response_distance_items=5,
        not_proven=['GPU logits and model prefill equality.','Independent distance responses: reference ground queries are digests, not arrays.'])
    dump(out/'PROOF_CPU.json',result)
    if not result['passed'] or not mutation['rejected']:
        raise ValueError('CPU protocol proof failed')
    return result

if __name__=='__main__':
    import sys
    print(__import__('json').dumps(run(Path(sys.argv[1])),sort_keys=True))
