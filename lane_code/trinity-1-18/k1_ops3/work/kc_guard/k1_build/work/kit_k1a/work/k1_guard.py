"""Reviewed gravity installation and bound K1 capture dispositions."""
import json
import shutil
from pathlib import Path

import bindings as B
import k1_phases as F
import gravity_guard as GG
from student_pilot import geometry_profiles

CODE = 'reference_camera_up_opposes_gravity'
_recorder = None
_convert = F.convert


def install():
    global _recorder
    if _recorder is None:
        recorder = GG.Recorder()
        GG.install(geometry_profiles, recorder)
        _recorder = recorder


def capture(c):
    return GG.capture('K1', c['canonical'])


def verdict(c):
    sealed, reviewed = _recorder.records[('K1', c['canonical'])]
    return dict(sealed_refused=sealed, reviewed_refused=reviewed)


def write_report(out):
    # Reports use verdicts validated during conversion or cache reload.
    (Path(out) / 'GUARD_REPORT.json').write_text(json.dumps(GG.report(), indent=2) + '\n')


def check_receipt(c, dest, receipt):
    refusal = receipt.get('geometry_refusal')
    votes = receipt.get('gravity_verdict', {})
    if (receipt.get('gravity_guard') != GG.identity()
            or set(votes) != {'sealed_refused', 'reviewed_refused'}
            or any(type(v) is not bool for v in votes.values())
            or receipt.get('sources') != B.source_identity()
            or receipt.get('phase') != 'unselected_cache_no_responses'):
        raise ValueError('Cache guard/source binding differs')
    names = {'candidates.json', 'parity_raw.jsonl'}
    if refusal:
        if (refusal != dict(code=CODE, message=CODE) or receipt.get('geometry') is not None
                or not votes['reviewed_refused'] or (dest / 'geometry.npz').exists()):
            raise ValueError('Cache geometry refusal differs')
        names.add('REFUSED_GEOMETRY.npz')
    else:
        if votes['reviewed_refused'] or not receipt.get('geometry'):
            raise ValueError('Cache geometry verdict differs')
        names.add('geometry.npz')
    if set(receipt['files']) != names or any(
            Path(pin['path']).resolve() != (dest / name).resolve()
            for name, pin in receipt['files'].items()):
        raise ValueError('Cache file binding differs')


def convert(c, boundary, dest, tower_root, own_root, progress):
    install()
    with capture(c):
        try:
            result = _convert(c, boundary, dest, tower_root, own_root, progress)
        except geometry_profiles.GeometryError as error:
            if str(error) != CODE or not _recorder.records.get(('K1', c['canonical']), (False, False))[1]:
                raise
            # The sealed converter writes before validating. Preserve that evidence
            # under a distinct name; no geometry.npz is admitted for this capture.
            names = ['candidates.json', 'parity_raw.jsonl', 'REFUSED_GEOMETRY.npz']
            (dest / 'geometry.npz').rename(dest / 'REFUSED_GEOMETRY.npz')
            source = Path(tower_root) / B.digest(c['canonical'])[:16]
            for name in ('candidates.json', 'parity_raw.jsonl'):
                shutil.copyfile(source / name, dest / name)
            result = dict(capture_sha256=B.digest(c), checkpoint=boundary.checkpoint,
                          synthetic=boundary.synthetic, sources=B.source_identity(), geometry=None,
                          geometry_refusal=dict(code=CODE, message=str(error)),
                          files={name: B.pin(dest / name) for name in names},
                          phase='unselected_cache_no_responses')
            progress('geometry_refused')
    result.update(gravity_guard=GG.identity(), gravity_verdict=verdict(c))
    # Replace the converter's provisional receipt only after attaching the guard.
    pending = dest / 'GUARDED_COMPLETE.json'
    B.write(pending, result)
    pending.replace(dest / 'CACHE_COMPLETE.json')
    return result


def run(m, out, *args, **kwargs):
    install()
    original = F.convert
    F.convert = convert
    try:
        return F.run(m, out, *args, **kwargs)
    finally:
        F.convert = original
        if (Path(out) / 'BINDING.json').exists():
            write_report(out)
