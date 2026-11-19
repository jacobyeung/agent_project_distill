"""The CPU host proof gates R1's native preparation and trainer."""
import os
from contextlib import contextmanager
from pathlib import Path
import shutil
import tempfile
from student_pilot.p3_provenance import digest, file_pin, load, pinned, write


ASSERTIONS = ('disk_plan', 'routing_selection', 'empty_root', 'job_tmp', 'runtime_binaries', 'directory_modes', 'scene_division')
TMP_NAMESPACE = Path('/tmp')
_FRESH_DIRECTORIES = {}


def create_job_tmp(path):
    """Create a private namespace before staging and issue a process-local, one-use token."""
    path = Path(path).absolute()
    if path == TMP_NAMESPACE.resolve() or not path.resolve().is_relative_to(TMP_NAMESPACE.resolve()):
        raise ValueError('R1_HOST_JOB_TMP_REQUIRED')
    path.mkdir(mode=0o700, parents=False, exist_ok=False)
    stat = path.stat()
    token = object()
    _FRESH_DIRECTORIES[token] = (path.resolve(), stat.st_dev, stat.st_ino)
    return token


def temporary_paths(value, job_tmp):
    """Reject input paths that depend on another job's filesystem."""
    if isinstance(value, dict):
        for key, item in value.items():
            temporary_paths(key, job_tmp)
            temporary_paths(item, job_tmp)
    elif isinstance(value, list):
        for item in value:
            temporary_paths(item, job_tmp)
    elif isinstance(value, str):
        path = Path(value)
        resolved = (path if path.is_absolute() else job_tmp/path).resolve()
        if '..' in path.parts or not resolved.is_relative_to(job_tmp.resolve()):
            raise ValueError('R1_HOST_PATH_OUTSIDE_JOB_TMP')


def fresh_tmp(root, request, token=None):
    job_tmp = Path(request.get('job_tmp', '')).absolute()
    namespace = TMP_NAMESPACE.resolve()
    if (not request.get('job_tmp') or job_tmp == namespace or not job_tmp.resolve().is_relative_to(namespace)
            or job_tmp.is_symlink() or not root.is_relative_to(job_tmp)):
        raise ValueError('R1_HOST_JOB_TMP_REQUIRED')
    if token is not None:
        stat = job_tmp.stat()
        expected = _FRESH_DIRECTORIES.pop(token, None)
        if expected != (job_tmp.resolve(), stat.st_dev, stat.st_ino) or stat.st_mode & 0o777 != 0o700:
            raise ValueError('R1_HOST_JOB_TMP_TOKEN_INVALID')
        if any(job_tmp.iterdir()):
            raise ValueError('R1_HOST_JOB_TMP_NOT_EMPTY')
    elif job_tmp.exists():
        raise ValueError('R1_HOST_JOB_TMP_NOT_FRESH')
    return job_tmp


def admit(cfg):
    from student_pilot.r1_coverage import deferred
    deferred(cfg, read_pins=True)
    value = cfg.get('r1_training', {})
    from student_pilot.r1_persisted import init_policy, export_only
    policy = init_policy(value)
    if value.get('handover_receipt'):
        receipt = load(pinned(value['handover_receipt']))
        if policy is not None:
            export_only(receipt, value.get('proof_mode'), init_policy=policy)
        elif receipt.get('schema') == 'p-export-only-v1':
            raise ValueError('P_EXPORT_ONLY_TRAINING_LAUNCH_REFUSED')
    from student_pilot.r1_training import validate, training_components, start
    from student_pilot.r1_mix import validate_binding
    from student_pilot.carrier_c1_run import identity
    from student_pilot.b7_inputs import layout
    validate(cfg)
    layout(cfg)
    value = cfg['r1_training']
    if set(value.get('store_hashes', {})) != {'pose','vqa','routing','pointing'}:
        raise ValueError('R1_ALL_STREAM_IDENTITIES_REQUIRED')
    from student_pilot.r1_training import boundary
    boundary(cfg,0)
    training_components(value['registry'], cfg)
    if not cfg.get('r2_sampling'):
        raise ValueError('R1_PRODUCTION_ROW_PLAN_MISSING')
    validate_binding(cfg['r2_sampling'])
    if value['row_plan_sha256'] != digest(cfg['r2_sampling']):
        raise ValueError('R1_ROW_PLAN_BINDING_DIFFERS')
    host = load(pinned(value['host_receipt'])) if value.get('host_receipt') else {}
    review = load(pinned(value['review'])) if value.get('review') else {}
    if (host.get('status') != 'PASS' or host.get('config_identity') != identity(cfg)
            or set(host.get('assertions', {})) != set(ASSERTIONS)
            or not all(host['assertions'].values()) or host.get('loader_audit', {}).get('complete') is not True):
        raise ValueError('R1_HOST_ADMISSION_MISSING')
    from student_pilot.routing_requirements import require
    from fractions import Fraction
    card=load(pinned(cfg['r2_sampling']['card']))
    mix={'cells':[dict(c,numerator=Fraction(str(c['rows_per_step'])).numerator,
                      denominator=Fraction(str(c['rows_per_step'])).denominator) for c in card['cells']]}
    from student_pilot.r1_coverage import deferred
    if not deferred(cfg):
        require(mix,host['loader_audit'].get('routing_training_counts'))
    if review.get('verdict') != 'PASS' or review.get('config_identity') != identity(cfg):
        raise ValueError('INDEPENDENT_REVIEW_PENDING')
    return start(cfg)


def begin_host(cfg, root, request, *, job_tmp_token=None):
    """Establish freshness and confinement before staging any job inputs."""
    from student_pilot.carrier_c1_run import identity
    root = Path(root).resolve()
    job_tmp = fresh_tmp(root, request, job_tmp_token)
    if root.exists() and any(root.iterdir()):
        raise ValueError('R1_HOST_ROOT_NOT_EMPTY')
    temporary_paths(cfg, job_tmp)
    temporary_paths(request, job_tmp)
    if job_tmp_token is None:
        job_tmp.mkdir(mode=0o700, parents=False, exist_ok=False)
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    root.chmod(0o700)
    result = dict(status='FAIL', config_identity=identity(cfg), assertions={k:False for k in ASSERTIONS},
                  missing=[], loader_audit={'complete':False})
    result['assertions']['empty_root'] = True
    result['assertions']['job_tmp'] = True
    return root, job_tmp, result


@contextmanager
def host_environment(job_tmp):
    """Confine caches and private directories, restoring the caller on refusal."""
    environment = ('TMPDIR', 'XDG_CACHE_HOME', 'HF_HOME', 'TRITON_CACHE_DIR', 'TORCH_HOME')
    saved = {name: os.environ.get(name) for name in environment}
    saved_tempdir = tempfile.tempdir
    saved_cwd = Path.cwd()
    for name in environment:
        os.environ[name] = str(job_tmp if name == 'TMPDIR' else job_tmp/name.lower())
    tempfile.tempdir = str(job_tmp)
    os.chdir(job_tmp)
    previous_umask = os.umask(0o077)
    try:
        yield
    finally:
        os.umask(previous_umask)
        tempfile.tempdir = saved_tempdir
        os.chdir(saved_cwd)
        for name, value in saved.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def check_host_runtime(cfg, request, result):
    from student_pilot.checkpoint_space import plan
    from student_pilot.carrier_c1_sweep import recipe_for
    expected = plan(recipe_for(cfg), retained_archive_copies=1)
    result['assertions']['disk_plan'] = cfg.get('checkpoint_disk_guard') == expected
    if not result['assertions']['disk_plan']:
        raise ValueError('R1_DISK_PLAN_DIFFERS')
    binaries = {}
    for name in request['binaries']:
        binary = shutil.which(name)
        if not binary:
            raise ValueError('R1_BINARY_MISSING:'+name)
        binaries[name] = file_pin(Path(binary).resolve())
    result['binaries'] = binaries
    result['assertions']['runtime_binaries'] = bool(binaries)


def verify_host_staging(entries, root):
    """Recheck native staging output with its hash and inventory checks."""
    from launch_r2.staging import checked
    root = Path(root).resolve()
    archives = set()
    for name, item in sorted(entries.items()):
        try:
            target = root/name
            if not name.startswith('u/') or '..' in Path(name).parts or root not in target.resolve().parents:
                raise ValueError('Staging target escaped the input root')
            if 'archive' in item or 'directory' in item:
                source = item.get('archive', item.get('directory'))
                key = source.get('sha256') or source['inventory_sha256']
                if not isinstance(key, str) or len(key) != 64 or any(c not in '0123456789abcdef' for c in key):
                    raise ValueError('Invalid archive identity')
                extracted = root/'x'/key
                if key not in archives:
                    if source.get('sha256'):
                        checked(root/'a'/key, source['sha256'])
                    elif not source.get('inventory'):
                        raise ValueError('Archive has no authenticated inventory')
                    for member, expected in source.get('inventory', {}).items():
                        if Path(member).is_absolute() or '..' in Path(member).parts:
                            raise ValueError('Staging inventory escaped its archive')
                        checked(extracted/member, expected)
                    archives.add(key)
                member = Path(item.get('member', ''))
                if member.is_absolute() or '..' in member.parts:
                    raise ValueError('Staging member escaped its archive')
                origin = extracted/member
                if item.get('directory'):
                    if not target.is_dir() or target.resolve() != origin.resolve():
                        raise ValueError('Staging directory differs from its archive')
                else:
                    checked(origin, item['sha256'])
                    checked(target, item['sha256'])
            else:
                checked(target, item['sha256'])
        except (ValueError, KeyError, TypeError, OSError) as error:
            raise ValueError('R1_HOST_STAGING_DIFFERS:'+name+':'+str(error)) from error


def stage_host(cfg, root, request, job_tmp, *, stage=None, result=None):
    """Stage authenticated inputs and retain the native routing composition."""
    # The source staging closure must be supplied and checked before any import of native preparation.
    if not request.get('staging') or not request.get('routing_selection'):
        raise ValueError('R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING')
    from launch_r2.staging import stage_inputs, validate_plan
    staging = load(pinned(request['staging']))
    temporary_paths(staging, job_tmp)
    validate_plan(cfg, staging['entries'])
    (stage_inputs if stage is None else stage)(staging['entries'], root)
    if stage is None:
        verify_host_staging(staging['entries'], root)
    if result is not None:
        result['stager'] = 'native' if stage is None else 'hook'
        result['staging_plan_sha256'] = request['staging']['sha256']
    def localize(value):
        if isinstance(value, dict):
            return {k:localize(v) for k,v in value.items()}
        if isinstance(value, list):
            return [localize(v) for v in value]
        if isinstance(value, str) and value.startswith('u/'):
            return str(root/value)
        return value
    staged_cfg = localize(cfg)
    from student_pilot.r1_coverage import routing_request
    minimal = routing_request(staged_cfg, localize(request))
    if not request.get('routing_base') or not minimal and not request.get('routing_inputs'):
        raise ValueError('R1_ROUTING_COMPOSITION_INPUTS_MISSING')
    if result is not None:
        original = staged_cfg['streams']['routing']
        substituted = localize(request['routing_base'])
        changes = dict(routing=dict(original=original, substituted=substituted,
            original_sha256=original['sha256'], substituted_sha256=substituted['sha256']))
        if not minimal:
            original = staged_cfg['r1_training'].get('routing_inputs')
            substituted = localize(request['routing_inputs'])
            changes['routing_inputs'] = dict(original=original, substituted=substituted,
                original_sha256=digest(original), substituted_sha256=digest(substituted))
        result['routing_substitution'] = changes
        result['routing_substituted'] = any(v['original'] != v['substituted'] for v in changes.values())
    staged_cfg['streams']['routing'] = localize(request['routing_base'])
    if not minimal:
        staged_cfg['r1_training']['routing_inputs'] = localize(request['routing_inputs'])
    temporary_paths(staged_cfg, job_tmp)
    return staged_cfg


def check_host_scene(cfg, result, *, record=False):
    from student_pilot.scene_division_gate import check_bound
    result['scene_division'] = check_bound(cfg)
    if record:
        result['scene_division_inputs'] = dict(division=cfg['scene_division'],
            **{name:cfg['streams'][name] for name in ('vqa', 'routing')})
    result['assertions']['scene_division'] = True


def check_host_selection(cfg, root, request, result, *, record=False):
    from student_pilot.s1_routing import build
    from student_pilot.mdg_parent import model_pin
    point = load(pinned(cfg['streams']['pointing']))
    regenerated = build(cfg, root/'selection', point['division'], model_pin(cfg))
    selection = load(pinned(request['routing_selection']))
    result['assertions']['routing_selection'] = digest(regenerated) == selection['regenerated_sha256']
    if record:
        result['routing_selection'] = request['routing_selection']
        result['regenerated_sha256'] = digest(regenerated)
    if not result['assertions']['routing_selection']:
        raise ValueError('R1_ROUTING_SELECTION_DIFFERS')


def finish_host(cfg, root, result, loader_audit, *, named_refusals=False):
    """Certify the configuration read by the final loader audit."""
    from student_pilot.carrier_c1_run import identity
    result['loader_audit'] = loader_audit
    result['config_identity'] = identity(cfg)
    result['assertions']['directory_modes'] = all(p.stat().st_mode & 0o777 == 0o700
        for p in [root, *[p for p in root.rglob('*') if p.is_dir()]])
    if named_refusals:
        for name in ASSERTIONS:
            if result['assertions'][name] is not True:
                raise ValueError('R1_HOST_ASSERTION_FALSE:'+name)
    if not all(result['assertions'].values()) or not result['loader_audit']['complete']:
        raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
    result['status'] = 'PASS'
    return result


def frame_host(cfg, root, request, *, job_tmp_token=None):
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
