"""B1/B4 acceptance through the production live backend and trace session."""
import argparse,json,sys,time
from pathlib import Path
TREE=Path(__file__).resolve().parents[1]
R=TREE if (TREE/'inputs').is_dir() else TREE.parents[1]
sys.path.insert(0,str(TREE))
from student_pilot.trace_version import model_version

def main():
    p=argparse.ArgumentParser();p.add_argument('--inputs',required=True);p.add_argument('--out',required=True)
    p.add_argument('--call-mode',choices=('scripted','free'),required=True);p.add_argument('--start-check',action='store_true');a=p.parse_args()
    if a.start_check:
        from acceptance_start_check import begin
        begin(2,a)
    live=json.loads(Path(a.inputs).read_text())
    if live['call_mode']!=a.call_mode:raise ValueError('Call mode differs')
    # The serial launcher has already validated every input without torch.
    import torch
    import acceptance_live_adapter as adapter
    from student_pilot import carrier_c1_decode as D
    from student_pilot.decode_parity import save_comparison, noise_report
    from student_pilot.live_trace313 import LiveSession,check_record
    if a.start_check:
        from acceptance_start_check import routed_check
        routed_check(a,live,adapter)
        return
    cpu=getattr(sys, '_acceptance_cpu_e2e', None)
    if not cpu and torch.cuda.device_count()!=1:raise ValueError('One assigned GPU required')
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False)
    model,processor=adapter.load(live,'cpu' if cpu else 'cuda:0');torch.set_num_threads(1)
    if cpu: live=dict(live,routed=cpu.routed_rows(live['routed']))
    count=len(live['routed']) if cpu else 32
    outputs={1:[],4:[]};repeats=[];start=time.monotonic();memory_checks=[]
    ids=[i['id'] for i in live['routed'][:32]]
    precision=str(next(model.parameters()).dtype)
    import transformers
    provenance=dict(torch_version=torch.__version__,transformers_version=transformers.__version__,
        parameter_dtype=precision,same_loaded_model=True,reference='B1 twice, same card and dtype',
        linear_attention_backends=sorted({str(getattr(m,'recurrent_gated_delta_rule')) for m in model.modules() if hasattr(m,'recurrent_gated_delta_rule')}))
    strict=precision not in ('torch.bfloat16','torch.float16')
    for first in range(0,count,4):
        items=live['routed'][first:first+4]
        batches=[adapter.base._batch(item,model,processor)[0] for item in items]
        refs=[adapter.base.document(i['row']).get('reference_trace') if a.call_mode=='scripted' else None for i in items]
        for arm,size in (('b1',1),('b1_repeat',1),('b4',4)):
            backends=[adapter.base._backend(i,b) for i,b in zip(items,batches)]
            sessions=[LiveSession(b,program_version=model_version(model,live.get('trace_program_version'))) for b in backends]
            kwargs=dict(max_new_tokens=16384,mask_source=[b.mask_source for b in backends],ground_backend=backends,trace_session=sessions,reference_trace=refs if a.call_mode=='scripted' else None)
            if size==1:
                records=[]
                for j,b in enumerate(batches):
                    records.append(D.generate(model,processor,b,**{k:v[j] if isinstance(v,list) else v for k,v in kwargs.items()}))
                    # Retain completed rows even if a later generate raises.
                    (out/f'{arm}_group_{first}.json').write_text(json.dumps(records)+'\n')
            else:records=D.generate(model,processor,batches,**kwargs)
            target=repeats if arm=='b1_repeat' else outputs[size]
            target.extend(records)
            (out/f'{arm}.json').write_text(json.dumps(target)+'\n')
            comparison=save_comparison(out,outputs[1],outputs[4],ids=ids,strict=strict)
            for record,ref in zip(records,refs):check_record(record,ref)
            if size==4:
                again=[LiveSession(b,program_version=model_version(model,live.get('trace_program_version'))) for b in backends]
                repeat=D.generate(model,processor,batches,**dict(kwargs,trace_session=again))
                memory=save_comparison(out/'memory'/str(first),records,repeat,
                    ids=ids[first:first+4],labels=['B4 fresh','B4 memory hit'])
                hits=all(s.memory_hits and all(s.memory_hits) for s in again)
                (out/'memory'/str(first)/'HITS.json').write_text(json.dumps(dict(all_hits=hits,rows=[s.memory_hits for s in again]))+'\n')
                if memory['status']!='PASS' or not hits:raise AssertionError('Memory hit differs; see saved memory comparison')
                for record,ref in zip(repeat,refs):check_record(record,ref)
                memory_checks.extend(dict(id=i['id'],responses_equal=True,memory_hits=s.memory_hits) for i,s in zip(items,again))
    comparison=save_comparison(out,outputs[1],outputs[4],ids=ids,strict=strict)
    floor=save_comparison(out/'repeatability',outputs[1],repeats,ids=ids,strict=strict,
                          labels=['B1 first','B1 repeat'])
    noise=noise_report(outputs[1],repeats,outputs[4],ids)
    passed=comparison['status']=='PASS' and floor['status']=='PASS' and len(outputs[1])==len(outputs[4])==len(repeats)==count
    report=dict(status='PASS' if passed else 'FAIL',call_mode=a.call_mode,rows=len(outputs[1]),
        comparisons=comparison['comparisons'],memory=memory_checks,noise=noise,
        strict_verdict=comparison['strict_verdict'],parameter_dtype=precision,numerical_provenance=provenance,
        zero_errors=True,all_eos=True,response_parse_and_replay=True,seconds=time.monotonic()-start)
    (out/'RESULT.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(status=report['status'],noise=noise,parameter_dtype=precision)),flush=True)
    if not passed:raise AssertionError('B1/B4 or B1 repeat parity failed; see saved records, COMPARISON.json and RESULT.json')

if __name__=='__main__':main()
