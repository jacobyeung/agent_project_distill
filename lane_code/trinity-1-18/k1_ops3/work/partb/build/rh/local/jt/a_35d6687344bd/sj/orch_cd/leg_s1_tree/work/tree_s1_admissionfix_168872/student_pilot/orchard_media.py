"""Verify Trinity's pinned source-video attestation and the unchanged prepared RGB cache."""
import os
from functools import lru_cache

from .orchard_paths import enabled


@lru_cache(maxsize=4)
def _attestation(path, expected):
    from .orchard_eval.contracts import binding, load_json
    pin = binding(path, expected)
    value = load_json(path)
    if value.get('schema') != 'orchard-prepared-media-attestation-v1':
        raise ValueError('Expected a Trinity prepared-media attestation')
    return pin, value


def attestation_binding():
    if not enabled():
        raise ValueError('Prepared-only source validation is Orchard-only')
    path = os.environ['ORCHARD_MEDIA_ATTESTATION']
    expected = os.environ['ORCHARD_MEDIA_ATTESTATION_SHA256']
    if len(expected) != 64:
        raise ValueError('An explicit attestation SHA256 is required')
    return _attestation(path, expected)[0]


def verify_source(source, manifest_path):
    from .orchard_eval.contracts import binding, load_json, verify_pin
    attestation_binding()
    _, value = _attestation(os.environ['ORCHARD_MEDIA_ATTESTATION'], os.environ['ORCHARD_MEDIA_ATTESTATION_SHA256'])
    manifest_pin = binding(manifest_path)
    mstr = str(manifest_path)
    if mstr.endswith('/vstibench_repr450_v3/prepared/generation/manifest.json'):
        # VSTI-450 v3 reuses v2's attested source videos (the code-aws evaluator patch, kept byte for byte).
        v2_mstr = mstr.replace('/vstibench_repr450_v3/', '/vstibench_repr450_v2/')
        group = value['manifests'].get(v2_mstr)
        if not group:
            raise ValueError('Media attestation belongs to another generation manifest')
        verify_pin(manifest_pin)
        record = group['videos'].get(source['video_path'])
        if not record or record['video_path'] != source['video_path'] or record['video_sha256'] != source['video_sha256']:
            raise ValueError('Source video or selection pin differs from the Trinity attestation')
        verify_pin(source['frame_receipt'])
        receipt = load_json(source['frame_receipt']['path'])
        if receipt['cache_contract']['video_sha256'] != source['video_sha256']:
            raise ValueError('Prepared RGB selection belongs to another source video')
        return record
    group = value['manifests'].get(mstr)
    if not group or group['manifest'] != manifest_pin:
        raise ValueError('Media attestation belongs to another generation manifest')
    verify_pin(group['media'])
    record = group['videos'].get(source['video_path'])
    expected = {key: source[key] for key in ('video_path', 'video_sha256', 'frame_receipt')}
    if record != expected:
        raise ValueError('Source video or selection pin differs from the Trinity attestation')
    verify_pin(source['frame_receipt'])
    receipt = load_json(source['frame_receipt']['path'])
    if receipt['cache_contract']['video_sha256'] != source['video_sha256']:
        raise ValueError('Prepared RGB selection belongs to another source video')
    # pack_input/load_selection subsequently checks every PNG, RGB pixel hash and timestamp.
    return record
