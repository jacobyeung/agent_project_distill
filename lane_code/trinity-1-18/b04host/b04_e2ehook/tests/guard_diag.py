"""Lane diagnostics (never imported by the reader): what the removed gravity checks would say on a geometry."""
import dataclasses

import numpy as np

UP_PLANE_MIN = .3  # C8r's reviewed check, reproduced for the report only
SEALED_MESSAGE = 'reference_camera_up_opposes_gravity'


def sealed_refuses(geometry):
    from student_pilot import geometry_profiles as GP
    c = geometry.contract
    try:
        GP.GeometryContract(**{f.name: getattr(c, f.name) for f in dataclasses.fields(GP.GeometryContract)}).validate()
    except GP.GeometryError as error:
        if str(error) == SEALED_MESSAGE:
            return True
        raise
    return False


def reviewed_refuses(geometry):
    R = np.asarray(geometry.C, float)[:, :3, :3]
    plane = np.linalg.norm(R[:, 2, :2], axis=1)
    margin = -R[:, 2, 1]
    if plane[0] >= UP_PLANE_MIN:
        return bool(margin[0] <= 0)
    usable = plane >= UP_PLANE_MIN
    return bool(usable.any() and np.median(margin[usable] / plane[usable]) <= 0)


def verdicts(geometry):
    return dict(sealed_guard_refuses=sealed_refuses(geometry), reviewed_guard_refuses=reviewed_refuses(geometry))


def without_sealed_check(fn):
    """Replay only: the old runtime's PolicyAudit session rebuilds recorded geometries through the base
    GeometryContract (ground_replay.restore_geometry); run `fn` with the reader's contract validate there."""
    def call(*args, **kwargs):
        from student_pilot import geometry_profiles as GP
        from e2e_reader.geometry import reader_contract
        original = GP.GeometryContract.validate
        GP.GeometryContract.validate = reader_contract(GP).validate
        try:
            return fn(*args, **kwargs)
        finally:
            GP.GeometryContract.validate = original
    return call
