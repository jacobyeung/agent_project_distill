"""Component evidence at training and claim boundaries; never inference policy."""
from .p3_provenance import load, pinned, digest
from pathlib import Path

RUN = '6ed2c7aa'
DEV = {'dev-S1', 'R0-dev', 'VSTI-dev', 'facing-twins'}
NOTICE = 'component evidence DEFERRED: nine records lost with trinity-2-18, rebuild in progress; no official read until they pass'


def deferred(cfg, phase='training', root=None):
    """Only a persisted P export and the pinned N card authorize deferral."""
    from .r1_training import PARENT
    from .r1_persisted import verify, scope, init_policy
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
                     value.get('persisted_files', {}), proof_mode=value.get('proof_mode'),init_policy=init_policy(value))
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
    if value.get('not_present_slots'):
        from .r1_absence import evidence
        with scope(closure['paths']):
            result.update(evidence(cfg,artifact))
    return result


def guard(artifact, banks, boundary):
    """Authenticated bank membership controls dev access; caller labels do not."""
    from .r2_policy import SCOPE
    if not set(banks) <= DEV | set(SCOPE):
        raise ValueError('COMPONENT_BANK_SCOPE_UNKNOWN:'+boundary)
    if set(banks) & set(SCOPE):
        if (artifact.get('r1_progress') or artifact.get('component_preparation')
                or artifact.get('component_evidence_sha256')) and not artifact.get('component_evidence'):
            raise ValueError('COMPONENT_EVIDENCE_MISSING:init_m544:'+boundary)
        for name, entry in (artifact.get('component_evidence') or {}).items():
            if entry.get('status') == 'DEFERRED':
                raise ValueError('COMPONENT_EVIDENCE_DEFERRED:'+name+':'+boundary)
        status = artifact.get('component_evidence')
        if status:
            from .r2_policy import LINEAGE, EXTERNAL, NEW, components
            if set(status) != set((*LINEAGE, *EXTERNAL, *NEW)):
                raise ValueError('COMPONENT_EVIDENCE_SLOTS_DIFFER:'+boundary)
            if any(v.get('status') not in ('VERIFIED','NOT_PRESENT') or not v.get('record') for v in status.values()):
                raise ValueError('COMPONENT_EVIDENCE_RECORD_REQUIRED:'+boundary)
            pin = artifact.get('component_preparation')
            if not pin:
                raise ValueError('COMPONENT_EVIDENCE_PREPARATION_REQUIRED:'+boundary)
            prep = load(pinned(pin))
            recorded = normalize(prep.get('component_evidence', {}))
            if (prep.get('schema') != 'c1-preparation-v1' or recorded != status
                    or artifact.get('component_evidence_sha256') != digest(recorded)):
                raise ValueError('COMPONENT_EVIDENCE_PREPARATION_MISMATCH:'+boundary)
            from .r1_absence import verify as verify_absence, evidence as absence_evidence, SLOT_CODES
            absent={k:v for k,v in status.items() if v.get('status')=='NOT_PRESENT'}
            for name,entry in absent.items():verify_absence(entry,prep,name)
            if absent:
                current={**prep,**next(iter(absent.values()))['record']['configuration']}
                current['r1_training']={**prep['r1_training'],'not_present_slots':list(SLOT_CODES)}
                absence_evidence(current,artifact)
                from .r2_policy import record, CHOICES, slots
                registry=load(pinned(prep['r1_training']['registry']))
                expected=slots()
                if set(registry)!=set(expected) or any(
                        any(registry[name].get(k)!=spec[k] for k in ('component','component_class','phase','expected_schema'))
                        for name,spec in expected.items()):
                    raise ValueError('COMPONENT_EVIDENCE_SLOTS_DIFFER:'+boundary)
                records={name:(absent[name] if name in absent else record(slot))
                         for name,slot in registry.items() if name not in CHOICES}
            else:records = components(prep['r1_training']['registry'], 'training')
            if normalize(records) != status:
                raise ValueError('COMPONENT_EVIDENCE_RECORD_MISMATCH:'+boundary)


def normalize(records):
    return {k: v if v.get('status') in ('DEFERRED', 'VERIFIED','NOT_PRESENT') else dict(status='VERIFIED', record=v)
            for k, v in records.items()}


def artifact_binding(cfg, status):
    """Carry the pinned preparation that actually recorded these statuses."""
    if not status:
        return {}
    if 'r1_training' in cfg:
        pin = cfg.get('preparation')
    else:
        from .r1_handover import metadata_load
        parent = metadata_load(cfg['init_artifact']['artifact'], {})
        pin = parent.get('component_preparation')
    if not pin or normalize(load(pinned(pin)).get('component_evidence', {})) != status:
        raise ValueError('COMPONENT_EVIDENCE_PREPARATION_MISMATCH:export')
    return dict(component_preparation=pin, component_evidence_sha256=digest(status))


def artifact_status(cfg):
    """Publish status on every N export and preserve inherited deferred slots."""
    from .r1_handover import metadata_load
    spec = (cfg.get('init_artifact') or {}).get('artifact')
    inherited = metadata_load(spec, (cfg.get('r1_training') or {}).get('persisted_files', {})).get('component_evidence', {}) if spec else {}
    if 'r1_training' in cfg:
        from .r1_training import training_components
        records = training_components(cfg['r1_training']['registry'], cfg)
        inherited = {**normalize(records), **inherited}
        inherited.update({k:v for k,v in records.items() if v.get('status')=='NOT_PRESENT'})
    if cfg.get('r2_evaluation'):
        guard(dict(component_evidence=inherited, component_preparation=cfg.get('preparation'),
                   component_evidence_sha256=digest(inherited)),
              ['VSI-Bench', 'VSTI', 'ReVSI'], 'official-export')
    return inherited
