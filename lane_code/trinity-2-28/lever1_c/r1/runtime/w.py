"""One exact prompt prefill and served geometry per pinned capture."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
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


def start_tower(spec,settings,bound,device='cuda:0'):
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
    early=TowerG3T(artifact,device)
    with torch.no_grad(), Audit(artifact):result=early(bound['frames'])
    if device!='cpu':torch.cuda.synchronize()
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


# CPU real unit (Orchard CPU check only). The production worker below runs its
# first capture on CPU with the full step-544 carrier, heads and G3T weights.
UNIT_RECEIPT='33.json'
UNIT_SAFETY=1.25


def unit_need(estimates,dense):
    """Seconds one capture needs: first model, carrier load and prefill, with margin."""
    e=estimates
    return UNIT_SAFETY*(e['first_model'][str(dense)]+e['load']+e['prefill'])+e['margin']


def admit_unit(selected,remaining,estimates):
    """Production-order index of the CPU unit and why it was chosen."""
    first=selected[0]['mapping']['dense_count']
    need=unit_need(estimates,first)
    info=dict(remaining_s=remaining,first_dense=first,first_need_s=need,estimates=estimates,safety=UNIT_SAFETY)
    if need<=remaining:return 0,dict(info,reason='first_unit',need_s=need)
    # Every stage stays exercised: a 32-frame capture runs the same binding,
    # first model, carrier load, prefill, geometry and record code.
    cheaper=[i for i,r in enumerate(selected) if r['mapping']['dense_count']<first]
    for i in cheaper:
        need=unit_need(estimates,selected[i]['mapping']['dense_count'])
        if need<=remaining:return i,dict(info,reason='time_guard',need_s=need)
    i=cheaper[0] if cheaper else 0
    return i,dict(info,reason='over_budget',need_s=unit_need(estimates,selected[i]['mapping']['dense_count']))


def _stats(values):
    a=np.asarray(values,dtype=np.float64)
    if not a.size or not np.isfinite(a).all():return dict(finite=bool(a.size and np.isfinite(a).all()))
    return dict(finite=True,min=float(a.min()),max=float(a.max()),mean=float(a.mean()),median=float(np.median(a)))


# Neutral receipt names for the first-model outputs (receipts stay label-free).
NAMES=dict(raw_pose9='pose9',anchor_slots='slots',frame_indices='indices',depth_grid='z',
           depth_conf_grid='zc',points_grid='xyz',grid_uv='uv',g3t_s='first_model_s')


def _neutral(value):
    return {NAMES.get(k,'t%d'%i if any(w in k for w in ('g3t','tower','depth','sam','ground','mask','dev')) else k):v
            for i,(k,v) in enumerate(sorted(value.items()))}


def _arrays(value):
    out={}
    for k,v in _neutral(value).items():
        a=np.asarray(v)
        if a.dtype.kind in 'fiub':out[k]=dict(shape=list(a.shape),dtype=str(a.dtype),finite=bool(np.isfinite(a.astype(np.float64)).all()) if a.size else True)
    return out


class Unit:
    """Stage timings, peak RSS and output checks, written after every stage."""
    def __init__(self,meta,unit,clock):
        self.path=Path(meta)/UNIT_RECEIPT;self.clock=clock;self.begun=time.monotonic()
        self.value=dict(passed=False,status='started',mode='cpu',stages=[],unit=dict(unit))
        self.save()
    def rss(self):
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024
    def stage(self,name,started,**extra):
        self.value['stages'].append(dict(name=name,seconds=time.monotonic()-started,
            elapsed_s=time.monotonic()-self.begun,peak_rss_bytes=self.rss(),**extra))
        self.save()
    def save(self):
        from orchard_h10.common import write
        self.value.update(seconds=time.monotonic()-self.begun,peak_rss_bytes=self.rss())
        write(self.path,self.value)


def unit_checks(row,first):
    """Clean-run checks on the served record of the CPU unit."""
    from .d import decode
    plane,uv=decode(row)
    import base64,io
    with np.load(io.BytesIO(base64.b64decode(row['arrays'])),allow_pickle=False) as z:half=z['depth']
    geometry=row['metadata']['geometry']
    scale=float(geometry['scale'])
    K=np.asarray(geometry['K'],dtype=np.float64)
    checks=dict(grid=dict(shape=list(half.shape),dtype=str(half.dtype),**_stats(half)),
                grid_exact=dict(shape=list(plane.shape),dtype=str(plane.dtype),**_stats(plane)),
                uv=dict(shape=list(np.asarray(uv).shape),**_stats(uv)),
                scale=dict(value=scale if np.isfinite(scale) else None,finite=bool(np.isfinite(scale))),
                K=dict(shape=list(K.shape),**_stats(K)),
                first_model=_arrays({k:v for k,v in first.items() if k!='source_hw'}),
                first_model_grid=_stats(first['depth_grid']),
                prefills=row['prefills'],decode_steps=row['decode_steps'])
    checks['clean']=bool(half.shape==(32,51,51) and half.dtype==np.float16 and checks['grid']['finite']
        and checks['grid_exact']['finite'] and checks['scale']['finite'] and scale>0 and checks['K']['finite']
        and all(x['finite'] for x in checks['first_model'].values())
        and row['prefills']==1 and row['decode_steps']==0)
    return checks


def run(config,stop_at,*,clock=time.time):
    from orchard_h10.common import write
    path=capture_path(config);path.parent.mkdir(parents=True,exist_ok=True)
    meta=Path(config['output'])/'metadata';marker=Path(config['stop_file'])
    reference=json.loads((Path(__file__).parent/'8.json').read_text())
    refs=load_rows();by_id={r['item_id']:r for r in refs}
    selected=[by_id[i] for i in reference['representatives']]
    unit=config.get('cpu_unit');device='cpu' if unit else 'cuda:0'
    expected=1 if unit else 60
    writer=Writer(path);checks=[];timings=[];failure=None;monitor=None;record=None
    def stop(n,f):marker.write_text(str(n)+'\n')
    old={n:signal.signal(n,stop) for n in (signal.SIGTERM,signal.SIGUSR1,signal.SIGINT)}
    try:
        root=bind_reader_root()
        from h1eval.h10.parity_adapter import settings_for,artifact_spec,prepare_runtime,make_capped_real
        from h1eval.items import digest
        from e2e_reader import parity
        import torch
        if unit:
            # Address-space cap for this CPU worker only; CUDA needs none.
            soft,hard=resource.getrlimit(resource.RLIMIT_AS)
            cap=int(unit['address_space']) if hard==resource.RLIM_INFINITY else min(int(unit['address_space']),hard)
            resource.setrlimit(resource.RLIMIT_AS,(cap,hard))
            torch.set_num_threads(int(unit['threads']))
            record=Unit(meta,unit,clock)
            record.value['environment']=dict(threads=torch.get_num_threads(),torch=torch.__version__,
                transformers=__import__('transformers').__version__,python=__import__('sys').version.split()[0],
                address_space_bytes=resource.getrlimit(resource.RLIMIT_AS)[0],cuda_visible=os.environ.get('CUDA_VISIBLE_DEVICES'))
            index,admission=admit_unit(selected,stop_at-clock(),unit['estimates'])
            record.value['admission']=admission
            # Production order up to and including the admitted capture.
            selected=[selected[index]]
            record.value['capture_index']=index
        elif 'H100' not in torch.cuda.get_device_name(0):raise ValueError('E03')
        from .m import Monitor
        from orchard_h10.s import stage_capture
        monitor=Monitor(meta,torch,cuda=not unit);monitor.begin(selected[0]['capture'])
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
        started=time.monotonic()
        stage_capture(settings,selected[0]['capture'])
        bound=parity.bind_item(selected[0]['task'],settings)
        spec=artifact_spec(settings['artifact_manifest'])
        if record:record.stage('bind',started,dense=len(bound['frames']['native_frames']))
        monitor.phase('1');tower_started=time.perf_counter();started=time.monotonic()
        early,first_tower=start_tower(spec,settings,bound,device)
        first_tower_seconds=time.perf_counter()-tower_started
        if record:record.stage('first_model',started,remaining_s=stop_at-clock())
        monitor.phase('2');started=time.monotonic()
        factory=make_capped_real(settings['export_dir'],spec,
                                [r['task'] for r in refs],settings=settings,device=device)
        if factory.load_info['export'].get('step')!=544:raise ValueError('E06')
        factory.generator.perception.g3t=early
        assert_reader_root(root)
        if record:
            model=factory.generator.model
            dtypes=sorted({str(x.dtype) for x in model.parameters()})
            record.stage('load',started,remaining_s=stop_at-clock(),parameters=sum(x.numel() for x in model.parameters()),
                         dtypes=dtypes,locations=sorted({str(x.device) for x in model.parameters()}),step=544)
        for index,ref in enumerate(selected):
            if clock()>=stop_at or marker.exists():break
            if index:
                monitor.begin(ref['capture'])
                stage_capture(settings,ref['capture'])
                bound=parity.bind_item(ref['task'],settings)
            monitor.phase('3');started=time.monotonic()
            # One representative per capture makes every tower call fresh.
            with fresh_perception(factory.generator):
                row=capture_one(factory.generator,bound,ref,tower_result=first_tower if index==0 else None)
            if index==0:row['timings']['g3t_s']=first_tower_seconds
            if record:
                record.stage('prefill',started,timings=_neutral(row['timings']))
                record.value['checks']=unit_checks(row,first_tower)
                started=time.monotonic()
            else:torch.cuda.synchronize()
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
            if record:
                # CPU numerics (fp32 first model, CPU bf16 kernels) are not the
                # GPU reference; parity is recorded, not required.
                record.value['parity']=dict(trusted=row['parity']['trusted'],
                    max_deviations={k:v for x in per_item for k,v in x['max_deviations'].items()},bounds=reference['bounds'])
                record.stage('record',started,bytes=writer.bytes)
            # Release per-capture RGB and geometry before staging the next one.
            del bound,row
            if index==0:del first_tower
    except Exception as e:
        from orchard_h10.e import exception
        exception(meta/'7.json',e)
        failure='E99:'+type(e).__name__.encode().hex()
        if record:
            import traceback
            lines=[l[-512:] for b in traceback.TracebackException.from_exception(e).format(chain=True) for l in b.splitlines()]
            record.value.update(error=(type(e).__name__+': '+str(e))[:2048],traceback=lines[-40:])
    finally:
        if monitor is not None:
            monitor.close();timings=monitor.rows
        writer.close()
        maxima={k:max((v['max_deviations'][k] for x in checks for v in x['items']),default=None) for k in reference['bounds']}
        receipt=dict(trusted=len(checks)==expected and all(x['trusted'] for x in checks) and failure is None,
            expected=expected,items=len(checks),bounds=reference['bounds'],bound_rule='twice maximum T1 repeat absolute deviation',
            max_deviations=maxima,captures=checks,gap_atol_m=reference['gap_atol_m'],
            capture_sha256=sha(path),capture_bytes=path.stat().st_size,capture_records=writer.items,failure=failure)
        write(meta/'PARITY.json',receipt);write(meta/'5.json',timings)
        result=dict(completed=len(checks),expected=expected,repeat_completed=0,repeat_expected=0,
                    complete=len(checks)==expected and failure is None,failure=failure)
        write(meta/'6.json',result)
        if record:
            done=[x['name'] for x in record.value['stages']]
            record.value.update(failure=failure,completed=len(checks),status='complete' if result['complete'] else 'failed',
                passed=bool(result['complete'] and done==['bind','first_model','load','prefill','record']
                            and record.value.get('checks',{}).get('clean') is True))
            record.save()
        for n,h in old.items():signal.signal(n,h)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('config');a=p.parse_args()
    v=json.loads(Path(a.config).read_text());r=run(v['config'],v['stop_at'])
    raise SystemExit(1 if r['failure'] else 0)
