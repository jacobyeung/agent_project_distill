"""Component evidence at training and claim boundaries; never inference policy."""
from .p3_provenance import load, pinned
from pathlib import Path

RUN = '6ed2c7aa'
DEV = {'dev-S1', 'R0-dev', 'VSTI-dev', 'facing-twins'}
NOTICE = 'component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass'


def deferred(cfg, phase='training', root=None):
    """Only a persisted P export and the pinned N card authorize deferral."""
    from .r1_training import PARENT
    from .r1_persisted import verify, scope
    from .r2_policy import LINEAGE, EXTERNAL, NEW
    from .r2_portable import bound
    value = cfg.get('r1_training') or {}
    if phase != 'training' or not value.get('mix') or value.get('proof_mode') not in (None, 'train', 'q'):
        return None
    card = load(bound(value['mix'], root))
    if card.get('vehicle') != 'N' or not (card.get('leg') == 'R1' or card.get('successor_of') == 'R1'):
        return None
    spec = (cfg.get('init_artifact') or {}).get('artifact') or {}
    if spec.get('sha256') == PARENT or not value.get('handover_receipt'):
        return None
    closure = verify(value['handover_receipt'], value.get('p_run', {}), spec,
                     value.get('persisted_files', {}), proof_mode=value.get('proof_mode'))
    with scope(closure['paths']):
        donor = load(pinned(value['p_run']['config']))
        artifact = load(pinned(spec))
    parent = (donor.get('init_artifact') or {}).get('artifact', {})
    if (Path(donor.get('output', '')).name != RUN or parent.get('sha256') != PARENT):
        return None
    # The authenticated donor config binds the exact step-544 artifact even when
    # P's sealed exporter predates the r2_identity field on export metadata.
    pin = value.get('component_rows')
    if not pin:
        raise ValueError('DEFERRED_COMPONENT_ROWS_RECORD_REQUIRED:data_rows_r2')
    rows = load(bound(pin, root))
    if (rows.get('schema') != 'r1-component-rows-v1' or rows.get('status') != 'DEFERRED'
            or not rows.get('proven') or not rows.get('unproven') or not rows.get('inputs')):
        raise ValueError('DEFERRED_COMPONENT_ROWS_RECORD_INVALID:data_rows_r2')
    for evidence in rows['inputs']:
        bound(evidence, root)
    result = {name:dict(status='DEFERRED', reason=NOTICE,
                       receipt_sha256=value['handover_receipt']['sha256']) for name in (*LINEAGE, *EXTERNAL, *NEW)}
    result['data_rows_r2'].update(reason='Alias-map rebuild pending; unresolved overlap is not clean evidence.', record=rows)
    result['heads_gf1_connector']['reason'] = 'N disables the fusion connector; its lost record is still owed before an official read.'
    return result


def guard(artifact, banks, boundary):
    """Authenticated bank membership controls dev access; caller labels do not."""
    from .r2_policy import SCOPE
    if not set(banks) <= DEV | set(SCOPE):
        raise ValueError('COMPONENT_BANK_SCOPE_UNKNOWN:'+boundary)
    if set(banks) & set(SCOPE):
        if artifact.get('r1_progress') and not artifact.get('component_evidence'):
            raise ValueError('COMPONENT_EVIDENCE_MISSING:init_m544:'+boundary)
        for name, entry in (artifact.get('component_evidence') or {}).items():
            if entry.get('status') == 'DEFERRED':
                raise ValueError('COMPONENT_EVIDENCE_DEFERRED:'+name+':'+boundary)


def artifact_status(cfg):
    """Publish status on every N export and preserve inherited deferred slots."""
    from .r1_handover import metadata_load
    spec = (cfg.get('init_artifact') or {}).get('artifact')
    inherited = metadata_load(spec, (cfg.get('r1_training') or {}).get('persisted_files', {})).get('component_evidence', {}) if spec else {}
    if 'r1_training' in cfg:
        from .r1_training import training_components
        records = training_components(cfg['r1_training']['registry'], cfg)
        inherited = {**{k:dict(status='VERIFIED', record=v) for k,v in records.items() if v.get('status') != 'DEFERRED'},
                **{k:v for k,v in records.items() if v.get('status') == 'DEFERRED'}, **inherited}
    if cfg.get('r2_evaluation'):
        guard(dict(component_evidence=inherited), ['VSI-Bench', 'VSTI', 'ReVSI'], 'official-export')
    return inherited
