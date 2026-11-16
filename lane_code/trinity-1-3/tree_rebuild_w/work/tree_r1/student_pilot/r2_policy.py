"""Hash-bound component evidence and bank reads; caller labels confer no eligibility."""
import hashlib
import inspect
import json
from pathlib import Path
import re
from .p3_provenance import digest, load, pinned, sha256
from .r2_portable import bound

SCOPE = ('VSI-Bench', 'VSTI', 'ReVSI')
LINEAGE = ('init_m544', 'heads_pose', 'heads_depth', 'heads_frame_embeddings', 'depth_init_vc')
CHOICES = ('grounding_selector_deployed', 'box_policy', 'room_policy', 'alias_table', 'depth_cut')
EXTERNAL = ('geometry_tower', 'segmenter')
NEW = ('data_rows_r2', 'heads_gf1_connector')
COMPONENTS = (*LINEAGE, *CHOICES, *EXTERNAL, *NEW)


def slots():
    result = {}
    for name in COMPONENTS:
        cls = 'lineage' if name in LINEAGE else 'program_choice' if name in CHOICES else 'external_frozen' if name in EXTERNAL else 'new_training'
        result[name] = dict(component=name, component_class=cls,
            phase='native_evaluation' if name in CHOICES else 'both',
            expected_schema='r2-component-evidence-v1', record=None,
            status='overlap_outside_claim_scope' if name in LINEAGE else 'exempt_disclosed' if name in EXTERNAL else 'MISSING')
    return result


def record(slot, root=None):
    if not slot.get('record'):
        raise ValueError('Missing component evidence: '+slot['component'])
    data = load(bound(slot['record'], root))
    if (data.get('schema') != slot['expected_schema'] or data.get('component') != slot['component']
            or data.get('component_class') != slot['component_class']
            or data.get('phase') != slot['phase'] or not data.get('inputs')):
        raise ValueError('Component record schema, class, phase or inputs differ')
    for pin in data['inputs']:
        bound(pin, root)
    if data.get('verdict') not in ('PROVEN_CLEAN', 'OVERLAP_FOUND', 'EXEMPT_FROZEN'):
        raise ValueError('Unknown component evidence is not a pass')
    if slot['component_class'] == 'external_frozen':
        if data['verdict'] != 'EXEMPT_FROZEN' or data.get('frozen') is not True:
            raise ValueError('External exemption requires frozen pretrained weights')
    elif slot['component_class'] == 'lineage':
        if not isinstance(data.get('overlaps'), list) or not isinstance(data.get('checked_banks'), list):
            raise ValueError('Lineage needs explicit overlap and checked-bank evidence')
        if not set(SCOPE) <= set(data['checked_banks']):
            raise ValueError('Unknown claim-scope overlap')
        if any(x['bank'] in SCOPE and str(x.get('venue')) != '381879' for x in data['overlaps']):
            raise ValueError('Overlap inside claim scope')
    elif slot['component_class'] == 'new_training':
        if data['verdict'] != 'PROVEN_CLEAN' or data.get('exclusions_complete') is not True:
            raise ValueError('New training requires complete clean scene evidence')
    return data


def components(registry_pin, phase, root=None):
    registry = load(bound(registry_pin, root))
    expected = slots()
    if set(registry) != set(expected) or phase not in ('training', 'native_evaluation'):
        raise ValueError('Component registry or phase differs')
    result = {}
    for name, spec in expected.items():
        entry = registry[name]
        if any(entry.get(k) != spec[k] for k in ('component', 'component_class', 'phase', 'expected_schema')):
            raise ValueError('Component slot was reclassified')
        if phase == 'training' and name in CHOICES:
            continue
        result[name] = record(entry, root)
    return result


def reader_hash():
    return digest(dict(source=sha256(Path(__file__)), entry='read_bank'))


def freeze_check(pin, prereg_pin, root=None):
    prereg = pinned(prereg_pin)
    if not pin:
        raise ValueError('Native evaluation requires the single dated freeze file')
    frozen = load(pinned(pin))
    required = {'C1', 'C2', 'C3', 'C4', 'D1', 'D2'}
    if (frozen.get('schema') != 'r2-dated-freeze-v1'
            or not re.fullmatch(r'\d{4}-\d{2}-\d{2}', frozen.get('date',''))
            or frozen['date'] < '2026-11-15' or frozen.get('prereg_sha256') != sha256(prereg)
            or not required <= set(frozen.get('decisions', {}))
            or not frozen.get('evidence')):
        raise ValueError('Incomplete or foreign dated freeze')
    for value in frozen['evidence']:
        bound(value, root)
    return frozen


def read_bank(bank_pin, catalog_pin=None, *, registry_pin=None, prereg_pin=None, freeze_pin=None,
              choices=(), camera_routing=False, declared_label=None, kit_root=None):
    """Own the actual JSON bank read; catalog binds exact item content and reader code."""
    if kit_root is None:
        raise ValueError('Bank gateway requires a sealed kit configuration')
    root = Path(kit_root).resolve()
    from launch_r2.build import verify
    verify(root)
    launch = load(root/'k/launch.json')
    cfg = load(bound(dict(path=launch['config']['file'], sha256=launch['config']['sha256']), root))
    policy = cfg.get('r2_evaluation') or {}
    if catalog_pin is not None and catalog_pin != policy.get('catalog'):
        raise ValueError('Caller catalog differs from sealed membership')
    catalog = load(bound(policy['catalog'], root))
    if bank_pin['sha256'] not in catalog.get('files', {}):
        raise ValueError('Actual bank file is absent from sealed membership')
    choices = tuple(policy.get('choices', ()))
    camera_routing = policy.get('camera_routing') is True
    registry_pin = cfg['r2_build2']['registry']
    prereg_pin = policy.get('prereg')
    freeze_pin = policy.get('freeze')
    items = load(pinned(bank_pin))
    if (catalog.get('schema') != 'r2-bank-catalog-v1' or catalog.get('reader_sha256') != reader_hash()
            or not isinstance(items, list) or not items):
        raise ValueError('Unknown bank reader or empty bank')
    identities, banks, venues = set(), set(), set()
    for item in items:
        key = digest(item)
        facts = catalog['items'].get(key)
        if (not facts or key in identities or not facts.get('banks')
                or key not in catalog['files'][bank_pin['sha256']]['items']
                or facts['banks'] != catalog['files'][bank_pin['sha256']]['banks']):
            raise ValueError('Unknown or repeated item identity')
        identities.add(key)
        banks.update(facts['banks'])
        venues.add(str(facts.get('venue')))
    if not banks <= {*SCOPE, 'dev-S1'}:
        raise ValueError('Actual bank is outside lineage claim scope')
    if set(choices) - set(CHOICES):
        raise ValueError('Unknown program choice')
    if 'grounding_selector_deployed' in choices and banks & {'ReVSI','VSTI'}:
        raise ValueError('Deployed selector is fitted on this bank')
    components(registry_pin, 'training', root)
    camera_exception = camera_routing and banks == {'VSTI'} and not choices and all(
        i.get('question_type') in ('camera_displacement', 'camera_movement_direction') for i in items)
    if banks & set(SCOPE) and not camera_exception:
        freeze_check(dict(path=str(bound(freeze_pin,root)),sha256=freeze_pin['sha256']) if freeze_pin else None,
                     dict(path=str(bound(prereg_pin,root)),sha256=prereg_pin['sha256']), root=root)
        registry = load(bound(registry_pin, root))
        for name in choices:
            record(registry[name], root)
    from .r2_units import metric_units
    return items, dict(metric_units=metric_units(items), reader_sha256=reader_hash(), item_set_sha256=digest(sorted(identities)),
        banks=sorted(banks), label='paired-comparison only' if 'dev-S1' in banks else 'claim_scope',
        required_scores=['all', 'without_venue_381879'], venue_present='381879' in venues,
        qualification_probe='seen-in-training', open_lineage_question='2026-11-13')


def seal_catalog(bank_files):
    """Builder-only membership from the actual pinned files; no runtime labels."""
    result = dict(schema='r2-bank-catalog-v1', reader_sha256=reader_hash(), files={}, items={})
    for bank, pin in bank_files.items():
        values = load(pinned(pin))
        keys = []
        for item in values:
            key = digest(item)
            if key in result['items']:
                raise ValueError('Repeated item in sealed bank files')
            result['items'][key] = dict(banks=[bank], venue=item.get('venue'))
            keys.append(key)
        result['files'][pin['sha256']] = dict(banks=[bank], items=keys)
    return result


def require_scores(receipt, scores):
    if set(scores) != set(receipt['required_scores']):
        raise ValueError('Both venue-inclusive and venue-excluded scores are required')
    for result in scores.values():
        for kind, units in receipt.get('metric_units', {}).items():
            breakdown = result.get('by_asked_unit', {}).get(kind, {}) if isinstance(result, dict) else {}
            if list(breakdown) != units:
                raise ValueError('Metric scores require every asked unit, metres first')
    return scores


def preparation(binding, root):
    """Resolve portable pins only inside the verified kit, then apply training gates."""
    from .r2_mix import preflight
    components(binding['registry'], 'training', root)
    if not binding.get('counts'):
        raise ValueError('Post-filter population counts are missing')
    return preflight(binding['mix'], binding['counts'], root=root,
                     source_presence=binding.get('source_presence'))


def legacy_reader_guard(cfg, artifact_pin):
    """Unsupported legacy readers cannot consume this lineage before bank admission."""
    ancestor = (cfg.get('init_artifact') or {}).get('artifact', {}).get('sha256')
    if (any(key in cfg for key in ('r2', 'r2_identity', 'r2_build2', 'geometry_connector'))
           ):
        raise ValueError('Legacy reader has no authenticated R2 bank adapter; use the bound bank gateway')


def unsupported_entry(entry):
    """This derived tree cannot authenticate legacy item formats. Fail before IO.

    The only admitted bank reader is read_bank: it binds actual item digests and
    the reader implementation. Renaming a bank or omitting lineage labels cannot
    enable a legacy entrypoint in this tree.
    """
    raise ValueError('Legacy reader has no authenticated R2 bank adapter: '+entry)
