"""First production capture of g.w.run on CPU, inside the pinned namespace.

Runs the operator's prepare() for read 0, then the exact first iteration of
g.w.run (stage_capture, bind_item, early G3T tower, capped real factory, one
prefill through capture_one, parity against the sealed reference) with
device='cpu' in place of 'cuda:0'. Writes one JSON result to argv[2].
"""
import json
import os
from pathlib import Path
import resource
import runpy
import sys
import time
import traceback

started = time.monotonic()
cfg_path, result_path, operator_path = sys.argv[1:4]
phases = {}
result = dict(passed=False, phases=phases)


def mark(name):
    phases[name] = dict(seconds=time.monotonic()-started,
                        peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)


def save():
    result.update(wall_seconds=time.monotonic()-started,
                  peak_rss_bytes=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024)
    Path(result_path).write_text(json.dumps(result, indent=2, default=str)+'\n')


try:
    c = json.loads(Path(cfg_path).read_text()); config = c['config']
    p = Path(config['package'])
    sys.path[:0] = [str(p/'b'), str(p/'tree'), str(p)]
    import l
    l.install(p)
    from orchard_h10.common import install_process_guard
    install_process_guard(Path(cfg_path).resolve().parent)
    import torch
    torch.set_num_threads(int(os.environ['OMP_NUM_THREADS']))
    import transformers
    result['environment'] = dict(python=sys.executable, prefix=sys.prefix, torch=torch.__version__,
                                 transformers=transformers.__version__, torch_file=torch.__file__,
                                 transformers_file=transformers.__file__, threads=torch.get_num_threads())
    op = runpy.run_path(operator_path, run_name='real_batch')
    wcfg = op['prepare'](config)[0]
    mark('prepare')
    from g import w
    root = w.bind_reader_root()
    from h1eval.h10.parity_adapter import settings_for, artifact_spec, prepare_runtime, make_capped_real
    from h1eval.items import digest
    from e2e_reader import parity
    from orchard_h10.s import stage_capture
    reference = json.loads((Path(w.__file__).parent/'8.json').read_text())
    refs = w.load_rows(); by_id = {r['item_id']: r for r in refs}
    selected = [by_id[i] for i in reference['representatives']]
    ref = selected[0]
    settings = settings_for(wcfg['settings'], 'devs1_routed'); prepare_runtime(settings)
    if any(settings.get(k) for k in ('sam3', 'selector_head', 'scale_head')):raise ValueError('E07')
    if settings['save_own_depth'] or settings['perception_memo_modules'] != ['g3t']:raise ValueError('E04')
    captures = parity._captures(settings.get('frames_json', parity.FRAMES))
    dense = parity._captures(settings.get('dense_manifest', parity.DENSE))
    for r in refs:
        native = r['task']['native']
        if digest(r['task']) != r['mapping']['task_sha256'] or digest(dict(anchors=captures[native], dense=dense[native])) != r['mapping']['frame_binding_sha256']:
            raise ValueError('E05')
    result['unit'] = dict(read=0, capture=ref['capture'], item_id=ref['item_id'], representatives=len(selected),
                          perception_memo=settings['perception_memo'], stage1_select_rule=settings.get('stage1_select_rule'))
    stage_capture(settings, ref['capture'])
    bound = parity.bind_item(ref['task'], settings)
    spec = artifact_spec(settings['artifact_manifest'])
    mark('staged_capture')
    # g.w.start_tower with device='cpu' (no CUDA synchronize).
    from e2e_reader.artifact import Artifact, Audit
    from e2e_reader.real import TowerG3T
    artifact = Artifact(spec['root'], spec['name'], spec['sha256'],
        code_roots=spec.get('code_roots'), env_roots=settings.get('env_roots', ()),
        write_roots=[os.environ[k] for k in ('TRITON_CACHE_DIR', 'TORCHINDUCTOR_CACHE_DIR', 'XDG_CACHE_HOME',
                                            'HF_HOME', 'TORCH_HOME') if os.environ.get(k)], required_roles=('g3t',))
    artifact.manifest = dict(artifact.manifest, components={'g3t': artifact.manifest['components']['g3t']})
    artifact.verify()
    early = TowerG3T(artifact, 'cpu')
    t0 = time.perf_counter()
    with torch.no_grad(), Audit(artifact):first_tower = early(bound['frames'])
    tower_seconds = time.perf_counter()-t0
    import numpy as np
    result['tower'] = dict(seconds=tower_seconds, **{k: list(np.asarray(v).shape) for k, v in first_tower.items() if k != 'source_hw'},
                           source_hw=list(first_tower['source_hw']),
                           depth_grid_finite=bool(np.isfinite(first_tower['depth_grid']).all()),
                           depth_grid_range=[float(np.min(first_tower['depth_grid'])), float(np.max(first_tower['depth_grid']))])
    mark('tower')
    factory = make_capped_real(settings['export_dir'], spec, [r['task'] for r in refs], settings=settings, device='cpu')
    if factory.load_info['export'].get('step') != 544:raise ValueError('E06')
    gen = factory.generator
    gen.perception.g3t = early
    w.assert_reader_root(root)
    result['model'] = dict(cls=type(gen.model).__name__, dtype=str(next(gen.model.parameters()).dtype),
                           parameters=sum(x.numel() for x in gen.model.parameters()), device=str(gen.device),
                           export_step=factory.load_info['export'].get('step'))
    mark('model_loaded')
    t0 = time.perf_counter()
    with w.fresh_perception(gen):
        row = w.capture_one(gen, bound, ref, tower_result=first_tower)
    prefill_seconds = time.perf_counter()-t0
    mark('capture_one')
    per_item = []
    for iid, expected in reference['geometry'].items():
        if expected['capture'] == ref['capture']:
            per_item.append(dict(item_id=iid, **w.compare(row['metadata']['geometry'], expected['geometry'], reference['bounds'])))
    geometry = row['metadata']['geometry']
    result['capture'] = dict(seconds=prefill_seconds, prefills=row['prefills'], decode_steps=row['decode_steps'],
                             timings=row['timings'], keys=sorted(row), metadata_keys=sorted(row['metadata']),
                             geometry_shapes={k: list(np.asarray(v).shape) for k, v in geometry.items() if not isinstance(v, (str, dict))},
                             parity=dict(trusted=all(x['trusted'] for x in per_item) and bool(per_item), items=per_item,
                                         bounds=reference['bounds']))
    result['passed'] = result['capture']['parity']['trusted'] and row['prefills'] == 1 and row['decode_steps'] == 0
except BaseException as error:
    result.update(error=type(error).__name__+': '+str(error)[:4000],
                  traceback=traceback.format_exc()[-12000:])
finally:
    save()
raise SystemExit(0 if result['passed'] else 1)
