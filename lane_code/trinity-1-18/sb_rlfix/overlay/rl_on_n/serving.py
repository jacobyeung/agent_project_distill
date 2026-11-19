"""Require the claimed-arm reader binding; never silently use own-head MDG.

The task requires the deployed evaluator's backend, not a new selector or a
new geometry adapter. Its table and adapter are production inputs. Neither
is supplied in sb_rlkit. Missing bindings refuse before model allocation.
"""
import importlib.util
from . import provenance as P

POSE_SOURCE='tower'


def load_binding(settings):
    settings=settings or {}
    for name in ('serving_table','evaluator_adapter'):
        if not settings.get(name):
            raise ValueError('MISSING grounding.'+name+' {path,sha256} binding for the claimed serving arm')
        P.checked(settings[name])
    # The adapter must come from the deployed evaluator and consume its real
    # table. No table schema, scene mapping, or backend is fabricated here.
    spec=importlib.util.spec_from_file_location('rl_deployed_serving_adapter',settings['evaluator_adapter']['path'])
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module,'validate_claimed_arm') or not hasattr(module,'build_backend'):
        raise ValueError('Deployed evaluator adapter requires validate_claimed_arm and build_backend')
    module.validate_claimed_arm(settings['serving_table'],pose_source=POSE_SOURCE,
                                camera='frozen_g3t',lifting='frozen_g3t',
                                grounding='sam3_selector',scale='fixed_math',gap='fixed_math')
    return module


def build_backend(model,row,batch,artifact_pin,audit_dir,settings):
    module=load_binding(settings)
    backend=module.build_backend(model=model,row=row,batch=batch,artifact_pin=artifact_pin,
                                 audit_dir=audit_dir,settings=settings)
    if backend.mask_source!='svp_sam3':
        raise ValueError('Claimed arm requires SAM 3 with its deployed selector; MDG is diagnostic only')
    return backend
