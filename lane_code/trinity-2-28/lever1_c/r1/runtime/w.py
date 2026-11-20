"""One exact prompt prefill and served geometry per pinned capture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import time
import numpy as np
from .t import bind_reader_root, assert_reader_root, load_rows, capture_path, fresh_perception
from .d import Writer, encode
from .c import geometry_record


def sha(path):
    with Path(path).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def compare(actual, expected, bounds):
    deltas={k:float(np.max(np.abs(np.asarray(actual[k])-np.asarray(expected[k])))) for k in bounds}
    ok=all(np.isfinite(deltas[k]) and deltas[k]<=bounds[k] for k in bounds)
    ok=ok and actual['source_indices']==expected['source_indices']
    return dict(trusted=bool(ok), max_deviations=deltas)


def start_tower(spec,settings,bound):
    import torch
    from e2e_reader.artifact import Artifact, Audit
    from e2e_reader.real import TowerG3T
    artifact=Artifact(spec['root'],spec['name'],spec['sha256'],
        code_roots=spec.get('code_roots'),env_roots=settings.get('env_roots',()),
        write_roots=[os.environ[k] for k in ('TRITON_CACHE_DIR','TORCHINDUCTOR_CACHE_DIR','XDG_CACHE_HOME',
                                            'HF_HOME','TORCH_HOME') if os.environ.get(k)],required_roles=('g3t',))
    # Authenticate only the early tower here. The normal factory verifies the
    # complete original manifest before allocating the shared carrier model.
    artifact.manifest=dict(artifact.manifest,components={'g3t':artifact.manifest['components']['g3t']})
    artifact.verify()
    early=TowerG3T(artifact,'cuda:0')
    with torch.no_grad(), Audit(artifact):result=early(bound['frames'])
    torch.cuda.synchronize()
    return early,result


def capture_one(gen,bound,ref,*,tower_result=None):
    import torch
    from student_pilot.carrier_c1_decode import _prepare_decode
    from student_pilot.ground_context import closed_adapters
    from e2e_reader.artifact import Audit
    from e2e_reader.generate import EntryCounter
    from e2e_reader.callhook import Unserved
    frames=bound['frames']
    if frames['anchor_indices']!=ref['source_indices'] or len(frames['native_frames'])!=ref['mapping']['dense_count']:
        raise ValueError('E01')
    batch=gen.prompt_batch(gen.processor,bound['row'])
    batch={k:v.to(gen.device) if hasattr(v,'to') else v for k,v in batch.items()}
    memo=getattr(gen.perception,'memo',None)
    if memo is not None:memo.item_id=ref['item_id'];memo.begin_read()
    counter=EntryCounter(gen.model.model.language_model); old=gen.perception.socket
    tower=gen.perception.g3t
    timings={}
    try:
        # lazy() constructs identical geometry before touching this socket. With
        # no socket its ground route raises Unserved after publishing servers.
        gen.perception.socket=None
        if tower_result is not None:gen.perception.g3t=lambda frames:tower_result
        with torch.no_grad(), Audit(gen.artifact) as audit:
            state=closed_adapters(_prepare_decode)(gen.model,gen.processor,batch,max_new_tokens=16384)
            servers,built=gen.perception.lazy(frames,state,timings)
            try:servers['ground']('')
            except Unserved:pass
            geometry=built['servers'].geometry
            record=geometry_record(geometry)
            audit.entries=counter.prefills+counter.steps
            result=encode(geometry,dict(capture=ref['capture'],item_id=ref['item_id'],geometry=record,
                source_hw=[frames['native_frames'][0].height,frames['native_frames'][0].width],
                dense_indices=frames['dense_indices'],anchor_slots=frames['anchor_slots'],
                frame_binding_sha256=ref['mapping']['frame_binding_sha256'],
                mask_canvas=[240,320],raw_mask_canvas=[480,640],
                grid_convention='square endpoint canvas 0..1000; mask pixel centres (x+.5)/W,(y+.5)/H',
                tower_scale=record['scale'],scale_applied=record['scale']))
    finally:
        counter.remove();gen.perception.socket=old;gen.perception.g3t=tower
    if counter.prefills!=1 or counter.steps!=0:raise ValueError('E02')
    result.update(timings=timings,prefills=counter.prefills,decode_steps=counter.steps)
    return result


def run(config,stop_at,*,clock=time.time):
    from orchard_h10.common import write
    path=capture_path(config);path.parent.mkdir(parents=True,exist_ok=True)
    meta=Path(config['output'])/'metadata';marker=Path(config['stop_file'])
    reference=json.loads((Path(__file__).parent/'8.json').read_text())
    refs=load_rows();by_id={r['item_id']:r for r in refs}
    selected=[by_id[i] for i in reference['representatives']]
    writer=Writer(path);checks=[];timings=[];failure=None;monitor=None
    def stop(n,f):marker.write_text(str(n)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT)}
    try:
        root=bind_reader_root()
        from h1eval.h10.parity_adapter import settings_for,artifact_spec,prepare_runtime,make_capped_real
        from h1eval.items import digest
        from e2e_reader import parity
        import torch
        if 'H100' not in torch.cuda.get_device_name(0):raise ValueError('E03')
        from .m import Monitor
        from orchard_h10.s import stage_capture
        monitor=Monitor(meta,torch);monitor.begin(selected[0]['capture'])
        settings=settings_for(config['settings'],'devs1_routed');prepare_runtime(settings)
        if any(settings.get(k) for k in ('sam3','selector_head','scale_head')):raise ValueError('E07')
        if settings['save_own_depth'] or settings['perception_memo_modules']!=['g3t']:raise ValueError('E04')
        captures=parity._captures(settings.get('frames_json',parity.FRAMES))
        dense=parity._captures(settings.get('dense_manifest',parity.DENSE))
        for ref in refs:
            native=ref['task']['native']
            if digest(ref['task'])!=ref['mapping']['task_sha256'] or digest(dict(anchors=captures[native],dense=dense[native]))!=ref['mapping']['frame_binding_sha256']:
                raise ValueError('E05')
        # Run the first tower before allocating the shared carrier model. Keep
        # its exact output for capture_one; this does not add a second forward.
        stage_capture(settings,selected[0]['capture'])
        bound=parity.bind_item(selected[0]['task'],settings)
        spec=artifact_spec(settings['artifact_manifest'])
        monitor.phase('1');tower_started=time.perf_counter()
        early,first_tower=start_tower(spec,settings,bound)
        first_tower_seconds=time.perf_counter()-tower_started
        monitor.phase('2')
        factory=make_capped_real(settings['export_dir'],spec,
                                [r['task'] for r in refs],settings=settings,device='cuda:0')
        if factory.load_info['export'].get('step')!=544:raise ValueError('E06')
        factory.generator.perception.g3t=early
        assert_reader_root(root)
        for index,ref in enumerate(selected):
            if clock()>=stop_at or marker.exists():break
            if index:
                monitor.begin(ref['capture'])
                stage_capture(settings,ref['capture'])
                bound=parity.bind_item(ref['task'],settings)
            monitor.phase('3')
            # One representative per capture makes every tower call fresh.
            with fresh_perception(factory.generator):
                row=capture_one(factory.generator,bound,ref,tower_result=first_tower if index==0 else None)
            if index==0:row['timings']['g3t_s']=first_tower_seconds
            torch.cuda.synchronize()
            monitor.phase('4');row['seconds']=monitor.current['seconds']
            per_item=[]
            for iid,expected in reference['geometry'].items():
                if expected['capture']==ref['capture']:
                    per_item.append(dict(item_id=iid,**compare(row['metadata']['geometry'],expected['geometry'],reference['bounds'])))
            row['parity']=dict(trusted=all(x['trusted'] for x in per_item),items=per_item)
            row['memory']=dict(monitor.current)
            writer.append(row);checks.append(dict(capture=ref['capture'],**row['parity']))
            write(meta/'4.json',dict(items=writer.items,bytes=writer.bytes))
            timings.append(monitor.finish('written'))
            # Release per-capture RGB and geometry before staging the next one.
            del bound,row
            if index==0:del first_tower
    except Exception as e:
        from orchard_h10.e import exception
        exception(meta/'7.json',e)
        failure='E99:'+type(e).__name__.encode().hex()
    finally:
        if monitor is not None:
            monitor.close();timings=monitor.rows
        writer.close()
        maxima={k:max((v['max_deviations'][k] for x in checks for v in x['items']),default=None) for k in reference['bounds']}
        receipt=dict(trusted=len(checks)==60 and all(x['trusted'] for x in checks) and failure is None,
            expected=60,items=len(checks),bounds=reference['bounds'],bound_rule='twice maximum T1 repeat absolute deviation',
            max_deviations=maxima,captures=checks,gap_atol_m=reference['gap_atol_m'],
            capture_sha256=sha(path),capture_bytes=path.stat().st_size,capture_records=writer.items,failure=failure)
        write(meta/'PARITY.json',receipt);write(meta/'5.json',timings)
        result=dict(completed=len(checks),expected=60,repeat_completed=0,repeat_expected=0,
                    complete=len(checks)==60 and failure is None,failure=failure)
        write(meta/'6.json',result)
        for n,h in old.items():signal.signal(n,h)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');a=p.parse_args()
    v=json.loads(Path(a.config).read_text());r=run(v['config'],v['stop_at'])
    raise SystemExit(1 if r['failure'] else 0)
