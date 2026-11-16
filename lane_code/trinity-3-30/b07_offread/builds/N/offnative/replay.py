"""CPU forced-token proof of the recorded decode protocol, with independent camera responses."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace as NS
import hashlib
from .paths import RET544, TOKENIZER
from .proof import select, compare, CAMERA, loss_record, verify_served, REDUCED_LIMIT
from .io import dump, sha

def replay_row(row, tok, openers, *, changed_response=False, mode='full', loss_pin=None):
    if mode not in ('full', 'reduced'):
        raise ValueError('unknown identity proof mode')
    if row['question_type'] not in CAMERA:
        if mode != 'reduced':
            raise ValueError('distance replay requires original masks or explicit reduced mode')
        record = loss_record(loss_pin)
        if row['key'] not in {m['key'] for m in record['masks']}:
            raise ValueError('distance item has no pinned lost mask')
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
        text=raw,calls=hook.records,finish=finish,heads=deepcopy(dec.get('heads',{}))),
        query_digest_source='recorded journal; no independent distance re-serving',independent_responses=independent,
        token_text_equal=True)

def run(out, *, mode='full', loss_pin=None):
    import torch
    from transformers import AutoTokenizer
    from student_pilot.carrier_c1_routing import add_routing_tokens
    torch.set_num_threads(1)
    path = RET544/'native/paired/results/items.jsonl'
    selected = select(path)
    if mode == 'reduced':
        loss_record(loss_pin, selected, journal=path, keys=out/'PROOF_KEYS.json')
    else:
        raise ValueError('CPU distance proof needs explicit reduced mode and pinned lost masks')
    dump(out/'PROOF_KEYS.json',dict(selection='Five camera and five distance items, ascending SHA256 of key, unflagged arm.',
        source_sha256=sha(path),keys=[dict(key=r['key'],question_type=r['question_type'],
        key_sha256=hashlib.sha256(r['key'].encode()).hexdigest()) for r in selected]))
    tok = AutoTokenizer.from_pretrained(TOKENIZER,local_files_only=True)
    openers = add_routing_tokens(NS(tokenizer=tok))['ids']
    actual = [replay_row(r,tok,openers,mode=mode,loss_pin=loss_pin) for r in selected]
    result = compare(selected,actual,'harness',mode=mode,loss_pin=loss_pin)
    try:
        replay_row(selected[0],tok,openers,changed_response=True)
    except ValueError as exc:
        mutation = dict(rejected=True,reason=str(exc))
    else:
        mutation = dict(rejected=False)
    result.update(cpu_forced_token_protocol=True, mutation=mutation,
        independent_camera_items=5, recorded_response_distance_items=5,
        lost_masks=loss_pin,
        evidence_scope='Forced-token CPU protocol proof; distance query digests and responses come from the pinned journal.',
        not_proven=['GPU logits and model prefill equality.',
                    'Independent re-serving of the five distance responses from the lost original masks.'],
        limitation=REDUCED_LIMIT)
    dump(out/'PROOF_CPU.json',result)
    if not result['passed'] or not mutation['rejected']:
        raise ValueError('CPU protocol proof failed')
    return result

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('out',type=Path)
    p.add_argument('--mode',choices=['full','reduced'],default='full')
    p.add_argument('--lost-masks',type=Path);p.add_argument('--lost-masks-sha256')
    a=p.parse_args()
    pin={'path':str(a.lost_masks),'sha256':a.lost_masks_sha256} if a.lost_masks else None
    result=run(a.out,mode=a.mode,loss_pin=pin)
    print(__import__('json').dumps({k:result[k] for k in ('passed','mode','independent_camera_items','recorded_response_distance_items')},sort_keys=True))
