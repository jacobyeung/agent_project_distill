"""Replay deployed text grounding on each capture's bound 32 or 64 native frames."""
from pathlib import Path
import json
import signal
import time
from . import w,d
from .c import Writer
from .p import compare


def run(config,stop_at,*,clock=time.time):
    from orchard_h10.common import write
    out=Path(config['output']);meta=out/'metadata';path=w.capture_path(config)
    path.parent.mkdir(parents=True,exist_ok=True)
    refs=w.load_rows();main={};repeat={};timings=[];failure=None;admission=None
    writer=Writer(path);marker=Path(config['stop_file']);first_counts=set()
    def stopped():return clock()>=stop_at or marker.exists()
    def stop(number,frame):
        marker.parent.mkdir(parents=True,exist_ok=True);marker.write_text(str(number)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT)}
    try:
        if stopped():raise InterruptedError('stopped before loading')
        reader_root=w.bind_reader_root()
        from h1eval.h10.parity_adapter import settings_for,artifact_spec,prepare_runtime,make_capped_real
        settings=settings_for(config['settings'],'devs1_routed')
        if (settings['stage1_select_rule']!='candidates_argmax' or settings['perception_memo']!='verify'
            or settings['perception_memo_modules']!=['g3t'] or settings['save_own_depth']):raise ValueError('settings differ')
        prepare_runtime(settings)
        from e2e_reader import parity
        from h1eval.items import digest
        w.assert_reader_root(reader_root)
        captures=parity._captures(settings.get('frames_json',parity.FRAMES))
        dense=parity._captures(settings.get('dense_manifest',parity.DENSE))
        census={}
        for ref in refs:
            native=ref['task']['native']
            if (digest(ref['task'])!=ref['mapping']['task_sha256'] or
                digest(dict(anchors=captures[native],dense=dense[native]))!=ref['mapping']['frame_binding_sha256']):
                raise ValueError('task or RGB binding differs')
            count=len(dense[native]['frames'])
            if count!=ref['mapping']['dense_count']:raise ValueError('dense census differs')
            census[ref['capture']]=count
        if list(census.values()).count(64)!=31 or list(census.values()).count(32)!=29:
            raise ValueError('expected 31 dense and 29 anchor-only captures')
        with d.installed() as admission:
            write(meta/'7.json',dict(admission=admission,capture_frame_counts=census))
            import torch
            device_name=torch.cuda.get_device_properties(0).name
            if 'H100' not in device_name:raise ValueError('requires assigned H100')
            factory=make_capped_real(settings['export_dir'],artifact_spec(settings['artifact_manifest']),
                                     [r['task'] for r in refs],settings=settings,device='cuda:0')
            if factory.load_info['export'].get('step')!=544:raise ValueError('step differs')
            for pass_id,selected,target in ((0,refs,main),(1,[r for r in refs if r['calls']][:10],repeat)):
                if pass_id and len(main)!=150:break
                for ref in selected:
                    if stopped():break
                    torch.cuda.synchronize();torch.cuda.reset_peak_memory_stats();started=time.perf_counter()
                    bound=parity.bind_item(ref['task'],settings)
                    binding=d.binding_record(bound,ref)
                    if pass_id:
                        with w.fresh_perception(factory.generator):row=w.replay(factory.generator,bound,ref)
                    else:row=w.replay(factory.generator,bound,ref)
                    torch.cuda.synchronize()
                    row.update(binding,pass_index=pass_id,arm='dense64' if pass_id==0 else 'dense64_noise',
                               seconds=time.perf_counter()-started,peak_gpu_bytes=torch.cuda.max_memory_allocated(),
                               peak_gpu_reserved_bytes=torch.cuda.max_memory_reserved(),memo_reuse=not bool(pass_id))
                    writer.append(row);target[ref['item_id']]=row['calls']
                    timing={k:row[k] for k in ('item_id','pass_index','seconds','peak_gpu_bytes','peak_gpu_reserved_bytes','ground_frame_count')}
                    timing['timings']=row['timings'];timings.append(timing)
                    n=binding['ground_frame_count']
                    if pass_id==0 and (not first_counts or (n not in first_counts and ref['calls'])):
                        free,total=torch.cuda.mem_get_info()
                        first=dict(timing,gpu_name=device_name,gpu_free_bytes=free,gpu_total_bytes=total,
                                   remaining_worker_seconds=max(0,stop_at-clock()),
                                   linear_160_item_minutes=160*row['seconds']/60,
                                   note='first cold item includes prefill, lazy towers, CPU linking and observer; excludes initial VLM load and gzip commit; planning estimate only')
                        write(meta/('8_'+str(n)+'.json'),first)
                        if ref['calls']:first_counts.add(n)
                        if row['seconds']>config.get('first_item_max_seconds',float('inf')):
                            raise RuntimeError('first item timing limit exceeded')
                        if row['peak_gpu_reserved_bytes']>config.get('first_item_max_reserved_bytes',float('inf')):
                            raise RuntimeError('first item memory limit exceeded')
                    write(meta/'4.json',dict(items=writer.items,main_items=len(main),repeat_items=len(repeat),bytes=writer.bytes))
                    del row,bound
    except InterruptedError:
        pass
    except Exception as error:
        failure=type(error).__name__+': '+str(error)
    finally:
        try:writer.close()
        except Exception as error:failure=failure or type(error).__name__+': '+str(error)
        noise=[]
        for ref in refs:
            key=ref['item_id']
            if key not in repeat:continue
            same,gaps=compare(main[key],repeat[key])
            noise.append(dict(item_id=key,discrete_match=same,
                              gaps=[{k:float(v) if hasattr(v,'as_tuple') else v for k,v in g.items()} for g in gaps]))
        receipt=dict(mode='dense64',trusted=False,parity_gate_applies=False,
                     response_strings_differ_by_design=True,items=len(main),expected=150,
                     capture_sha256=w.sha(path),capture_records=writer.items,capture_bytes=path.stat().st_size,
                     repeat_items=len(repeat),repeat_expected=10,arm_noise=noise,
                     failure=failure,step=544,admission=admission)
        write(meta/'PARITY.json',receipt);write(meta/'5.json',timings)
        result=dict(completed=len(main),expected=150,repeat_completed=len(repeat),repeat_expected=10,
                    complete=len(main)==150 and len(repeat)==10 and failure is None,failure=failure)
        write(meta/'6.json',result)
        for n,handler in old.items():signal.signal(n,handler)
    return result
