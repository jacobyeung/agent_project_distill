"""The CPU host proof gates R1's native preparation and trainer."""
import os
from pathlib import Path
import shutil
from student_pilot.p3_provenance import digest, file_pin, load, pinned, write


ASSERTIONS = ('disk_plan', 'routing_selection', 'empty_root', 'runtime_binaries', 'directory_modes', 'scene_division')


def admit(cfg):
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
    require(mix,host['loader_audit'].get('routing_training_counts'))
    if review.get('verdict') != 'PASS' or review.get('config_identity') != identity(cfg):
        raise ValueError('INDEPENDENT_REVIEW_PENDING')
    return start(cfg)


def frame_host(cfg, root, request):
    """Run the production CPU preparation from a fresh root; failures stay explicit."""
    from student_pilot.carrier_c1_run import identity
    from student_pilot.checkpoint_space import plan
    from student_pilot.carrier_c1_sweep import recipe_for
    root = Path(root).resolve()
    if root.exists() and any(root.iterdir()):
        raise ValueError('R1_HOST_ROOT_NOT_EMPTY')
    root.mkdir(parents=True, mode=0o700, exist_ok=True)
    root.chmod(0o700)
    result = dict(status='FAIL', config_identity=identity(cfg), assertions={k:False for k in ASSERTIONS},
                  missing=[], loader_audit={'complete':False})
    result['assertions']['empty_root'] = True
    previous_umask = os.umask(0o077)
    try:
        if os.environ.get('CUDA_VISIBLE_DEVICES', ''):
            raise ValueError('CPU_ONLY_REQUIRED')
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
        # The source staging closure must be supplied and checked before any import of native preparation.
        if not request.get('staging') or not request.get('routing_selection'):
            raise ValueError('R1_HOST_STAGING_AND_SELECTION_INPUTS_MISSING')
        from launch_r2.staging import stage_inputs, validate_plan
        staging = load(pinned(request['staging']))
        validate_plan(cfg, staging['entries'])
        stage_inputs(staging['entries'], root)
        def localize(value):
            if isinstance(value, dict):
                return {k:localize(v) for k,v in value.items()}
            if isinstance(value, list):
                return [localize(v) for v in value]
            if isinstance(value, str) and value.startswith('u/'):
                return str(root/value)
            return value
        staged_cfg = localize(cfg)
        from student_pilot.scene_division_gate import check_bound
        result['scene_division'] = check_bound(staged_cfg)
        result['assertions']['scene_division'] = True
        from student_pilot.s1_routing import build
        from student_pilot.mdg_parent import model_pin
        point = load(pinned(staged_cfg['streams']['pointing']))
        regenerated = build(staged_cfg, root/'selection', point['division'], model_pin(staged_cfg))
        selection = load(pinned(request['routing_selection']))
        result['assertions']['routing_selection'] = digest(regenerated) == selection['regenerated_sha256']
        if not result['assertions']['routing_selection']:
            raise ValueError('R1_ROUTING_SELECTION_DIFFERS')
        from student_pilot.s1_admission import admit as native_admit
        write(root/'c.json', staged_cfg)
        prepared = native_admit(file_pin(root/'c.json'), root/'p', [root], threads=8, prepare_only=True)
        result['preparation'] = prepared
        # This audit must come from the same production reader and final sampler indices.
        from student_pilot.r1_loader import production_audit
        result['loader_audit'] = production_audit(load(pinned(prepared['config'])), root/'audit')
        result['assertions']['directory_modes'] = all(p.stat().st_mode & 0o777 == 0o700
            for p in [root, *[p for p in root.rglob('*') if p.is_dir()]])
        if not all(result['assertions'].values()) or not result['loader_audit']['complete']:
            raise ValueError('R1_HOST_ASSERTIONS_INCOMPLETE')
        result['status'] = 'PASS'
    except (ValueError, KeyError, TypeError, OSError) as error:
        result['missing'].append(str(error))
    finally:
        os.umask(previous_umask)
    write(root/'receipt.json', result)
    return result
