"""Bind the tower's viewed-frame source without inventing dense clip frames."""
from pathlib import Path
from .io import load, sha
CLIP_LABEL = 'G3T on the 32 viewed frames, not the pre-registered dense 64'


def bind_source(source, *, freeze=None, mapping=None, production=False, reader='harness'):
    if reader == 'e2e':
        return {'source':'inside_generate', 'label':'Towers run inside generate on its own frames.'}
    if source not in ('clip32','original'):
        raise ValueError('missing input: --g3t-source {clip32,original}')
    if production and (freeze or {}).get('g3t_source') != source:
        raise ValueError('missing input: P8 freeze_values.g3t_source must name '+source)
    value = {'source':source,'count':32 if source=='clip32' else 64,
             'label':CLIP_LABEL if source=='clip32' else 'G3T on registered original-video dense 64 frames'}
    if source=='original':
        if not mapping or not Path(mapping).is_file():
            raise ValueError('missing input: registered clip-to-original mapping with anchor correspondence')
        record=load(mapping)
        if record.get('schema')!='clip-original-v1' or not record.get('registration') or not record.get('clips'):
            raise ValueError('invalid registered clip-to-original mapping')
        for clip, row in record['clips'].items():
            for name in ('clip_sha256','original_sha256'):
                import re
                if not re.fullmatch('[0-9a-f]{64}',row.get(name,'')):
                    raise ValueError('mapping lacks '+name+': '+clip)
            anchors, dense, slots = (row.get(k,[]) for k in ('anchor_indices','dense_indices','anchor_slots'))
            if (len(anchors)!=32 or len(dense)!=64 or len(slots)!=32 or
                    dense!=sorted(set(dense)) or slots!=sorted(set(slots)) or
                    any(type(i)!=int or not 0<=i<64 for i in slots) or
                    [dense[i] for i in slots]!=anchors):
                raise ValueError('mapping anchor correspondence differs: '+clip)
        value['mapping_sha256']=sha(mapping)
    return value
