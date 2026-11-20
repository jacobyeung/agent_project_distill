"""Point and restricted-selector passes plus ten fresh text replays."""
from pathlib import Path
import json
import signal
import time
from . import w
from .c import Writer
from .p import compare
from .points import load, binding


def run(config,stop_at,*,clock=time.time):
    from orchard_h10.common import write
    out=Path(config['output']);meta=out/'metadata';path=w.capture_path(config)
    path.parent.mkdir(parents=True,exist_ok=True)
    refs=w.load_rows();main={};restricted={};repeat={};timings=[];bindings=[];failure=None;api=None
    writer=Writer(path);marker=Path(config['stop_file'])
    def stopped():return clock()>=stop_at or marker.exists()
    def stop(number,frame):
        marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text(str(number)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT)}
    excluded=set();repeat_expected=10
    try:
        here=Path(__file__).parent
        pin=json.loads((here/'3.json').read_text())['points_sha256']
        value=load(here/'2.json',pin,refs)
        if stopped():raise InterruptedError('stopped before loading')
        reader_root=w.bind_reader_root()
        from h1eval.h10.parity_adapter import settings_for,artifact_spec,prepare_runtime,make_capped_real
        settings=settings_for(config['settings'],'devs1_routed')
        if (settings['stage1_select_rule']!='candidates_argmax' or settings['perception_memo']!='verify'
            or settings['perception_memo_modules']!=['g3t'] or settings['save_own_depth']):raise ValueError('settings differ')
        prepare_runtime(settings)
        from e2e_reader import parity,stage1
        from h1eval.items import digest
        w.assert_reader_root(reader_root)
        from .geometric import admit
        Prompt,api=admit(settings['sam3']['source_root'])
        captures=parity._captures(settings.get('frames_json',parity.FRAMES))
        dense=parity._captures(settings.get('dense_manifest',parity.DENSE))
        for ref in refs:
            native=ref['task']['native'];cap=captures[native]
            if (digest(ref['task'])!=ref['mapping']['task_sha256'] or
                digest(dict(anchors=cap,dense=dense[native]))!=ref['mapping']['frame_binding_sha256']):
                raise ValueError('task or RGB binding differs')
            br=binding(value,ref,[f['sha256'] for f in cap['frames']],stage1.name_key)
            bindings.append(br)
            if br['excluded']:excluded.add(ref['capture'])
        by_id={b['item_id']:b for b in bindings}
        write(meta/'7.json',dict(points_sha256=pin,api=api,bindings=bindings,excluded_captures=sorted(excluded)))
        from .point_socket import point_context
        from .restricted import restricted_context
        factory=make_capped_real(settings['export_dir'],artifact_spec(settings['artifact_manifest']),
                                 [r['task'] for r in refs],settings=settings,device='cuda:0')
        if factory.load_info['export'].get('step')!=544:raise ValueError('step differs')
        import torch
        chosen=[r for r in refs if r['calls']][:10]
        repeat_expected=sum(r['capture'] not in excluded for r in chosen)
        for pass_id,arm,selected,target in ((0,'points',refs,main),(2,'restricted_selector',refs,restricted),(1,'text_noise',chosen,repeat)):
            if pass_id and len(main)!=150:break
            for ref in selected:
                if stopped():break
                key=ref['item_id']
                if ref['capture'] in excluded:
                    if pass_id==1:continue
                    row=dict(schema='ground-capture-v1',item_id=key,capture=ref['capture'],
                             source_indices=ref['source_indices'],geometry=None,objects=[],calls=[],
                             excluded=True,exclusion_reason='anchor RGB SHA256 mismatch',binding=by_id[key],
                             prefills=0,decode_steps=0,answer_pass=False)
                    seconds=0.;allocated=reserved=0
                else:
                    torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
                    bound=parity.bind_item(ref['task'],settings)
                    bound_hashes=[f['sha256'] for f in bound['row']['student_input']['frames']]
                    if bound_hashes!=by_id[key]['bound_anchor_sha256']:raise ValueError('bound RGB hashes changed')
                    if pass_id==1:
                        with w.fresh_perception(factory.generator):row=w.replay(factory.generator,bound,ref)
                    elif pass_id==2:
                        with restricted_context(factory.generator,ref,value['points'][key]):
                            row=w.replay(factory.generator,bound,ref)
                    else:
                        with point_context(factory.generator,ref,value['points'][key],Prompt):
                            row=w.replay(factory.generator,bound,ref)
                    row.update(excluded=False,binding=by_id[key])
                    torch.cuda.synchronize();seconds=time.perf_counter()-started
                    allocated=torch.cuda.max_memory_allocated();reserved=torch.cuda.max_memory_reserved()
                    del bound
                row.update(pass_index=pass_id,arm=arm,seconds=seconds,
                           peak_gpu_bytes=allocated,peak_gpu_reserved_bytes=reserved,memo_reuse=pass_id!=1)
                writer.append(row);target[key]=row['calls']
                timings.append({k:row[k] for k in ('item_id','pass_index','arm','seconds','peak_gpu_bytes','peak_gpu_reserved_bytes')})
                write(meta/'4.json',dict(items=writer.items,main_items=len(main),restricted_items=len(restricted),repeat_items=len(repeat),bytes=writer.bytes))
                del row
    except InterruptedError:
        pass
    except Exception as error:
        failure=type(error).__name__+': '+str(error)
    finally:
        try:writer.close()
        except Exception as error:failure=failure or type(error).__name__+': '+str(error)
        noise=[]
        for ref in refs:
            if ref['item_id'] not in repeat:continue
            same,gaps=compare(ref['calls'],repeat[ref['item_id']])
            noise.append(dict(item_id=ref['item_id'],discrete_match=same,
                              gaps=[{k:float(v) if hasattr(v,'as_tuple') else v for k,v in g.items()} for g in gaps]))
        receipt=dict(mode='points',trusted=False,parity_gate_applies=False,items=len(main),expected=150,
                     capture_sha256=w.sha(path),capture_records=writer.items,capture_bytes=path.stat().st_size,
                     points_sha256=locals().get('pin'),api=api,bindings=bindings,
                     excluded_captures=sorted(excluded),excluded_items=sum(r['capture'] in excluded for r in refs),
                     text_noise=noise,repeat_items=len(repeat),repeat_expected=repeat_expected,restricted_items=len(restricted),
                     failure=failure,step=544,per_item=[dict(item_id=r['item_id'],discrete_match=None) for r in refs])
        write(meta/'PARITY.json',receipt);write(meta/'5.json',timings)
        write(meta/'4.json',dict(items=writer.items,main_items=len(main),restricted_items=len(restricted),repeat_items=len(repeat),bytes=writer.bytes))
        result=dict(completed=len(main),expected=150,restricted_completed=len(restricted),restricted_expected=150,repeat_completed=len(repeat),repeat_expected=repeat_expected,
                    excluded_items=receipt['excluded_items'],
                    complete=len(main)==150 and len(restricted)==150 and len(repeat)==repeat_expected and failure is None,failure=failure)
        write(meta/'6.json',result)
        for n,handler in old.items():signal.signal(n,handler)
    return result
