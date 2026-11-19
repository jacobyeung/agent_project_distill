from pathlib import Path
L=Path(__file__).resolve().parents[2];T=L/"work/tree_r1"
p=T/"student_pilot/r1_coverage.py";s=p.read_text();a=s.index("def deferred(cfg):");b=s.index("def normalize(text):")
s=s[:a]+'''# These two catalog entries describe audit provenance, never routing composition.
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
            if name not in AUDIT_SOURCE_NAMES:
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
    if deferred(cfg, sources=sources):
        return ()
    from .r1_population import SLICE_CELLS
    extra=set(sources)&set(PINS)
    if extra and extra!=set(PINS):raise ValueError('R1_COVERAGE_SOURCES_INCOMPLETE')
    return (*SLICE_CELLS,*sorted(extra))

''' +s[b:]
a=s.index('    if deferred(cfg):',s.index('def validate_binding'));b=s.index('    sources=load',a)
s=s[:a]+"    deferred(cfg, read_pins=True)\n"+s[b:];p.write_text(s)
def edit(name,old,new):
 p=T/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new,1))
edit('launch_r1/production_proof.py',"        card = load(pinned(cfg['r1_training']['mix']))", "        from student_pilot.r1_coverage import deferred\n        deferred(cfg, request, read_pins=True)\n        card = load(pinned(cfg['r1_training']['mix']))")
edit('launch_r1/entry.py',"def admit(cfg):\n", "def admit(cfg):\n    from student_pilot.r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n")
edit('launch_r1/entry.py','    root = Path(root).resolve()\n    job_tmp = fresh_tmp', '    from student_pilot.r1_coverage import deferred\n    deferred(cfg, request)\n    root = Path(root).resolve()\n    job_tmp = fresh_tmp')
edit('student_pilot/s1_admission.py','    cfg = load(pinned(config_pin))\n', '    cfg = load(pinned(config_pin))\n    from .r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n')
edit('student_pilot/r1_rooms.py',"    audit = load(pinned(pin))\n", "    from .r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n    audit = load(pinned(pin))\n")
edit('student_pilot/r1_rooms.py',"    value = cfg['r1_training']\n    rooms = Rooms", "    from .r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n    value = cfg['r1_training']\n    rooms = Rooms")
edit('student_pilot/r1_population.py',"        if minimal and self.sources:\n            raise ValueError('R1_DEFERRED_MEMBERSHIP_NONEMPTY')", "        if minimal:\n            from .r1_coverage import deferred\n            deferred({'r1_training': {'routing_slices': 'deferred_first_boundary'}}, membership=value)")
edit('student_pilot/r1_population.py',"    minimal = deferred(cfg)\n", "    minimal = deferred(cfg, read_pins=True, card=card)\n")
edit('student_pilot/r1_population.py',"    receipt, _ = prepared(cfg)\n", "    from .r1_coverage import deferred, slice_bound\n    minimal = deferred(cfg, read_pins=True)\n    routing = load(pinned(cfg['streams']['routing']))\n    if minimal and routing.get('source_membership'):\n        slice_bound('streams.routing.source_membership', '<present>', 'R1_DEFERRED_MEMBERSHIP_NONEMPTY')\n    receipt, _ = prepared(cfg)\n")
edit('launch_r1/build.py',"    output=Path(output)\n", "    cfg_input_root=Path(cfg).resolve().parent\n    cfg=load(cfg)\n    from student_pilot.r1_coverage import deferred\n    deferred(cfg, read_pins=True)\n    output=Path(output)\n")
edit('launch_r1/build.py',"    cfg_input_root=Path(cfg).resolve().parent\n    cfg=load(cfg)\n    from student_pilot.p3_provenance import pinned", "    from student_pilot.p3_provenance import pinned")
print('Updated central gate and six callers')
