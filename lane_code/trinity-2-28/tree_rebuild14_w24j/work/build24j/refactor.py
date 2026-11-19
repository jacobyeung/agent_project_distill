from pathlib import Path

tree = Path(__file__).resolve().parents[1] / 'tree_r1'
path = tree / 'launch_r1/entry.py'
s = path.read_text()
begin = s.index('    from student_pilot.carrier_c1_run import identity\n', s.index('def frame_host'))
body = s[begin:]
root = body[body.index('    root = Path(root).resolve()'):body.index('    environment =')]
environment = body[body.index('    environment ='):body.index('    try:')]
restore = body[body.index('        os.umask(previous_umask)'):body.index("    write(root/'receipt.json'")]
runtime = body[body.index('        expected = plan'):body.index('        # The source staging')]
staging = body[body.index('        # The source staging'):body.index('        from student_pilot.scene_division_gate')]
scene = body[body.index('        from student_pilot.scene_division_gate'):body.index('        from student_pilot.s1_routing import build')]
selection = body[body.index('        from student_pilot.s1_routing import build'):body.index('        from student_pilot.s1_admission import admit')]
finish = body[body.index("        result['config_identity']"):body.index('    except (ValueError')]
dedent = lambda value: '\n'.join(line[4:] if line.startswith('    ') else line for line in value.split('\n'))
helpers = '''def begin_host(cfg, root, request, *, job_tmp_token=None):
    """Establish freshness and confinement before staging any job inputs."""
    from student_pilot.carrier_c1_run import identity
''' + root + '    return root, job_tmp, result\n\n\n' + '''@contextmanager
def host_environment(job_tmp):
    """Confine caches and private directories, restoring the caller on refusal."""
''' + environment + '    try:\n        yield\n    finally:\n' + restore + '\n\n' + '''def check_host_runtime(cfg, request, result):
    from student_pilot.checkpoint_space import plan
    from student_pilot.carrier_c1_sweep import recipe_for
''' + dedent(runtime) + '\n\n' + '''def stage_host(cfg, root, request, job_tmp):
    """Stage authenticated inputs and retain the native routing composition."""
''' + dedent(staging) + '    return staged_cfg\n\n\n' + '''def check_host_scene(cfg, result):
''' + dedent(scene).replace('staged_cfg', 'cfg') + '\n\n' + '''def check_host_selection(cfg, root, request, result):
''' + dedent(selection).replace('staged_cfg', 'cfg') + '\n\n' + '''def finish_host(cfg, root, result, loader_audit, *, named_refusals=False):
    """Certify the configuration read by the final loader audit."""
    from student_pilot.carrier_c1_run import identity
    result['loader_audit'] = loader_audit
''' + dedent(finish).replace("identity(load(pinned(produced)))", 'identity(cfg)') + '    return result\n\n\n'
# Keep the legacy failure string for mode p; q names the failed assertion.
helpers = helpers.replace("    if not all(result['assertions'].values()) or not result['loader_audit']['complete']:", "    if named_refusals:\n        for name in ASSERTIONS:\n            if result['assertions'][name] is not True:\n                raise ValueError('R1_HOST_ASSERTION_FALSE:'+name)\n    if not all(result['assertions'].values()) or not result['loader_audit']['complete']:")
frame = '''def frame_host(cfg, root, request, *, job_tmp_token=None):
    """Run the production CPU preparation from a fresh root; failures stay explicit."""
    from student_pilot.r1_coverage import deferred
    deferred(cfg, request)
    root, job_tmp, result = begin_host(cfg, root, request, job_tmp_token=job_tmp_token)
    with host_environment(job_tmp):
        try:
            if os.environ.get('CUDA_VISIBLE_DEVICES', ''):
                raise ValueError('CPU_ONLY_REQUIRED')
            check_host_runtime(cfg, request, result)
            staged_cfg = stage_host(cfg, root, request, job_tmp)
            check_host_scene(staged_cfg, result)
            check_host_selection(staged_cfg, root, request, result)
            from student_pilot.s1_admission import admit as native_admit
            write(root/'c.json', staged_cfg)
            prepared = native_admit(file_pin(root/'c.json'), root/'p', [root], threads=8, prepare_only=True)
            result['preparation'] = prepared
            from student_pilot.r1_population import bind_prepared
            produced = bind_prepared(load(pinned(prepared['config'])), root/'population')
            result['population_config'] = produced
            # This audit must come from the same production reader and final sampler indices.
            from student_pilot.r1_loader import production_audit
            result['loader_audit'] = production_audit(load(pinned(produced)), root/'audit')
            finish_host(load(pinned(produced)), root, result, result['loader_audit'])
        except (ValueError, KeyError, TypeError, OSError) as error:
            result['missing'].append(str(error))
    write(root/'receipt.json', result)
    return result
'''
s = s[:s.index('def frame_host')] + helpers + frame
s = s.replace('import os\n', 'import os\nfrom contextlib import contextmanager\n', 1)
path.write_text(s)
