"""Compare two isolated readers on the same seeded text rows without decoding frames."""
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sqlite3
import subprocess
import sys

SEED = 20261123


def write(path, value):
    Path(path).write_text(json.dumps(value, sort_keys=True, indent=1)+'\n')


def selected(database, count, rng, stream):
    with sqlite3.connect(Path(database).resolve().as_uri()+'?mode=ro', uri=True) as c:
        keys = [r[0] for r in c.execute('SELECT i FROM rows ORDER BY i')]
        if len(keys) < count:
            raise ValueError('E91')
        result = []
        for pos in sorted(rng.sample(range(len(keys)), count)):
            i, raw, target = c.execute('SELECT i,row,target FROM rows WHERE i=?', (keys[pos],)).fetchone()
            row = json.loads(raw)
            result.append(dict(key=[stream, i, str(row.get('qid', row.get('id', '')))],
                               position=pos, row=row, stored_target=target))
        return result


def evaluate(processor, cfg, samples):
    import numpy as np
    from unittest.mock import patch
    from student_pilot import carrier_c1_data as data, carrier_c1_routing as routing, pose_samples
    from student_pilot.batches import training_text
    records = []
    for sample in samples:
        row = sample['row']; captured = []
        def capture(proc, question, options, arrays, metadata, target, pixels, limit):
            prompt, suffix = training_text(proc, question, options, target)
            tok = proc.tokenizer
            captured.append(dict(pixels=list(pixels), encoder_size=dict(shortest_edge=len(arrays)*pixels[0],
                longest_edge=len(arrays)*pixels[1]), frame_count=tok._c1_frame_count if hasattr(tok, '_c1_frame_count') else 32,
                frame_markers=tok._c1_frame_markers if hasattr(tok, '_c1_frame_markers') else False,
                frame_layout=cfg.get('frame_layout', 'spread'), encoded_frames=len(arrays),
                frame_indices=list(metadata.frames_indices), b7_layout=hasattr(proc, '_b7_layout'),
                prompt_ids=tok.encode(prompt, add_special_tokens=False),
                target_ids=tok.encode(suffix, add_special_tokens=False),
                combined_ids=tok.encode(prompt+suffix, add_special_tokens=False)))
            return {}, {}
        try:
            if sample['key'][0]=='routing':
                row=routing.tool_mode(row,cfg.get('tool_mode_flag'))
                if 'routing' in row:
                    target,_,_=routing.render_full(row['routing']['events'],row['routing']['answer'])
                    row={**row,'target':target}
            with patch.object(pose_samples, 'load_frames', side_effect=lambda inputs:np.zeros((len(inputs['frames']),1,1,3), dtype=np.uint8)), patch.object(pose_samples, 'encode_frames', side_effect=capture):
                data.encode_layout_row(processor, row, cfg.get('frame_layout', 'spread'), cfg.get('frame_pair_gap_seconds'))
            if len(captured)!=1:raise ValueError('E92')
            records.append(dict(key=sample['key'], status='PASS', values=captured[0]))
        except Exception as error:
            records.append(dict(key=sample['key'], status='FAIL', error=type(error).__name__+':'+str(error)))
    return records


def worker(control, tree):
    value=json.loads(Path(control).read_bytes());tree=Path(tree).resolve()
    sys.path[:]=[str(tree)]+value['environment']['paths']
    from student_pilot.source_seal import inventory
    from student_pilot.p3_provenance import digest, load, pinned
    actual=digest(inventory(tree))
    if actual!=value['tree_sha256']:raise ValueError('E93')
    from student_pilot.carrier_c1_run import processor_for_receipt
    for dest,item in value['assets'].items():
        pinned(dict(path=dest,sha256=item['sha256']))
    processor=processor_for_receipt(value['model_value'],value['config'])
    samples=json.loads(Path(value['samples']).read_bytes())
    records=evaluate(processor,value['config'],samples)
    write(value['output'],dict(tree_sha256=actual,config_sha256=digest(value['config']),model=value['model'],rows=records))


def compare(samples, n, p, scope):
    keys=sorted(s['key'] for s in samples)
    sha=hashlib.sha256(json.dumps(keys,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    rows=[]
    for i,s in enumerate(samples):
        a,b=n['rows'][i],p['rows'][i]
        ok=(a['key']==b['key']==s['key'] and a['status']==b['status']=='PASS' and a['values']==b['values']
            and not a['values']['b7_layout'] and not b['values']['b7_layout'] and b['values']['pixels']==[16384,147456])
        rows.append(dict(key=s['key'],status='PASS' if ok else 'FAIL',n=a,p=b))
    return dict(status='PASS' if all(r['status']=='PASS' for r in rows) else 'FAIL',seed=SEED,
                sample_sha256=sha,sample_key_encoding='sorted [stream,i,qid] compact UTF-8 JSON',
                count=len(rows),scope=scope,rows=rows,n_tree=n['tree_sha256'],p_tree=p['tree_sha256'],
                rgb_decoded=False,model_weights_loaded=False)


def run(kit, root):
    import z
    root=Path(root)
    namespace=z.load(Path(kit)/'k/p.json')['namespace']
    sys.path.insert(0,str(Path(namespace)/'p/s'))
    from student_pilot.r1_persisted import scope
    paths=z.load(root/'pins.json')['paths'].copy()
    q=Path(namespace)/'p/q'
    for p in (q/'u').iterdir():
        if p.is_file() and len(p.name)==64:paths[p.name]=str(p)
    with scope(paths):return run_bound(kit,root)



def child_reason(path, side, returncode):
    reason = 'E95:'+side+':'+str(returncode)
    if side != 'n':
        return reason
    try:
        with Path(path).open('rb') as stream:
            stream.seek(0, 2)
            stream.seek(max(0, stream.tell()-(64 << 10)))
            lines = stream.read(64 << 10).decode('utf-8', errors='replace').splitlines()
        starts = [i for i, line in enumerate(lines) if line == 'Traceback (most recent call last):']
        if starts:
            # The exception terminates this traceback. Later stdout and notes
            # are not exception records, even when they contain a colon.
            frames = False
            for line in lines[starts[-1]+1:]:
                if line.startswith('  File '):
                    frames = True
                if frames and re.fullmatch(r'[A-Za-z_][\w.]*(?::.*)?', line):
                    reason += ':'+line[:4096]
                    break
    except OSError:
        pass
    return reason


# AutoProcessor's local metadata closure; weight indices and shards are excluded.
ASSETS = frozenset(('config.json', 'processor_config.json', 'preprocessor_config.json',
    'video_preprocessor_config.json', 'tokenizer_config.json', 'tokenizer.json',
    'special_tokens_map.json', 'added_tokens.json', 'vocab.json', 'vocab.txt',
    'merges.txt', 'tokenizer.model', 'spiece.model', 'sentencepiece.bpe.model',
    'chat_template.jinja', 'chat_template.json'))


def metadata_mounts(value, root):
    from student_pilot.p3_provenance import pinned
    logical = Path(value['root'])
    if not logical.is_absolute() or '..' in logical.parts:
        raise ValueError('E95:root')
    mounts = {}
    for name, h in sorted(value['files'].items()):
        path = Path(name)
        if path.is_absolute() or '..' in path.parts:
            raise ValueError('E95:path')
        if name not in ASSETS and not (path.parent == Path('chat_templates') and path.suffix == '.jinja'):
            continue
        target = str(logical/name)
        try:
            source = pinned(dict(path=target, sha256=h))
        except (OSError, ValueError):
            # Mode r already stages these bytes from the resolved metadata pins.
            source = pinned(dict(path=str(Path(root)/'m'/name), sha256=h))
        mounts[target] = dict(source=str(source), sha256=h)
    if 'config.json' not in value['files'] or not mounts:
        raise ValueError('E95:metadata')
    return mounts


def run_bound(kit, root):
    import z,rb
    root=Path(root);kit=Path(kit)
    namespace=z.load(kit/'k/p.json')['namespace'];q=Path(namespace)/'p/q'
    tree=Path(namespace)/'p/s'
    sys.path.insert(0,str(tree))
    from student_pilot.p3_provenance import load,pinned
    from student_pilot.mdg_parent import model_pin
    from student_pilot.source_seal import inventory
    from student_pilot.p3_provenance import digest
    cfg=load(q/'n.json');pcontrol=load(q/'base_input.json');mounts=load(q/'base_mounts.json')
    output=root/'proc_check.json';samples=None;scope={}
    try:
        vqa=None;reason='E94'
        try:
            receipt=load(pinned(cfg['streams']['vqa']));vqa=pinned(receipt['database'])
        except (OSError,ValueError,KeyError) as error:
            reason=type(error).__name__+':'+str(error)
        rng=random.Random(SEED)
        samples=selected(q/'selection/rows.sqlite',40 if vqa is not None else 80,rng,'routing')
        if vqa is not None:samples+=selected(vqa,40,rng,'vqa')
        scope=dict(routing=40 if vqa is not None else 80,vqa=40 if vqa is not None else 0,
                   vqa_staged=vqa is not None,vqa_unavailable_reason=None if vqa is not None else reason)
        sample_path=q/'pc_rows.json';write(sample_path,samples)
        results={}
        for side,config,source,model in [('n',cfg,tree,model_pin(cfg)),
                ('p',pcontrol['config'],q/'base_tree',pcontrol['recipe']['base_model'])]:
            sealed=load(pinned(config['code']))
            if digest(inventory(source))!=sealed['tree_sha256']:raise ValueError('E93')
            if side=='p' and not sealed['tree_sha256'].startswith('b83a8a35'):raise ValueError('E93')
            control=q/('pc_'+side+'.json');result=q/('pc_'+side+'_out.json')
            env=pcontrol['environment'] if side=='p' else rb.environment()
            value=load(pinned(model)); assets=metadata_mounts(value,root)
            write(control,dict(config=config,model=model,model_value=value,assets=assets,environment=env,tree_sha256=sealed['tree_sha256'],samples=str(sample_path),output=str(result)))
            cmd=rb.command(q,control,source,mounts if side=='p' else {},env)
            script=Path(__file__).resolve()
            at=cmd.index('--chdir');cmd[at:at]=['--ro-bind',str(script.parent),str(script.parent)]
            if side=='n':
                # N's prepared paths are already authenticated and restored by the outer view.
                at=cmd.index('--chdir');cmd[at:at]=['--ro-bind','/scratch','/scratch','--ro-bind',str(root),str(root),'--bind',str(q),str(q)]
            at=cmd.index('--chdir')
            for dest,item in sorted(assets.items()):
                cmd[at:at]=['--ro-bind',item['source'],dest]; at+=3
            cmd[-3:]=[str(script),str(control),str(source)]
            with (root/('pc_'+side+'.log')).open('xb') as log:
                child=subprocess.run(cmd,stdout=log,stderr=-2,check=False)
            if child.returncode:raise ValueError(child_reason(root/('pc_'+side+'.log'),side,child.returncode))
            results[side]=load(result)
        value=compare(samples,results['n'],results['p'],scope)
    except Exception as error:
        value=dict(status='FAIL',seed=SEED,reason=type(error).__name__+':'+str(error))
        if samples is not None:
            keys=sorted(s['key'] for s in samples)
            value.update(sample_sha256=hashlib.sha256(json.dumps(keys,separators=(',',':'),ensure_ascii=False).encode()).hexdigest(),
                         count=len(samples),scope=scope,rows=[dict(key=s['key'],status='FAIL',reason='E95') for s in samples])
    write(output,value)
    return int(value['status']!='PASS')


if __name__=='__main__':worker(*sys.argv[1:3])
