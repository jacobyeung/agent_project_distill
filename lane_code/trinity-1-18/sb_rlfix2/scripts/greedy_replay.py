"""GPU-only A4 m200 token replay gate. This command never launches training."""
import argparse
from pathlib import Path
from rl_on_n import provenance as P
from rl_on_n.serving import (ROOT, PAYLOAD, default_binding, load_binding,
                             build_reader, reader_runtime, PINS)
from rl_on_n.replay import selection, check_export, TYPES


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--export-dir',required=True,help='Restored m200 directory containing RESTORE.json')
    ap.add_argument('--config',required=True,help='A4 m200 prepared config, authenticated by EXPORT_PIN.json')
    ap.add_argument('--artifact-binding',required=True,help='Existing artifact binding admitting sealed A4 code and RL overlay')
    ap.add_argument('--artifact-binding-sha256',required=True)
    ap.add_argument('--tree',default='/scratch/jjyeung/orch_n30/sb_f64/pkg/work/tree_r1',help='N training tree to test with the A4 reader')
    ap.add_argument('--out',default=str(ROOT/'out/GREEDY_REPLAY.json'))
    a=ap.parse_args();P.sha(__file__)
    output=Path(a.out).resolve()
    if not output.is_relative_to(ROOT):raise ValueError('Replay output must be inside the workspace')
    binding=default_binding();binding['artifact_manifest']=dict(path=a.artifact_binding,sha256=a.artifact_binding_sha256)
    settings=load_binding(binding);P.tree(a.tree)
    for path in (ROOT/'overlay/rl_on_n').glob('*.py'):P.sha(path)
    # Fail on the wrong export before loading weights or touching a GPU.
    check_export(a.export_dir,a.config)
    selected=selection()
    specs=P.load(P.checked(binding['artifact_manifest']))
    P.checked(dict(path=str(Path(specs['root'])/specs['name']),sha256=specs['sha256']))
    import torch
    torch.set_num_threads(8)
    if not torch.cuda.is_available() or torch.cuda.device_count()!=1:
        raise ValueError('Expose exactly one assigned GPU for the replay')
    from e2e_reader.parity import load_native,bind_item
    from h1eval.h10.parity_adapter import map_items
    from rl_on_n.adapters import install
    from rl_on_n.rollout import sample,native_kwargs
    # Load A4 with its sealed restore implementation; never import the staged /p reader.
    replay_settings=dict(settings,tree=str(PAYLOAD/'tree'),config=a.config,export_dir=a.export_dir)
    with reader_runtime():
        model,processor,info=load_native(a.export_dir,device='cuda:0',settings=replay_settings)
    torch.manual_seed(17);installed=install(model,16,32)
    # Zero-initialized adapters must leave the m200 greedy policy unchanged.
    reader=build_reader(model,processor,binding,'cuda:0')
    mapped,_=map_items([s['item'] for s in selected],settings)
    from evalpath.runtime import prompt_batch
    results=[];mismatches=[];counts={t:0 for t in TYPES}
    for chosen in selected:
        item=chosen['item'];bound=bind_item(mapped[item['id']],settings)
        row=bound['row']
        # Exercise the training frame bridge using the exact recorded dense selection.
        row['student_input']['geometry_dense']=dict(
            frames=[dict(path=str(path),sha256=P.sha(path)) for path in
                    bind_item(mapped[item['id']],settings,verify=False)['frames']['native_frames']],
            frame_indices=bound['frames']['dense_indices'])
        batch=prompt_batch(processor,row,info['config'],'routed')
        batch={k:v.to('cuda:0') if isinstance(v,torch.Tensor) else v for k,v in batch.items()}
        prompt=dict(row=row,type=item['question_type'],prompt_id=item['id'])
        actual=sample(model,processor,batch,decode=native_kwargs(processor,prompt,batch,reader),greedy=True)
        expected=chosen['expected'];equal=actual['tokens']==expected['tokens'] and actual['finish']==expected['finish']
        if not equal:mismatches.append(item['id'])
        counts[item['question_type']]+=1
        results.append(dict(id=item['id'],type=item['question_type'],match=equal,
                            expected_tokens=expected['tokens'],actual_tokens=actual['tokens'],
                            expected_finish=expected['finish'],actual_finish=actual['finish'],
                            journal=chosen['journal'],journal_sha256=chosen['journal_sha256']))
    P.write(output,dict(status='PASS' if not mismatches else 'FAIL',counts=counts,mismatches=mismatches,
            export_pin_sha256=PINS['export_pin'][1],tree_root=str(Path(a.tree).resolve()),
            adapter_rank=16,adapter_alpha=32,adapter_modules=installed,binding=binding,results=results,
            command='bash scripts/run_greedy_replay.sh '+__import__('shlex').join(__import__('sys').argv[1:])))
    if mismatches:raise SystemExit('A4 greedy token replay FAILED; training remains blocked')

if __name__=='__main__':main()
