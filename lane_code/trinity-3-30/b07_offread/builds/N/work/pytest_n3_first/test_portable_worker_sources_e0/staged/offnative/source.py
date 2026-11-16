"""Bind dense reconstruction before selecting the model's 32 anchors."""
from pathlib import Path
import re
from .io import load, sha
from .paths import ROOT
CLIP_LABEL = 'Diagnostic only: G3T on 32 viewed frames; no benchmark result'


def validate_mapping(record, *, production=False):
    if record.get('schema') != 'revsi-dense64-v1' or not record.get('registration') or not record.get('clips'):
        raise ValueError('invalid registered dense mapping')
    for clip, row in record['clips'].items():
        path = Path(row.get('path', ''))
        if not row.get('path') or path.is_absolute() or '..' in path.parts:
            raise ValueError('mapping lacks safe relative original path: '+clip)
        anchors, dense, slots = (row.get(k, []) for k in ('anchor_indices', 'dense_indices', 'anchor_slots'))
        if (len(anchors) != 32 or len(dense) != 64 or len(slots) != 32
                or any(type(i) != int or i < 0 for i in anchors+dense+slots)
                or dense != sorted(dense) or slots != sorted(set(slots))
                or any(i >= 64 for i in slots) or [dense[i] for i in slots] != anchors
                or row.get('dense_decode_indices') != list(range(64))):
            raise ValueError('mapping anchor correspondence differs: '+clip)
        for name in ('clip_sha256', 'original_sha256'):
            if not re.fullmatch('[0-9a-f]{64}', row.get(name) or '') and production:
                raise ValueError('mapping hash pending: '+clip+' '+name)
    return record


def bind_source(source='original', *, freeze=None, mapping=None, production=False,
                reader='harness', benchmark='revsi999t32'):
    if source == 'clip32' and production:
        raise ValueError('clip32 is diagnostic only; proof and production are refused')
    if reader == 'e2e':
        return {'source':'inside_generate', 'label':'Towers run inside generate on its own frames.'}
    if source not in ('clip32','original'):
        raise ValueError('missing input: --g3t-source {clip32,original}')
    if production and (freeze or {}).get('g3t_source') != source:
        raise ValueError('missing input: P8 freeze_values.g3t_source must name '+source)
    value = {'source':source, 'count':32 if source=='clip32' else 64,
             'label':CLIP_LABEL if source=='clip32' else 'Dense G3T reconstruction on 64 frames, then anchor selection'}
    if source == 'original' and benchmark == 'vsibench5130':
        return dict(value, media='same_full_video', anchor_alignment='registered_floor_uniform_union')
    if source == 'original':
        mapping = Path(mapping or ROOT/'out/REVSI_DENSE_MAPPING.json')
        if not mapping.is_file():
            raise ValueError('missing input: registered dense mapping')
        record = validate_mapping(load(mapping), production=production)
        if production and len(record['clips']) != 302:
            raise ValueError('mapping must cover all 302 videos')
        value.update(mapping_sha256=sha(mapping), media='official_64_frame_clip',
                     hashes_pending=record.get('hashes_pending', True))
    return value
