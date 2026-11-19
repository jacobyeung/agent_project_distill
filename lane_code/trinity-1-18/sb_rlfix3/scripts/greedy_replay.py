"""GPU-only A4 m200 token replay gate. This command never launches training."""
import argparse
from collections import Counter
import os
from pathlib import Path
import shlex
import sys
from rl_on_n import provenance as P
from rl_on_n.serving import (ROOT, default_binding, load_binding, build_reader, reader_runtime, PINS)
from rl_on_n.replay import (selection, check_export, export_identity, require_scratch, require_interpreter,
                            require_card, replay_key, matched_items, append_item, call_records, COUNTS)


def families(output):
    return [c.get('family') for c in call_records(output)]


def fired(output):
    return bool((output.get('decode_budget') or {}).get('fired'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--export-dir',required=True,help='Restored m200 directory containing RESTORE.json')
    ap.add_argument('--config',required=True,help='A4 m200 prepared config, authenticated by EXPORT_PIN.json')
    ap.add_argument('--artifact-binding',required=True,help='Existing artifact binding admitting sealed A4 code and RL overlay')
    ap.add_argument('--artifact-binding-sha256',required=True)
    ap.add_argument('--tree',default='/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1',help='N training tree to test with the A4 reader')
    ap.add_argument('--out',default=str(ROOT/'out/GREEDY_REPLAY.json'))
    a=ap.parse_args();P.sha(__file__)
    output=Path(a.out).resolve();items_path=output.with_suffix('.items.jsonl')
    if not output.is_relative_to(ROOT):raise ValueError('Replay output must be inside the workspace')
    require_interpreter()
    require_scratch(dict(export_dir=a.export_dir,config=a.config,artifact_binding=a.artifact_binding,tree=a.tree,out=output))
    binding=default_binding();binding['artifact_manifest']=dict(path=a.artifact_binding,sha256=a.artifact_binding_sha256)
    settings=load_binding(binding);P.tree(a.tree)
    code=sorted((ROOT/'overlay/rl_on_n').glob('*.py'))+[Path(__file__).resolve()]
    # Fail on the wrong export before loading weights or touching a GPU.
    pin=check_export(a.export_dir,a.config)
    selected=selection()
    specs=P.load(P.checked(binding['artifact_manifest']))
    require_scratch({'artifact root':specs['root'],**{'code root '+k:v for k,v in specs.get('code_roots',{}).items()}})
    P.checked(dict(path=str(Path(specs['root'])/specs['name']),sha256=specs['sha256']))
    import torch
    torch.set_num_threads(8)
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1:
        raise ValueError('Expose exactly one assigned GPU for the replay')
    card=torch.cuda.get_device_name(0);require_card(card)
    from e2e_reader.parity import bind_item
    from rl_on_n.adapters import install
    from rl_on_n.rollout import sample,native_kwargs
    from rl_on_n.train import load_export,prompt_inputs
    with reader_runtime():
        from h1eval.h10.parity_adapter import map_items
        mapped,_=map_items([s['item'] for s in selected],settings)
    restore=P.pin(Path(a.export_dir)/'RESTORE.json')
    config=dict(path=str(Path(a.config).resolve()),sha256=pin['preparation']['config']['sha256'])
    identity=export_identity(a.export_dir)
    key=replay_key(identity=identity,binding=binding,tree=str(Path(a.tree).resolve()),card=card,
                   code={str(p):P.sha(p) for p in code})
    results=matched_items(items_path,key)
    pending=[s for s in selected if s['item']['id'] not in results]
    if pending:
        # The training loader and prompt builder; zero-initialized adapters leave m200 greedy tokens unchanged.
        model,processor,info=load_export(restore,config,'cuda:0',binding)
        torch.manual_seed(17);installed=install(model,16,32)
        reader=build_reader(model,processor,binding,'cuda:0')
    for chosen in pending:
        item=chosen['item'];bound=bind_item(mapped[item['id']],settings)
        row=bound['row']
        # Exercise the training frame bridge using the exact recorded dense selection.
        row['student_input']['geometry_dense']=dict(
            frames=[dict(path=str(path),sha256=P.sha(path)) for path in
                    bind_item(mapped[item['id']],settings,verify=False)['frames']['native_frames']],
            frame_indices=bound['frames']['dense_indices'])
        batch=prompt_inputs(processor,row,info['config'],'cuda:0')
        prompt=dict(row=row,type=item['question_type'],prompt_id=item['id'])
        actual=sample(model,processor,batch,decode=native_kwargs(processor,prompt,batch,reader),greedy=True)
        expected=chosen['expected']
        equal=(actual['tokens']==expected['tokens'] and actual['finish']==expected['finish']
               and families(actual)==families(expected) and fired(actual)==fired(expected))
        results[item['id']]=dict(key=key,id=item['id'],group=chosen['group'],type=item['question_type'],match=equal,
            expected_tokens=expected['tokens'],actual_tokens=actual['tokens'],
            expected_finish=expected['finish'],actual_finish=actual['finish'],
            expected_families=families(expected),actual_families=families(actual),
            expected_fired=fired(expected),actual_fired=fired(actual),refusal=actual.get('refusal'),
            adapter_modules=installed,journal=chosen['journal'],journal_sha256=chosen['journal_sha256'])
        append_item(items_path,results[item['id']])
    rows=[results[s['item']['id']] for s in selected]
    mismatches=[r['id'] for r in rows if not r['match']]
    counts=dict(Counter(r['group'] for r in rows))
    P.write(output,dict(status='PASS' if not mismatches and counts==COUNTS else 'FAIL',counts=counts,mismatches=mismatches,
            export_pin_sha256=PINS['export_pin'][1],export_identity=identity,tree_root=str(Path(a.tree).resolve()),
            card=card,key=key,items=P.pin(items_path),adapter_rank=16,adapter_alpha=32,
            adapter_modules=rows[0]['adapter_modules'],binding=binding,results=rows,
            command='bash scripts/run_greedy_replay.sh '+shlex.join([os.environ.get('REPLAY_CARD','<card>'),*sys.argv[1:]])))
    if mismatches:raise SystemExit('A4 greedy token replay FAILED; training remains blocked')

if __name__=='__main__':main()
