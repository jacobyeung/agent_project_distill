"""Keep the pinned phase implementation and observe its prefill and commits."""
from contextlib import contextmanager
import builtins
import io
import json
import os
from pathlib import Path
import sys
import tarfile
import time
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parent))
import job_support as H
from phase_support import budget, canary, refuse_incomplete

KIT = Path('/scratch/jjyeung/orch_n30/k1_ops3/kc/k1_build/work/kit_k1a')
NATIVE = Path('/scratch/jjyeung/orch_cd/evalx/work/milestone/native_package_s24_05/sources/sj/orch_cd/evalx/work/milestone/native/out2')
IDENTITY = '84ea03af6049a179bf4a44619b1534fdcb528b5511544189236254b5d66842cb'

@contextmanager
def metadata_mapping(mapping):
    """CPU-only exact-file resolution; do not edit pins or metadata contents."""
    if not mapping:
        yield
        return
    old_open, old_io, old_stat = builtins.open, io.open, Path.stat
    old_tar_open = tarfile.open
    def translated(path):
        return mapping.get(os.fspath(path), path) if isinstance(path, (str, os.PathLike)) else path
    def opened(path, mode='r', *args, **kwargs):
        if translated(path) != path and any(x in mode for x in 'wax+'):
            raise ValueError('Metadata mapping is read-only')
        return old_open(translated(path), mode, *args, **kwargs)
    def io_opened(path, mode='r', *args, **kwargs):
        if translated(path) != path and any(x in mode for x in 'wax+'):
            raise ValueError('Metadata mapping is read-only')
        return old_io(translated(path), mode, *args, **kwargs)
    builtins.open, io.open = opened, io_opened
    def tar_opened(name=None, mode='r', *args, **kwargs):
        if translated(name) != name and not mode.startswith('r'):
            raise ValueError('Metadata archives are read-only')
        return old_tar_open(translated(name), mode, *args, **kwargs)
    tarfile.open = tar_opened
    Path.stat = lambda path, *a, **kw: old_stat(Path(translated(path)), *a, **kw)
    try:
        yield
    finally:
        builtins.open, io.open, Path.stat = old_open, old_io, old_stat
        tarfile.open = old_tar_open

def prepared(manifest, mapping=None):
    sys.path.insert(0, str(NATIVE))
    import read_runtime
    with metadata_mapping(mapping or {}):
        cfg, receipt, model = read_runtime.prepared(
            manifest['gpu']['config'], manifest['gpu']['artifact'], manifest['gpu']['data_receipt'])
        from student_pilot import carrier_c1_run as trainer
        assert trainer.identity(cfg) == IDENTITY
        assert read_runtime.metadata(manifest['gpu']['artifact'])['config_sha256'] == IDENTITY
    return dict(passed=True, config_identity=IDENTITY, artifact=manifest['gpu']['artifact'],
                model_manifest=receipt['model'], fresh_preparation=False)

def run(config, fixture=None):
    sys.path[:0] = [str(KIT / 'work'), str(KIT / 'native_kit')]
    import verify_sources
    import bindings as B
    import boundaries
    import k1_phases as F
    import k1_pipeline as P
    source = Path(config['source'])
    source.mkdir(parents=True, exist_ok=True)
    (source / 'metadata').mkdir(exist_ok=True)
    manifest = B.load(config['manifest'])
    assert H.sha(config['manifest']) == config['manifest_sha256']
    evidence = dict(verified_sources=verify_sources.verify())
    evidence['prepared'] = prepared(manifest, config.get('metadata_mapping'))
    with metadata_mapping(config.get('metadata_mapping', {})):
        P.check_manifest(manifest, 'own')
    reference = B.load(config['tower_binding'])
    identity = dict(sources=B.source_identity(), producer_sha256=B.sha(F.__file__))
    assert all(reference[k] == v for k, v in identity.items())
    evidence['binding'] = dict(**identity, manifest_sha256=B.digest(manifest),
                               tower_manifest_sha256=reference['manifest_sha256'],
                               amendment=2, captures_unchanged=config['captures_unchanged'])
    # For the CPU fixture, check all 300 captures before using a six-capture run.
    if fixture is not None:
        manifest = fixture['manifest']
    plan = B.digest(manifest)
    evidence['restore'] = H.restore(config['pointer'], source, plan)
    out = source / 'native/probe'
    out.mkdir(parents=True, exist_ok=True)
    refuse_incomplete(B, manifest, out)
    if (out / 'STOP').exists() and (out / 'STOP').read_text().strip() != 'RESUME':
        raise ValueError('STOP requires operator review')
    elapsed = time.time() - config['started_unix']
    timing = budget(elapsed, config['capture_reserve_seconds'], config['return_margin_seconds'],
                    deadline_unix=config.get('deadline_unix'), started_unix=config['started_unix'])
    if fixture is not None:
        timing['max_seconds'] = min(timing['max_seconds'], fixture['max_seconds'])
    H.dump(source / 'metadata/budget.json', timing)
    if timing['max_seconds'] <= 0:
        (out / 'STOP').write_text('BUDGET\n')
    state = dict(current=None, started=None, prefill=None, tokens={}, first_three_returned=False)
    if (out / 'TOKENS.json').exists():
        state['tokens'] = B.load(out / 'TOKENS.json')
    first = {c['canonical'] for c in manifest['captures'][:3]}
    journal_code = F.journal.__code__
    longest = config['capture_reserve_seconds']

    def observe(frame, event, result):
        nonlocal longest
        if event != 'return':
            return
        if frame.f_code.co_name == '_prepare_decode' and frame.f_code.co_filename.endswith('/student_pilot/carrier_c1_decode.py'):
            # The pinned function performs prefill and returns before Row.step.
            # Reading these scalars neither changes the result nor retains tensors.
            state['prefill'] = dict(prompt_tokens=int(result.prompt_length), generated_tokens=0,
                                    counter='pinned_prefill_returns_before_sampling')
        if frame.f_code != journal_code:
            return
        row = frame.f_locals
        if row['event'] == 'capture_start':
            state.update(current=row['canonical'], started=time.monotonic(), prefill=None)
        elif row['event'] == 'capture_commit':
            key = row['canonical']
            if key == state['current']:
                observed = state['prefill']
                if fixture is not None:
                    observed = dict(prompt_tokens=4700, generated_tokens=0, counter='CPU_FIXTURE')
                if observed is None:
                    raise ValueError('Prefill observer did not record this capture')
                seconds = time.monotonic() - state['started']
                state['tokens'][key] = dict(**observed, seconds=seconds)
                longest = max(longest, seconds)
                H.dump(out / 'TOKENS.json', state['tokens'])
            if first <= set(state['tokens']) and not state['first_three_returned']:
                report = canary(B, F, manifest, out, fixture is not None,
                                config['canary_limit_seconds'])
                report['observations'] = {k: state['tokens'][k] for k in sorted(first)}
                report['synthetic'] = fixture is not None
                H.dump(source / 'metadata/CANARY.json', report)
                H.snapshot_manifest(source)
                token = 'c' + uuid.uuid4().hex[:16]
                H.publish(source, config['pool'], config['cloud'], token, plan,
                          0 if report['passed'] else 1, fixture is not None)
                state['first_three_returned'] = True
                if not report['passed']:
                    raise ValueError('Canary failed; STOP written and returned')
            allocation = min(43200, config['deadline_unix'] - config['started_unix']) if config.get('deadline_unix') is not None else 43200
            if time.time() - config['started_unix'] + longest + config['return_margin_seconds'] >= allocation:
                (out / 'STOP').write_text('BUDGET\n')

    H.dump(source / 'metadata/admission.json', evidence)
    old_profile, old_argv = sys.getprofile(), sys.argv
    code, failure = 1, None
    try:
        sys.setprofile(observe)
        if timing['max_seconds'] <= 0:
            # The pinned CLI requires a positive cap; return before dispatch.
            code = 4
        elif fixture is not None:
            code = F.run(manifest, out, fixture['boundary'], 'own', timing['max_seconds'])
        else:
            sys.argv = [str(KIT / 'work/k1_pipeline.py'), 'cache', '--manifest', config['manifest'],
                        '--out', str(out), '--phase', 'own', '--max-seconds', str(timing['max_seconds'])]
            code = P.main()
    except Exception as error:
        failure = dict(type=type(error).__name__, message=str(error))
        H.dump(source / 'metadata/failure.json', failure)
        (out / 'STOP').write_text('Worker failure; operator review required\n')
    finally:
        sys.setprofile(old_profile)
        sys.argv = old_argv
        assert B.source_identity() == identity['sources']
        if code == 4 and failure is None and (out / 'STOP').exists() and (out / 'STOP').read_text().strip() == 'BUDGET':
            # The pinned phase explicitly accepts RESUME. Preserve the file and
            # distinguish a normal allocation boundary from a canary refusal.
            (out / 'STOP').write_text('RESUME\n')
        if code != 4 or failure is not None:
            marker = 'COMPLETE.json' if code == 0 and failure is None else 'FAILED.json'
            H.dump(source / marker, dict(plan_sha256=plan, synthetic=fixture is not None, returncode=code))
        H.snapshot_manifest(source)
        token = 'a' + uuid.uuid4().hex[:16]
        returned = H.publish(source, config['pool'], config['cloud'], token, plan, code, fixture is not None)
        if code in (0, 4) and failure is None and (not (out / 'STOP').exists() or (out / 'STOP').read_text().strip() == 'RESUME'):
            H.advance(config['pointer'], config['pool'], token, plan, returned)
    if failure:
        raise ValueError('Worker failed; evidence returned')
    return dict(code=code, canary_returned=state['first_three_returned'],
                observations=state['tokens'], return_receipt=returned, admission=evidence)

if __name__ == '__main__':
    result = run(json.loads(Path(sys.argv[1]).read_text()))
    raise SystemExit(0 if result['code'] in (0, 4) else result['code'])
