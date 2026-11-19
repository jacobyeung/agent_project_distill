"""Pinned wording exclusion and coverage-source identities for training intake."""
import json,re,unicodedata
from .p3_provenance import load,pinned,digest

SPLIT = '2463193d00fabda5c62d07027527f57a5943dd52ee2b346a215576e55d1abf19'
PINS = {'coverage_units':'8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82',
        'coverage_distance':'15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022'}
EXTRA_PINS = {'camera_wording':'e3c72962e3fd774c7e15fa1e4aeae1b6642264bf4f3cf54b9e350b8d7bfb9707'}
CAMERA_WORDINGS = '0b6f8eb3fe99a1ccb011195778e0ecec89dce90ff13f0b6d90321c85955d6b86'

# These two catalog entries describe audit provenance, never routing composition.
AUDIT_SOURCE_NAMES = frozenset(('room', 'room_programs_excluded'))

def slice_bound(field, name, legacy=''):
    raise ValueError('R1_MINIMAL_SLICE_BOUND:'+field+':'+str(name)
                     + (':'+legacy if legacy else ''))

def deferred(cfg, request=None, *, sources=None, membership=None, card=None,
             counts=None, indices=None, read_pins=False):
    """Central MINIMAL gate. Read metadata pins only, never source rows or envelopes.

    Before staging, check inline fields. After localization, read_pins also checks
    authenticated catalogs and sampler metadata before any training reader runs.
    FULL returns immediately and retains its existing readers and refusals.
    """
    value = (cfg or {}).get('r1_training') or {}
    if 'routing_slices' not in value:
        return False
    if value['routing_slices'] != 'deferred_first_boundary':
        raise ValueError('R1_ROUTING_SLICES_INVALID')
    def catalog(raw, field):
        if not isinstance(raw, dict):
            slice_bound(field, '<invalid>')
        for name in sorted(raw):
            if name not in AUDIT_SOURCE_NAMES or name in deferred_names():
                slice_bound(field, name)
    def members(raw, field):
        if not isinstance(raw, dict) or not isinstance(raw.get('sources'), dict):
            slice_bound(field, '<invalid>')
        for name in sorted(raw['sources']):
            slice_bound(field, name, 'R1_DEFERRED_MEMBERSHIP_NONEMPTY')
    def document(raw):
        return load(pinned(raw)) if isinstance(raw, dict) and 'path' in raw and 'sha256' in raw else raw
    for prefix, obj in (('r1_training', value), ('request', request or {})):
        for field in ('routing_inputs', 'row_slice_inputs'):
            if field in obj and (field == 'routing_inputs' or obj[field] != {}):
                raw = obj[field]
                name = sorted(raw)[0] if isinstance(raw, dict) and raw else '<present>'
                slice_bound(prefix+'.'+field, name,
                            'R1_DEFERRED_ROUTING_INPUTS_PRESENT' if field == 'routing_inputs' else '')
        if read_pins:
            if obj.get('row_sources') is not None:
                catalog(document(obj['row_sources']), prefix+'.row_sources')
            if obj.get('source_membership') is not None:
                members(document(obj['source_membership']), prefix+'.source_membership')
    if sources is not None:
        catalog(sources, 'r1_training.row_sources')
    if membership is not None:
        members(membership, 'source_membership')
    if read_pins:
        for field, pin in (('streams.routing', (cfg or {}).get('streams', {}).get('routing')),
                           ('request.routing_base', (request or {}).get('routing_base'))):
            if pin is not None:
                if field == 'request.routing_base':
                    from .r1_handover import pin_values
                    if pin_values(pin) != pin_values((cfg or {}).get('streams', {}).get('routing')):
                        raise ValueError('R1_ROUTING_BASE_DIFFERS')
                receipt = document(pin)
                if receipt.get('source_membership'):
                    slice_bound(field+'.source_membership', '<present>',
                                'R1_ROUTING_BASE_INVALID:R1_DEFERRED_MEMBERSHIP_NONEMPTY')
        sampling = (cfg or {}).get('r2_sampling') or {}
        cards = []
        for field, pin in (('r1_training.mix', value.get('mix')),
                           ('r2_sampling.card', sampling.get('card')),
                           ('request.card', (request or {}).get('card'))):
            if pin is not None:
                cards.append((field, document(pin)))
        population = document(sampling['population']) if sampling.get('population') else {}
        bound_indices = document(sampling['indices']) if sampling.get('indices') else {}
        for field, bound_card in cards:
            deferred_card(bound_card, population.get('counts'), bound_indices.get('cells'), field=field)
        for field, mapping in (('r2_sampling.population.counts', population.get('counts', {})),
                               ('r2_sampling.indices.cells', bound_indices.get('cells', {}))):
            for name, amount in mapping.items():
                if name in deferred_names() and amount:
                    slice_bound(field, name, 'R1_DEFERRED_CELL_NONZERO:'+name)
        if population.get('source_membership'):
            members(document(population['source_membership']), 'r2_sampling.population.source_membership')
    if card is not None:
        deferred_card(card, counts, indices)
    return True

def deferred_names():
    from .r1_population import SLICE_CELLS
    return {*SLICE_CELLS, *PINS, *globals().get('EXTRA_PINS', {}), 'coverage', 'camera_wording'}

def deferred_card(card, counts=None, indices=None, *, field='card'):
    """The base has its own cell; every other routing cell remains empty."""
    from fractions import Fraction
    names = deferred_names()
    base = [c for c in card['cells'] if c['type'] == 'routing_base']
    if len(base) != 1 or base[0]['stream'] != 'routing' or Fraction(str(base[0]['rows_per_step'])) != 64:
        raise ValueError('R1_DEFERRED_BASE_CELL_REQUIRED')
    for cell in card['cells']:
        if cell['type'] in names or cell['stream'] == 'routing' and cell['type'] != 'routing_base':
            name = cell['type']
            if (Fraction(str(cell['rows_per_step'])) != 0
                    or Fraction(str(cell.get('ceiling_rows_per_step', 0))) != 0
                    or counts is not None and counts.get(name, 0) != 0
                    or indices is not None and indices.get(name, [])):
                slice_bound(field+'.cells', name, 'R1_DEFERRED_CELL_NONZERO:'+name)
    for mapping in (counts or {}, indices or {}):
        for name, amount in mapping.items():
            if name in names and amount:
                slice_bound(field+'.cells', name, 'R1_DEFERRED_CELL_NONZERO:'+name)

def routing_request(cfg, request):
    """A minimal request binds the same authenticated base as its config."""
    if not deferred(cfg, request, read_pins=True):
        return False
    from .r1_handover import pin_values
    base = request.get('routing_base')
    if not base or pin_values(base) != pin_values(cfg.get('streams', {}).get('routing')):
        raise ValueError('R1_ROUTING_BASE_DIFFERS')
    value = load(pinned(base))
    from .carrier_c1_routing import ROUTING_SCHEMA
    if value.get('source_membership'):
        slice_bound('request.routing_base.source_membership', '<present>', 'R1_ROUTING_BASE_INVALID')
    if (value.get('schema') != ROUTING_SCHEMA or value.get('scene_role', 'train') != 'train'
            or value.get('heldout_overlap') != 0):
        raise ValueError('R1_ROUTING_BASE_INVALID')
    return True

def source_names(sources, cfg=None):
    if deferred(cfg, sources=sources, read_pins=True):
        return ()
    from .r1_population import SLICE_CELLS
    extra=set(sources)&set(PINS)
    if extra and extra!=set(PINS):raise ValueError('R1_COVERAGE_SOURCES_INCOMPLETE')
    return (*SLICE_CELLS,*sorted(extra),*sorted(set(sources)&set(EXTRA_PINS)))

def normalize(text):
    return ' '.join(unicodedata.normalize('NFKC',text).casefold().split())

class WordingExclusion:
    def __init__(self,pin,camera=None):
        if pin.get('sha256')!=SPLIT:raise ValueError('R1_WORDING_EXCLUSION_PIN')
        value=load(pinned(pin));self.patterns=[]
        if len(value.get('held_out',[]))!=8:raise ValueError('R1_WORDING_EXCLUSION_COUNT')
        for template in value['held_out']:
            expression=re.escape(normalize(template))
            for name in ('a','b','u'):expression=expression.replace(re.escape('{'+name+'}'),'.+?')
            self.patterns.append((template,re.compile('^'+expression+'$')))
        if camera is not None:
            if camera.get('sha256') != CAMERA_WORDINGS:raise ValueError('R1_CAMERA_WORDING_PIN')
            heldout=load(pinned(camera)).get('heldout',{})
            templates=[t for group in heldout.values() for t in group]
            if len(templates)!=24:raise ValueError('R1_CAMERA_WORDING_COUNT')
            for template in templates:
                parts=re.split(r'(\{(?:i|j|n|unit|options)\})',normalize(template))
                expression=''.join('.+?' if p.startswith('{') and p.endswith('}') else re.escape(p) for p in parts)
                self.patterns.append((template,re.compile('^'+expression+'$')))

    def check(self,row):
        for value in (row,row.get('student_input',{}),row.get('routing',{}),row.get('ground_record',{})):
            if not isinstance(value,dict):continue
            question=value.get('question')
            if isinstance(question,str):
                for name,pattern in self.patterns:
                    if pattern.fullmatch(normalize(question)):
                        raise ValueError('R1_HELD_OUT_WORDING:'+name)
        return row

def validate_binding(cfg):
    from .r1_launch22 import validate_removals
    validate_removals(cfg)
    value=cfg.get('r1_training') or {};pin=value.get('wording_exclusion')
    deferred(cfg, read_pins=True)
    sources=load(pinned(value['row_sources'])) if value.get('row_sources') else {}
    extra=set(PINS)&set(sources)
    if extra:
        source_names(sources)
        if pin is None:raise ValueError('R1_WORDING_EXCLUSION_REQUIRED')
        for name,h in PINS.items():
            if sources[name]['source']['sha256']!=h:raise ValueError('R1_COVERAGE_SOURCE_PIN:'+name)
            pinned(sources[name]['source'])
    camera=value.get('camera_wording_exclusion')
    for name in set(EXTRA_PINS)&set(sources):
        if sources[name]['source']['sha256']!=EXTRA_PINS[name]:raise ValueError('R1_CAMERA_SOURCE_PIN')
        pinned(sources[name]['source'])
        if camera is None or pin is None:raise ValueError('R1_CAMERA_WORDING_REQUIRED')
    return WordingExclusion(pin,camera) if pin else None

def rewording(child,parent):
    """Prove that a pinned coverage row changes wording and identifiers only."""
    from copy import deepcopy
    a,b=deepcopy(child),deepcopy(parent)
    units='ground_record' in a
    p=a['provenance']
    edit=p.get('details',{}).pop('question_edit',None) if units else p.pop('dist_diag_question_edit',None)
    if (not edit or edit.get('reworded_from')!=b['qid'] or edit.get('before')!=b['question']
            or edit.get('after')!=a['question'] or edit.get('candidate_id_before')!=b['candidate_id']
            or a['candidate_id']==b['candidate_id']):raise ValueError('R1_COVERAGE_PARENT_IDENTITY')
    keys=('qid','question','candidate_id') if units else ('qid','question','question_identity','candidate_id')
    for row in (a,b):
        for key in keys:row.pop(key,None)
        if units:
            for key in ('qid','question','question_identity','candidate_id'):row['ground_record'].pop(key,None)
    if a!=b:raise ValueError('R1_COVERAGE_NON_WORDING_CHANGE')
    return parent['qid']

def union_rows(base,extra):
    values={}
    for rows in (base,extra):
        for row in rows:
            if (set(row)!={'row_key','canonical','reason'} or row.get('reason')!='k1_heldout_v7'
                    or not isinstance(row.get('row_key'),str) or not row['row_key']
                    or not isinstance(row.get('canonical'),str) or '/' not in row['canonical']):
                raise ValueError('R1_K1_UNION_ROW_INVALID')
            if row['row_key'] in values and values[row['row_key']]!=row:raise ValueError('R1_K1_UNION_CONFLICT')
            values[row['row_key']]=row
    return [values[k] for k in sorted(values)]

def read_list(pin):
    with pinned(pin).open() as f:return [json.loads(line) for line in f if line.strip()]

def verify_union(value,removals,base_hash,n_hash):
    spec=value.get('v7_k1_union');pin=value.get('v7_k1_removal',{})
    if not spec:return False
    if set(spec)!={'base','extra','union'} or spec['base'].get('sha256')!=base_hash or spec['union']!=pin:
        raise ValueError('R1_K1_UNION_BINDING')
    expected=union_rows(read_list(spec['base']),read_list(spec['extra']))
    if read_list(pin)!=expected:raise ValueError('R1_K1_UNION_CONTENT')
    hashes=[p['sha256'] for p in removals]
    if (hashes.count(base_hash)!=1 or hashes.count(pin['sha256'])!=1 or n_hash not in hashes
            or not hashes.index(base_hash)<hashes.index(pin['sha256'])<hashes.index(n_hash)):
        raise ValueError('R1_K1_UNION_ORDER')
    return True
