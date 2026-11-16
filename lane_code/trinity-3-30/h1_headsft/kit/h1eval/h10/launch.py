"""Flush and resume complete (item, arm, mode) reads from b04's generator."""
import argparse
from datetime import datetime, timezone
import fcntl
import importlib
import inspect
import json
import os
from pathlib import Path
import platform
import sys
import time

if not __package__:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = 'h1eval.h10'
from h1eval.items import K, load_manifest, sha, digest
from h1eval.cli import modes as parse_modes, code_hash, export_hash
from h1eval.modes import mode_key, applies, plan, read_counts, DEFAULT_MODES
from .parity_adapter import ENTRY, DEFAULT_SETTINGS


def reader_factory(root, entry=ENTRY):
    root = Path(root).resolve()
    if not (root.is_relative_to('/scratch') or root.is_relative_to('/dev/shm')):
        raise ValueError('Stage the reader on /scratch or /dev/shm')
    module, name = entry.split(':')
    if not (root/'e2e_reader').is_dir():
        raise ValueError('--reader-root must contain b04 e2e_reader/ with make_real')
    for key, value in tuple(sys.modules.items()):
        if key == 'e2e_reader' or key.startswith('e2e_reader.'):
            source = getattr(value, '__file__', None)
            if source and not Path(source).resolve().is_relative_to(root):
                raise ValueError('Another e2e_reader is already imported; launch in a fresh process')
    sys.path.insert(0, str(root))
    importlib.invalidate_caches()
    try:
        mod = importlib.import_module(module)
        factory = getattr(mod, name)
    except (ImportError, AttributeError) as error:
        raise ValueError(f'b04 make_real is unavailable under {root} ({entry}); stage the published reader') from error
    source = Path(inspect.getsourcefile(factory)).resolve()
    if not source.is_relative_to(root):
        raise ValueError('make_real resolved outside --reader-root')
    kwargs = dict(perception_factory=None, device='cpu')
    if entry == ENTRY:kwargs['settings'] = {}
    inspect.signature(factory).bind(None, None, [], **kwargs)
    return factory


def shard(value):
    try:
        i, n = map(int, value.split('/'))
        if n < 1 or not 0 <= i < n:raise ValueError()
    except (ValueError, TypeError):
        raise ValueError('--shard must be zero-based i/n, with 0 <= i < n')
    return i, n


def selected(items, value):
    i,n=shard(value)
    return items[i::n]


def select_types(all_items, items, types):
    """ORCH 1739Z: decode type by type (baseline + its modes together), so usage lands per type."""
    wanted=[t for t in types.split(',') if t]
    known={r.get('question_type',r.get('type')) for r in all_items}
    if not wanted or set(wanted)-known:raise ValueError('--types names an unknown item type')
    chosen=[r for r in items if r.get('question_type',r.get('type')) in wanted]
    if not chosen:raise ValueError('--types selects no item of this shard')
    return chosen


def read_records(path):
    if not path.exists():return []
    rows=[]
    with path.open() as f:
        for line in f:
            if not line.endswith('\n'):
                raise ValueError(f'Incomplete JSONL tail in {path}; preserve it and use a fresh output directory')
            row=json.loads(line)
            if row.get('complete') is not True:raise ValueError('Uncommitted JSONL record')
            rows.append(row)
    keys=[(r['id'],r['arm'],r['mode']) for r in rows]
    if len(keys)!=len(set(keys)):raise ValueError('Duplicate completed records')
    return rows


def write_json(path, value):
    path.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')


def tower_records(directory, binding, items):
    """Reuse only complete baseline records with matching immutable parity bindings."""
    root=Path(directory)
    source=json.loads((root/'environment.json').read_text())['binding']
    for key in ('export_sha256','item_set_sha256','items_sha256','reader_sha256',
                'artifact_manifest_sha256'):
        if key not in source or source[key]!=binding[key]:
            raise ValueError('Tower reuse hash mismatch: '+key)
    rows=[r for r in read_records(root/'items.jsonl') if r['arm']=='tower']
    if any(r['mode']!='none' for r in rows):raise ValueError('Tower reuse requires unperturbed records')
    by_id={r['id']:r for r in rows}
    if len(by_id)!=len(rows):raise ValueError('Duplicate tower records')
    expected={r['id']:r for r in items}
    if not expected.keys()<=by_id.keys():raise ValueError('Tower reuse is missing items')
    result=[]
    for identifier,item in expected.items():
        row=by_id[identifier]
        if (row['type']!=item['question_type'] or row['room_key']!=item['room_key'] or
                row.get('intervention')!={'name':'none'} or 'text' not in row['output'] or
                'finish' not in row['output']):raise ValueError('Tower reuse record differs')
        result.append({**row,'reused':True})
    return result,dict(environment_sha256=sha(root/'environment.json'),records_sha256=sha(root/'items.jsonl'))


def run(args, *, make_real=None, factory_options=None):
    manifest=load_manifest(args.items)
    selected_items=selected(manifest['items'], args.shard)
    if getattr(args,'types',None):selected_items=select_types(manifest['items'],selected_items,args.types)
    arms=args.arms.split(',')
    if not arms or len(set(arms))!=len(arms) or any(a not in ('own','tower') for a in arms):
        raise ValueError('Arms must be unique own,tower values')
    interventions=[{'name':'none'},*parse_modes(args.modes)]
    if any(m['name'] in ('donor','gt') for m in interventions) and not factory_options:
        raise ValueError('donor/gt require explicitly bound Heads/GT via factory_options; no inferred donor or GT')
    maker=make_real or reader_factory(args.reader_root,args.reader_entry)
    reviewed = args.reader_entry == ENTRY
    settings = None; mapped = None; mapping = None
    if reviewed:
        from .parity_adapter import settings_for, map_items, artifact_spec, prepare_runtime, validate_own_settings, reader_code_hash
        settings = settings_for(getattr(args, 'settings', DEFAULT_SETTINGS), manifest['name'])
        if Path(settings['export_dir']).resolve() != Path(args.export).resolve():
            raise ValueError('Settings export_dir differs from --export')
        settings_artifact = settings['artifact_manifest']
        if isinstance(settings_artifact, str):
            settings_artifact = artifact_spec(settings_artifact)
        if settings_artifact != artifact_spec(args.artifact_manifest):
            raise ValueError('Settings artifact binding differs from --artifact-manifest')
        mapped, mapping = map_items(manifest['items'], settings, name=manifest['name'])
        if make_real is None:
            if 'own' in arms:validate_own_settings(settings, selected_items)
            prepare_runtime(settings)
    source=Path(inspect.getsourcefile(maker)).resolve()
    export=Path(args.export).resolve();artifact=Path(args.artifact_manifest).resolve()
    out=Path(args.out).resolve()
    if out==export or export in out.parents:raise ValueError('Output must be outside export')
    binding=dict(schema='h10-shard-v1',item_set_sha256=manifest['item_set_sha256'],
                 items_sha256=sha(args.items),export_sha256=export_hash(export),
                 artifact_manifest_sha256=sha(artifact),reader_sha256=code_hash(Path(args.reader_root)/'e2e_reader'),
                 maker_sha256=sha(source),maker_name=maker.__qualname__,reader_entry=args.reader_entry,
                 evaluator_code_sha256=code_hash(),
                 expected_calls_sha256=sha(K/'rows/expected_calls.py'),
                 r0_code_sha256=sha(K/'tree/student_pilot/h1_r0.py'),
                 shard=args.shard,ids=[r['id'] for r in selected_items],
                 count=manifest['count'],arms=arms,modes=interventions,device=args.device,
                 lineage='SFT',step=544,fixture=make_real is not None,
                 r0_pin=manifest['r0_check']['pin'])
    if reviewed:
        binding.update(settings_sha256=digest(settings), mapping_sha256=mapping['sha256'],
                       parity_code_sha256=reader_code_hash(args.reader_root))
    reused=[]
    tower_from=getattr(args,'tower_from',None)
    if tower_from:
        if 'tower' not in arms:raise ValueError('--tower-from requires tower arm')
        if reviewed and not (Path(tower_from)/'environment.json').exists():
            from .parity_adapter import parity_tower_records
            # Require complete coverage of the full registered set, even for a shard.
            all_reused,source_pin=parity_tower_records(tower_from,manifest['items'],mapped,
                settings=settings,export=export,artifact=artifact,reader_root=args.reader_root)
            selected_ids={r['id'] for r in selected_items}
            reused=[r for r in all_reused if r['id'] in selected_ids]
        else:
            reused,source_pin=tower_records(tower_from,binding,selected_items)
        binding['tower_from']=source_pin
    counts=read_counts(selected_items,interventions,arms,bool(tower_from))
    print(json.dumps(dict(read_plan=counts,shard=args.shard)),flush=True)
    out.mkdir(parents=True,exist_ok=True)
    with (out/'writer.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('Another writer holds this shard output')
        env=out/'environment.json'
        if env.exists():
            old=json.loads(env.read_text())
            if old['binding']!=binding:raise ValueError('Resume binding differs; use a fresh output directory')
        else:
            if (out/'items.jsonl').exists():raise ValueError('Records lack environment binding')
            write_json(env,dict(binding=binding,settings=settings,items=str(Path(args.items).resolve()),
                export=str(export),artifact_manifest=str(artifact),reader_root=str(Path(args.reader_root).resolve()),
                utc=datetime.now(timezone.utc).isoformat(),host=platform.node(),python=sys.version,
                cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
                threads={k:os.environ.get(k) for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS')}))
        if mapping is not None:
            mapping_path=out/'item_mapping.json'
            if mapping_path.exists() and json.loads(mapping_path.read_text())!=mapping:
                raise ValueError('Resume mapping differs')
            write_json(mapping_path,mapping)
        rows=read_records(out/'items.jsonl')
        allowed=plan(selected_items,arms,interventions)
        done={(r['id'],r['arm'],r['mode']):r for r in rows}
        if not set(done)<=allowed:raise ValueError('Completed records are outside shard plan')
        from .perception_own import configured
        timings=[];started=time.perf_counter();added=0
        sample=[r['seconds'] for r in rows if not r.get('reused')][:10]
        projection_path=out/'projection.json'
        def project():
            if len(sample)!=10:return
            seconds=sum(sample)/10
            projection=dict(sample_items=10,seconds_per_read=seconds,read_plan=counts,
                            expected_card_hours=counts['reads']*seconds/3600,
                            excludes_model_loading=True)
            write_json(projection_path,projection)
            print(json.dumps(dict(projection=projection)),flush=True)
        if len(sample)==10 and not projection_path.exists():project()
        with (out/'items.jsonl').open('a') as stream:
            for row in reused:
                key=(row['id'],'tower','none')
                if key in done:continue
                stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
                done[key]=row;added+=1
            for arm in arms:
                cached_generator=None
                for mode in interventions:
                    key=mode_key(mode)
                    todo=[r for r in selected_items if (r['id'],arm,key) in allowed and (r['id'],arm,key) not in done]
                    if not todo:continue
                    bound=[]
                    def own_factory(artifact, model, device, *, processor=None, item=None):
                        value=configured(mode,**(factory_options or {}))(artifact,model,device,
                            processor=processor,item=item,settings=settings)
                        bound[:]=[value]
                        return value
                    factory=None if arm=='tower' else own_factory
                    t=time.perf_counter()
                    if reviewed:
                        if cached_generator is None:
                            cached_generator=maker(export,artifact_spec(artifact),
                                [mapped[r['id']] for r in selected_items],perception_factory=factory,
                                device=args.device,settings=settings)
                        generator=cached_generator
                    else:
                        generator=maker(export,artifact,selected_items,perception_factory=factory,device=args.device)
                    load_s=time.perf_counter()-t
                    try:
                        for item in todo:
                            t=time.perf_counter();output=generator(mapped[item['id']] if reviewed else item);seconds=time.perf_counter()-t
                            if not isinstance(output,dict) or 'text' not in output or 'finish' not in output:
                                raise ValueError('make_real generator must return reader output with text and finish')
                            if arm=='own' and bound and 'heads' in bound[-1].last:
                                state=bound[-1].last;heads=state['heads']
                                output={**output,'heads':dict(pose9=heads.pose9.tolist(),gravity=heads.gravity.tolist()),
                                        'intervention':state['intervention'], 'finite_heads':state.get('finite_heads',{})}
                            row=dict(id=item['id'],room_key=item['room_key'],type=item['question_type'],
                                     arm=arm,mode=key,intervention=mode,applied=arm=='own',
                                     output=output,seconds=seconds,complete=True)
                            stream.write(json.dumps(row,allow_nan=False)+'\n');stream.flush();os.fsync(stream.fileno())
                            done[(item['id'],arm,key)]=row;added+=1
                            if len(sample)<10:
                                sample.append(seconds)
                                if len(sample)==10:project()
                            print(json.dumps(dict(id=item['id'],arm=arm,mode=key,finish=output['finish'],seconds=seconds)),flush=True)
                    finally:
                        if not reviewed and callable(getattr(generator,'close',None)):generator.close()
                        del generator
                    timings.append(dict(arm=arm,mode=mode,load_s=load_s,items=len(todo)))
                if cached_generator is not None:
                    if callable(getattr(cached_generator,'close',None)):cached_generator.close()
                    del cached_generator
                    import gc
                    gc.collect()
        with (out/'timings.jsonl').open('a') as f:
            f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),seconds=time.perf_counter()-started,
                                   added=added,skipped=len(rows),loads=timings))+'\n');f.flush()
        return dict(added=added,skipped=len(rows),completed=len(done),expected=len(allowed))


def parser():
    p=argparse.ArgumentParser(description=__doc__)
    for key in ('items','export','artifact-manifest','reader-root','out'):p.add_argument('--'+key,required=True)
    p.add_argument('--shard',default='0/1');p.add_argument('--types',default=None,help='comma list of question types to decode');p.add_argument('--arms',default='own,tower')
    p.add_argument('--modes',default=DEFAULT_MODES)
    p.add_argument('--tower-from',help='b04 run directory containing gpu_results/own_depth_p*/items.jsonl and LOAD_RECEIPT.json')
    p.add_argument('--settings',default=DEFAULT_SETTINGS,help='Reviewed b04 settings JSON')
    p.add_argument('--device',default='cuda:0');p.add_argument('--reader-entry',default=ENTRY)
    return p


def main(argv=None):
    p=parser();args=p.parse_args(argv)
    try:print(json.dumps(run(args)));return 0
    except (ValueError,FileNotFoundError,ImportError) as e:p.exit(2,str(e)+'\n')

if __name__=='__main__':raise SystemExit(main())
