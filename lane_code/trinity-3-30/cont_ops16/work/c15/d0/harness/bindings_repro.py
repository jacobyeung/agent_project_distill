"""Reconstruct the bindings that rebuild kit 07ca49df from its own k/ records (output: JSON to stdout).
Optional argv[2]: a JSON file of D0 overrides merged into bindings['config'] and bindings['deployment']."""
import copy, hashlib, json, sys
base = sys.argv[1]
K = base + '/k/'
def pin(name):
    p = K + name
    return dict(path=p, sha256=hashlib.sha256(open(p, 'rb').read()).hexdigest())
cfg = json.load(open(K + 'b02e4385.json'))
launch = json.load(open(K + 'launch.json'))
computed = {'code', 's1_routing', 'scene_coverage', 'route_table', 's1_route_policy', 'stall_guard',
            'checkpoint_disk_guard', 'remove_files', 'dev_scene_exclusions', 'benchmark_scene_exclusions'}
config = {k: copy.deepcopy(v) for k, v in cfg.items() if k not in computed}
b = dict(world_size=4, kit_key='07ca49df', run_key='469ddece', config=config,
         frame_map=pin('frame_map.jsonl.gz'), frame_plan=pin('frame_plan.json.gz'), fps_authority=pin('frame_rates.json'),
         scene_reference=pin('scene_reference.json'), route_table=pin('routes.json'),
         small_inputs={n: pin(n) for n in ('input_mdg_clips.json', 'input_mdg_rasters.json', 'input_source_tokenizer.json')},
         review=pin('review.json'), staging=pin('staging.json'), archive=pin('archive.json'),
         authorization=json.load(open(K + '4.json')), persistent_run_root=launch['persistent_run_root'],
         frame_roots=launch['in_job_admission']['frame_roots'], status='BLOCKED',
         scene_source_map=cfg['scene_coverage']['source_map'],
         input_catalog={k: v for k, v in cfg['s1_routing']['catalog'].items()})
if len(sys.argv) > 2:
    over = json.load(open(sys.argv[2]))
    b['config'].update(over.get('config', {})); b['deployment'] = over.get('deployment', {})
    for k in ('kit_key', 'run_key', 'persistent_run_root'):
        if k in over: b[k] = over[k]
json.dump(b, sys.stdout, indent=1, sort_keys=True)
