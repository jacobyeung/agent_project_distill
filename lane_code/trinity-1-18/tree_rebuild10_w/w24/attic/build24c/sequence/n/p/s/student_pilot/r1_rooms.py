"""Pinned physical-room admission; no inference-time policy or network access."""
import csv
import re
from .p3_provenance import load, pinned

AUTHORITY = {
    'split': '27126674a57111585615308cb3e779e169b5693b1c87afafe691ce8e56c2b390',
    'visits': '657020f2d1119220b5068176ffc7298a8585076468407b60d8f5e3e6223442ca',
    'aliases': 'c47c5fcd242edc12396cfc47c300da24d3dd2e68aa6ee24abed965f78c84a11b',
    'reserve': 'bdb5d40244cdaf5060fd0a549acc2844a41039ecf78a23ef021a77eab188a4e3',
    'build': '0cbbf99778a189b0751808506b029414d1916b482cd650c3c0af160f505fded1',
}
TEACHER = '4d4736cf64e496a184d36d74d710e76d1673429e28790613794867ac077048a9'
STORE = '210b25349b23af5b38a5b5d90caa97be2bb296dbabd8773d54e658e0aad22443'
V7_K1_LIST = '43853165f921d077eab92baaf83f29a69cd4f3efef789249bb8db99893853cf6'
N_LIST = '02315a74ed9020a9b7aa2f1a70ac765701bf17c71d4027d4424b9fdf0678a411'


class Rooms:
    def __init__(self, pins):
        if set(pins) != set(AUTHORITY) or any(pins[k]['sha256'] != v for k,v in AUTHORITY.items()):
            raise ValueError('R1_ROOM_AUTHORITY_PIN_MISMATCH')
        paths = {k:pinned(v) for k,v in pins.items()}
        split = load(paths['split'])
        if split['teacher_k1']['sha256'] != TEACHER:
            raise ValueError('R1_ROOM_TEACHER_MISMATCH')
        self.k1 = {c['room'] for c in split['teacher_k1']['captures'] if c['k1_split']=='heldout'}
        self.reserve = {s.strip() for s in paths['reserve'].read_text().splitlines() if s.strip()}
        self.r0 = self.reserve | {c['room'] for c in split['r0_scenes']['captures'].values()}
        with paths['visits'].open() as f:
            self.visits = {r['video_id']:r['visit_id'] for r in csv.DictReader(f)}
        self.aliases = load(paths['aliases'])
        self.build = load(paths['build'])
        if len(self.k1)!=50 or len(self.reserve)!=372:
            raise ValueError('R1_ROOM_AUTHORITY_COUNT_MISMATCH')

    def canonical(self, row):
        # A row's own canonical always wins over an alias lookup.
        for value in (row, row.get('provenance') or {}, row.get('ground_record') or {}, row.get('gt_authority') or {}, row.get('routing') or {}):
            if value.get('canonical'):
                return value['canonical'], 'row_field'
        ds, scene = row.get('dataset',''), row.get('scene','')
        token = {'scannet':'d1','scannetpp':'d2','scannetppv2':'d2','arkitscenes':'d3'}.get(ds,ds)
        canonical = self.aliases.get(token+'/'+scene)
        if canonical:
            return canonical, 'alias'
        if ds in ('scannet','scannetpp','scannetppv2') and scene:
            return ds+'/'+scene, 'dataset_scene'
        if ds=='d1' and re.fullmatch(r'scene\d+_\d+',scene):
            return 'scannet/'+scene, 'dataset_scene'
        if ds=='d2' and re.fullmatch(r'[0-9a-f]{10}',scene):
            return 'scannetpp/'+scene, 'dataset_scene'
        if ds in ('arkitscenes','d3') and scene.isdigit():
            return 'arkitscenes/'+scene, 'dataset_scene'
        return None, 'unresolved'

    def room(self, canonical):
        ds, capture = canonical.split('/',1)
        if ds=='scannet':
            match = re.match(r'(scene\d+)',capture)
            if match:
                return 'scannet/'+match.group(1)
        if ds in ('scannetpp','scannetppv2') and capture:
            return 'scannetpp/'+capture
        if ds=='arkitscenes' and capture.isdigit():
            visit = self.visits.get(capture)
            return 'arkitscenes/venue'+visit if visit and visit!='NA' else 'arkitscenes/capture'+capture
        raise ValueError('R1_ROOM_CANONICAL_UNRESOLVED')

    def status(self, row):
        canonical, how = self.canonical(row)
        if not canonical:
            return 'unresolved', None, how
        try:
            room = self.room(canonical)
        except (ValueError, TypeError):
            return 'unresolved', canonical, how
        return ('r0' if room in self.r0 else 'k1_heldout' if room in self.k1 else 'ok'), canonical, how

    def admit(self, row):
        status, _, _ = self.status(row)
        if status != 'ok':
            raise ValueError('R1_ROOM_ROW_REFUSED:'+status)


def verify_audit(cfg, pin):
    """Certify slice exclusion and bind a separate, explicitly scoped store record."""
    from .r1_coverage import deferred
    deferred(cfg, read_pins=True)
    from .r1_launch22 import validate_removals, bound
    validate_removals(cfg)
    audit = load(pinned(pin))
    value = cfg['r1_training']
    from .r1_handover import pin_values
    if (audit.get('schema')!='r1-room-audit-v1' or audit.get('complete') is not True
            or audit.get('unknown_overlap')!=0 or pin_values(audit.get('row_sources'))!=pin_values(value['row_sources'])
            or [{k:v for k,v in p.items() if k!='path'} for p in audit.get('remove_files',[])]
               != [{k:v for k,v in p.items() if k!='path'} for p in cfg['remove_files']]
            or pin_values(audit.get('authority'))!=pin_values(value.get('room_authority'))):
        raise ValueError('R1_PROOF_ROOM_AUTHORITY_INCOMPLETE')
    rooms = Rooms(audit['authority'])
    sources = load(pinned(value['row_sources']))
    from .r1_coverage import source_names
    for kind in source_names(sources, cfg):
        report = audit['slices'][kind]
        if (pin_values(report['source'])!=pin_values(sources[kind]['source']) or report['unresolved']!=0
                or report['unremoved_hits']!=0):
            raise ValueError('R1_PROOF_ROOM_SLICE_UNCERTIFIED:'+kind)
        pinned(report['source'])
    for removal in cfg['remove_files']:
        pinned({k:removal[k] for k in ('path','sha256')})
    store = audit['store']
    actual = load(pinned(cfg['streams']['vqa']))['database']
    if (pin_values(store['database'])!=pin_values(actual) or pin_values(store['certification'])!=pin_values(audit['authority']['build'])
            or store['scope']!='resolvable_rows_and_pinned_build_record'):
        raise ValueError('R1_PROOF_ROOM_STORE_UNCERTIFIED')
    # The build record certifies its own appended population, not unresolved legacy rows.
    augmented = actual['sha256'] != STORE and bool(value.get('direction_twins'))
    if actual['sha256'] != STORE and bound(cfg) and not augmented:
        raise ValueError('R1_TWIN_BINDING_REQUIRED_FOR_STORE')
    if augmented:
        from .r1_direction_twins import verify_augmented
        verify_augmented(cfg, actual)
    if actual['sha256'] != STORE and not augmented and store['unresolved'] != 0:
        raise ValueError('R1_PROOF_ROOM_STORE_PIN_MISMATCH')
    if actual['sha256'] == STORE or augmented:
        pin = value.get('v7_k1_removal') or {}
        hashes = [p['sha256'] for p in cfg['remove_files']]
        from .r1_coverage import verify_union
        union = verify_union(value, cfg['remove_files'], V7_K1_LIST, N_LIST)
        if ((not union and pin.get('sha256') != V7_K1_LIST) or hashes.count(V7_K1_LIST) != 1
                or N_LIST not in hashes or hashes.index(V7_K1_LIST) >= hashes.index(N_LIST)
                or pin_values(store.get('k1_removal')) != pin_values(pin)):
            raise ValueError('R1_PROOF_V7_K1_REMOVAL_REQUIRED')
        pinned(pin)
        if store.get('unremoved_hits') != 0:
            raise ValueError('R1_PROOF_V7_K1_UNREMOVED')
    return audit


def census(cfg, *, store_hits=None):
    """Stream sources once, retaining only counts and bounded unresolved examples."""
    from collections import Counter
    import json
    import sqlite3
    from .row_removals import Removals
    from .r1_coverage import deferred
    deferred(cfg, read_pins=True)
    value = cfg['r1_training']
    rooms = Rooms(value['room_authority'])
    removals = Removals(cfg['remove_files'])
    from .r1_coverage import validate_binding
    wording = validate_binding(cfg)
    reports, hits = {}, []
    sources = load(pinned(value['row_sources']))
    from .r1_coverage import source_names
    for kind in source_names(sources, cfg):
        counts, hows = Counter(), Counter()
        with pinned(sources[kind]['source']).open() as f:
            for line in f:
                row = json.loads(line)
                if wording is not None:wording.check(row)
                status, canonical, how = rooms.status(row)
                counts['rows'] += 1; counts[status] += 1; hows[how] += 1
                if status in ('k1_heldout','r0'):
                    hits.append(dict(row_key=row['qid'],reason='k1_heldout_known' if status=='k1_heldout' else status,
                                     scene=row.get('dataset','')+'/'+row.get('scene',''),canonical=canonical))
                    counts['unremoved_hits'] += int(removals.keep(row))
        reports[kind] = dict(source=sources[kind]['source'],canonical_from=dict(hows),
                            **{k:counts[k] for k in ('rows','ok','k1_heldout','r0','unresolved','unremoved_hits')})
    database = load(pinned(cfg['streams']['vqa']))['database']
    twin_rooms = None
    if value.get('direction_twins'):
        from .r1_direction_twins import Binding
        twin_rooms = Binding(cfg)
    counts, hows, examples = Counter(), Counter(), []
    connection = sqlite3.connect(pinned(database).as_uri()+'?mode=ro',uri=True)
    try:
        for (raw,) in connection.execute('SELECT row FROM rows ORDER BY i'):
            row = json.loads(raw)
            if wording is not None:wording.check(row)
            status, canonical, how = rooms.status(row)
            if twin_rooms is not None:
                room=twin_rooms.room(row)
                status='r0' if room in rooms.r0 else 'k1_heldout' if room in rooms.k1 else 'ok'
                how='pinned_tiered_room' if how=='unresolved' else how
            counts['rows'] += 1; counts[status] += 1; hows[how] += 1
            if status in ('k1_heldout','r0'):
                counts['unremoved_hits'] += int(removals.keep(row))
                if store_hits is not None and status == 'k1_heldout':
                    store_hits.append(dict(row_key=row['qid'],canonical=canonical,reason='k1_heldout_v7'))
            if status=='unresolved' and len(examples)<200:
                examples.append(dict(row_key=row['qid'],dataset=row.get('dataset'),scene=row.get('scene')))
    finally:
        connection.close()
    unknown = sum(r['unresolved'] for r in reports.values())
    audit = dict(schema='r1-room-audit-v1',complete=unknown==0 and all(r['unremoved_hits']==0 for r in reports.values()),
                 unknown_overlap=unknown,k1_rooms=len(rooms.k1),r0_rooms=len(rooms.reserve),
                 r0_union_rooms=len(rooms.r0),authority=value['room_authority'],
                 row_sources=value['row_sources'],remove_files=cfg['remove_files'],slices=reports,
                 store=dict(database=database,certification=value['room_authority']['build'],
                            scope='resolvable_rows_and_pinned_build_record',canonical_from=dict(hows),
                            unresolved_examples=examples,
                            k1_removal=value.get('v7_k1_removal'),
                            **{k:counts[k] for k in ('rows','ok','k1_heldout','r0','unresolved','unremoved_hits')}),
                 certifies='All bound pinned slices exclude K1/R0 after the pinned lists. The N-side list excludes resolvable v7 K1 rows when bound. Unresolved v7 rows retain the population admitted by P and are bound to the pinned v7 build record, not declared overlap-free. The build record certifies only the population that record names.')
    return audit, hits
