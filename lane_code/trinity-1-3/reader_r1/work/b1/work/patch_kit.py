from pathlib import Path
P=Path('work/p')
def edit(name,a,b):
 p=P/name;s=p.read_text();assert a in s,(name,a);p.write_text(s.replace(a,b))
edit('b/e2e_reader/servers.py',"names = re.findall(r'\"([^\"]*)\"', call)","names = re.findall(r'[ab]=\"([^\"]*)\"', call)")
edit('b/e2e_reader/servers.py',"state=session.box_registry.states.get(name),\n                    stage1=deepcopy(socket.stage1.get(name, {}))) for name in names\n                    if name in session.box_registry.states or name in socket.stage1]", "state=session.box_registry.states.get(name),\n                    chosen_index=socket.stage1.get(name, {}).get('chosen_index'),\n                    linked_candidates=socket.stage1.get(name, {}).get('linked_candidates')) for name in names]")
edit('h1eval/perception.py',"built={'scale':1.,'heads':heads,'intervention':intervention}","built={'scale':1.,'heads':heads,'intervention':intervention,'frames':frames}")
edit('h1eval/h10/depth_snapshot.py',"    if geometry is None:\n        return None", "    if geometry is None:\n        from h1eval.perception import own_profile\n        geometry = own_profile(state['heads'], state['frames'])")
edit('h1eval/h10/depth_snapshot.py','geometry.contract.frame_map.indices','geometry.contract.frame_map.source_indices')
# Build directly from the complete staged payload, with no external code discovery.
p=P/'orchard_h10/build.py';s=p.read_text();a=s.index('B=Path(');b=s.index('\ndef batch(',a)
s=s[:a]+'''T=K/'orchard_h10/vendor'
CORE=('orchard_launcher.py','orchard_job.py','orchard_stage.py','export_stage.py',
      'orchard_results.py','return_io.py','stdout_transfer.py','trace_runtime.py',
      'chain_save.py','ORCHARD_ASSETS.json','MODELS.json','TRANSPORT.json')


def sources():
    """Rebuild the full staged payload inventory, including nested selector inputs."""
    original = json.loads((K/'9.json').read_text())['payload_pins']
    files = {name:K/name for name in original}
    files['h1eval/h10/depth_snapshot.py'] = K/'h1eval/h10/depth_snapshot.py'
    for name, path in files.items():
        if path.is_symlink() or not path.is_file():
            raise ValueError('Code package requires a regular source: '+name)
    return files

''' +s[b:]
s=s.replace('def build(destination, token=None, refresh=False, reader_repin=None):',"def build(destination, token=None, refresh=False, reader_repin=None, rule='null_argmax'):\n    if rule not in ('null_argmax', 'candidates_argmax'):\n        raise ValueError('unknown_stage1_select_rule')")
s=s.replace("if not destination.is_relative_to(K):raise ValueError('Build output must stay in K')", "if not destination.is_relative_to(K.parents[1]):raise ValueError('Build output must stay in the workdir')")
s=s.replace("             order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),", "             order=list(__import__('orchard_h10.common',fromlist=['ORDER']).ORDER),\n             types=['object_abs_distance'], modes=['none'], stage1_select_rule=rule, save_own_depth=True,")
s=s.replace("package=str(destination.relative_to(K))", "package=str(destination.relative_to(K.parents[1]))")
s=s.replace("meaning='step-544 own dev-S1; registered modes; five ordered types'", "meaning='step-544 own dev-S1 distance baseline; '+rule")
s=s.replace("    a=p.parse_args();print(json.dumps(build(a.out,a.token,a.refresh,a.reader_repin),sort_keys=True))", "    p.add_argument('--rule',choices=('null_argmax','candidates_argmax'),default='null_argmax')\n    a=p.parse_args();print(json.dumps(build(a.out,a.token,a.refresh,a.reader_repin,a.rule),sort_keys=True))")
p.write_text(s)
edit('orchard_h10/prepare.py',"env_roots=inputs.get('env_roots',[]),arm='own_depth')", "env_roots=inputs.get('env_roots',[]),arm='own_depth',\n        stage1_select_rule=config.get('stage1_select_rule','null_argmax'),\n        save_own_depth=config.get('save_own_depth',True))")
edit('orchard_h10/job.py',"    if 'types' in inputs:","    if cfg.get('types') and inputs.get('types') != cfg['types']:\n        raise ValueError('Input types differ from package plan')\n    if cfg.get('modes') == ['none'] and inputs.get('optional'):\n        raise ValueError('Baseline package has no optional reads')\n    if 'types' in inputs:")
edit('orchard_h10/job.py',"                     types=inputs.get('types') or list(ORDER),", "                     types=cfg.get('types') or inputs.get('types') or list(ORDER),\n                     modes=cfg.get('modes'), stage1_select_rule=cfg.get('stage1_select_rule','null_argmax'),")
edit('orchard_h10/runner.py',"    if t<len(ORDER):args+=['--types',ORDER[t]]", "    if config.get('modes'):args+=['--modes',','.join(config['modes'])]\n    if t<len(ORDER):args+=['--types',ORDER[t]]")
edit('orchard_h10/runner.py',"expected=plan(chosen,['own'],[{'name':'none'},*modes(DEFAULT_MODES)])", "expected=plan(chosen,['own'],modes(','.join(config['modes'])) if config.get('modes') else [{'name':'none'},*modes(DEFAULT_MODES)])")
edit('orchard_h10/runner.py',"types=types,arms=['own'])", "types=types,arms=['own'],\n                  stage1_select_rule=config.get('stage1_select_rule','null_argmax'),modes=config.get('modes'))")
