"""Differential behaviour harness: python harness.py TREE LABEL TMP OUT.json

Runs one deterministic battery of cases against TREE. Every case records the
result or exception (type, args, message, traceback statements), every file
open/mkdir/sqlite connect observed by an audit hook, and files written under
the case output directory. TMP must be the same absolute path for every tree so
fixture pins are byte-identical across trees.
"""
import copy
import hashlib
import inspect
import itertools
import json
import os
import sqlite3
import sys
import traceback
from pathlib import Path
from unittest.mock import patch

TREE = Path(sys.argv[1]).resolve()
LABEL = sys.argv[2]
TMP = Path(sys.argv[3]).resolve()
OUT = Path(sys.argv[4]).resolve()
TMP.mkdir(parents=True, exist_ok=False)
os.environ['TMPDIR'] = str(TMP)
os.chdir(TMP)
sys.path.insert(0, str(TREE))
sys.path.insert(1, str(Path(__file__).resolve().parent))

import realmap  # noqa: E402
from student_pilot import r1_coverage as C, r1_routing as R, r1_population as P  # noqa: E402
from student_pilot import r2_intake as I, r1_persisted, r1_launch22  # noqa: E402
from student_pilot.p3_provenance import file_pin, load, digest  # noqa: E402
import student_pilot.carrier_c1_run, student_pilot.carrier_c1_routing, student_pilot.r1_rooms  # noqa: E402,F401
import student_pilot.row_removals, student_pilot.s1_exclusions, student_pilot.r1_handover  # noqa: E402,F401
from student_pilot.carrier_c1_routing import ROUTING_SCHEMA  # noqa: E402

FAMILIES = ('absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery', 'camera_wording')
AUDIT = ('room', 'room_programs_excluded')
NAMES8 = FAMILIES + AUDIT
SLICES = ('recovery', 'absolute_distance', 'units')
COVER = ('coverage_distance', 'coverage_units')
HAS_DECL = hasattr(C, 'routing_declaration')
MEMBERSHIP_CFG = 'cfg' in inspect.signature(P.Membership.__init__).parameters
SKIP_PREFIX = tuple(p for p in {sys.prefix, sys.base_prefix, '/proc', '/dev', '/etc', '/usr', '/sys'} if p)


def norm(s):
    s = str(s)
    return s.replace(str(TREE), '<TREE>').replace(str(TMP), '<TMP>')


def normj(v):
    if isinstance(v, dict):
        return {norm(k): normj(x) for k, x in v.items()}
    if isinstance(v, (list, tuple)):
        return [normj(x) for x in v]
    if isinstance(v, (str, Path)):
        return norm(v)
    if isinstance(v, (int, float, bool)) or v is None:
        return v
    if isinstance(v, C.WordingExclusion):
        return dict(WordingExclusion=[t for t, _ in v.patterns])
    return dict(object=type(v).__name__)


EVENTS = None


def hook(event, args):
    if EVENTS is None:
        return
    if event == 'open':
        path = args[0]
        if isinstance(path, int):
            return
        p = os.fsdecode(path)
        if p.endswith(('.py', '.pyc', '.so')) or p.startswith(SKIP_PREFIX):
            return
        EVENTS.append(['open', norm(p), str(args[1])])
    elif event in ('os.mkdir', 'os.rename', 'os.remove', 'os.rmdir', 'shutil.rmtree', 'sqlite3.connect'):
        a = args[0]
        EVENTS.append([event, norm(os.fsdecode(a)) if isinstance(a, (str, bytes, os.PathLike)) else repr(a)])


sys.addaudithook(hook)
RESULTS = {}


def tree_files(d):
    d = Path(d)
    if not d.exists():
        return None
    out = {}
    for p in sorted(d.rglob('*')):
        if p.is_file():
            out[norm(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        else:
            out[norm(p)] = 'dir'
    return out


def run(name, fn, watch=None):
    global EVENTS
    assert name not in RESULTS, name
    before = tree_files(watch) if watch else None
    rec = {}
    EVENTS = []
    try:
        rec['ok'] = normj(fn())
    except BaseException as e:  # noqa: BLE001
        rec['exc'] = type(e).__name__
        rec['args'] = normj(list(e.args))
        rec['str'] = norm(str(e))
        tb = traceback.extract_tb(e.__traceback__)
        rec['frames'] = [[norm(f.filename) if str(TREE) in f.filename else Path(f.filename).name, f.name,
                          norm(f.line)] for f in tb]
        rec['lines'] = [[norm(f.filename), f.lineno] for f in tb if str(TREE) in f.filename]
        if e.__cause__ is not None:
            rec['cause'] = [type(e.__cause__).__name__, norm(str(e.__cause__))]
    finally:
        rec['events'] = EVENTS
        EVENTS = None
    if watch:
        rec['written'] = {'before': before, 'after': tree_files(watch)}
    RESULTS[name] = rec
    return rec


class Fx:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.n = 0

    def path(self, suffix='.json'):
        self.n += 1
        return self.root/('f%05d%s' % (self.n, suffix))

    def pin(self, value):
        p = self.path()
        p.write_text(json.dumps(value, sort_keys=True))
        return file_pin(p)

    def raw(self, data, suffix='.jsonl'):
        p = self.path(suffix)
        p.write_bytes(data)
        return file_pin(p)


FX = Fx(TMP/'fx')
MAPS, _ = realmap.build_map()
ORIG = realmap.original()
for key in ('wording_exclusion', 'camera_wording_exclusion'):
    pin = ORIG['r1_training'][key]
    MAPS[pin['sha256']] = str(realmap.local(pin['path']))
NREM = ORIG['remove_files'][-1]
MAPS[NREM['sha256']] = str(realmap.local(NREM['path']))
WORDING = dict(path=MAPS[ORIG['r1_training']['wording_exclusion']['sha256']],
               sha256=ORIG['r1_training']['wording_exclusion']['sha256'])
CAMEX = dict(path=MAPS[ORIG['r1_training']['camera_wording_exclusion']['sha256']],
             sha256=ORIG['r1_training']['camera_wording_exclusion']['sha256'])
LAUNCH22 = copy.deepcopy(ORIG['r1_training']['launch22'])
REMOVE_FILES = [dict(path=str(realmap.local(p['path'])), sha256=p['sha256']) for p in ORIG['remove_files']]
REMOVALS_LOCAL = all(Path(p['path']).is_file() and realmap.sha(p['path']) == p['sha256'] for p in REMOVE_FILES)

# Deterministic fixture source files, one per family.
SRC = {k: FX.raw(('{"fixture":"%s"}\n' % k).encode()) for k in NAMES8}
FIX_PINS = {k: SRC[k]['sha256'] for k in COVER}
FIX_EXTRA = {'camera_wording': SRC['camera_wording']['sha256']}


def deferred_pins_cfg():
    return dict(r1_training=dict(routing_slices='deferred_first_boundary',
                                 row_sources=FX_STATIC['room_rows'], source_membership=FX_STATIC['empty_members']))


FX_STATIC = dict(room_rows=FX.pin({'room': dict(source=SRC['room'])}), empty_members=FX.pin(dict(sources={})),
                 empty=FX.pin({}))

# ---------------------------------------------------------------- source_names
CFGS = {
    'None': lambda: None, 'empty': lambda: {}, 'r1empty': lambda: {'r1_training': {}},
    'deferred': lambda: {'r1_training': {'routing_slices': 'deferred_first_boundary'}},
    'bogus': lambda: {'r1_training': {'routing_slices': 'bogus'}},
    'deferred_pins': deferred_pins_cfg,
}


def subsets(names):
    for n in range(len(names)+1):
        yield from itertools.combinations(names, n)


def group_source_names():
    for sub in subsets(NAMES8):
        src = {k: dict(source=SRC[k]) for k in sub}
        tag = '+'.join(sub) or '-'
        run('SN|noarg|'+tag, lambda: C.source_names(src))
        for cname, make in CFGS.items():
            run('SN|'+cname+'|'+tag, lambda: C.source_names(src, make()))


# ---------------------------------------------------------------- validate_binding
def vb_cfg(sub, mode, excl, camera='fixture'):
    specs = {k: dict(source=SRC[k]) for k in sub}
    if 'camera_wording' in sub and camera != 'fixture':
        specs['camera_wording'] = dict(source=camera)
    t = dict(row_sources=FX.pin(specs))
    cfg = dict(r1_training=t)
    if mode == 'deferred':
        t['routing_slices'] = 'deferred_first_boundary'
    if excl in ('wording', 'both'):
        t['wording_exclusion'] = WORDING
    if excl == 'bad_wording':
        t['wording_exclusion'] = FX_STATIC['empty']
    if excl == 'both':
        t['camera_wording_exclusion'] = CAMEX
        t['launch22'] = LAUNCH22
        cfg['remove_files'] = REMOVE_FILES
    return cfg


def group_validate_binding():
    for sub in subsets(NAMES8):
        tag = '+'.join(sub) or '-'
        for mode in ('plain', 'deferred'):
            for excl in ('none', 'wording', 'both', 'bad_wording'):
                cfg = vb_cfg(sub, mode, excl)
                run('VB|real|%s|%s|%s' % (mode, excl, tag), lambda: C.validate_binding(cfg))
                with patch.dict(C.PINS, FIX_PINS), patch.dict(C.EXTRA_PINS, FIX_EXTRA):
                    run('VB|fixpins|%s|%s|%s' % (mode, excl, tag), lambda: C.validate_binding(cfg))


# ---------------------------------------------------------------- Membership
def membership(pin, minimal, cfg):
    if MEMBERSHIP_CFG:
        return P.Membership(pin, minimal=minimal, cfg=cfg)
    return P.Membership(pin, minimal=minimal)


def fixture_row(kind):
    return dict(dataset='d1', scene='fixture_clean', question_type='camera_displacement', qid='fixture_'+kind,
                target='<think>The camera moves right between the shown frames.</think><answer>right</answer>')


def group_membership():
    cfgs = {'legacy_absent': None, 'legacy_r1empty': {'r1_training': {}}, 'legacy_empty': {},
            'deferred': {'r1_training': {'routing_slices': 'deferred_first_boundary'}},
            'deferred_pins': deferred_pins_cfg()}
    for sub in subsets(FAMILIES + ('room',)):
        tag = '+'.join(sub) or '-'
        sources = {}
        rows = {}
        for k in sub:
            row = dict(fixture_row(k), r1_source=dict(family=k, sha256=SRC[k]['sha256']))
            rows[k] = row
            sources[k] = dict(source=SRC[k], rows={row['qid']: digest(row)})
        pin = FX.pin(dict(schema='r1-source-membership-v1', sources=sources))
        for cname, cfg in cfgs.items():
            for minimal in (False, True):
                reach = (minimal is False and cname.startswith('legacy')) or (minimal is True and cname.startswith('deferred'))
                prefix = 'MEM|' + ('reach' if reach else 'unreach')

                def body():
                    m = membership(pin, minimal, copy.deepcopy(cfg))
                    cells = []
                    probes = [*rows.values(), dict(fixture_row('base'), qid='a0_recovery_1'),
                              dict(fixture_row('base'), qid='base_cam'),
                              dict(fixture_row('x'), qid='misfiled', r1_source=dict(family='units', sha256='0'*64))]
                    for row in probes:
                        try:
                            cells.append(m.cell(row, 'routing'))
                        except ValueError as e:
                            cells.append('!'+str(e))
                    return dict(sources=sorted(m.sources), rows=sorted(m.rows), cells=cells)
                run('%s|%s|%s|%s' % (prefix, cname, minimal, tag), body)


# ---------------------------------------------------------------- compose_native (tiny fixtures)
def tiny_base(cfg):
    db = sqlite3.connect(':memory:')
    db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
    db.commit()
    p = FX.path('.sqlite')
    p.write_bytes(db.serialize())
    db.close()
    division = FX.pin(dict(train_scenes=['d1/fixture_clean'], heldout_scenes=['d1/held']))
    cfg.update(dev_scene_exclusions=FX.pin(dict(schema='dev_s1_withhold_v1', natives=['d1/dev'], rooms=['d1/dev'],
               physical_groups=['scannet/dev'], canonical={'d1/dev': ['scannet/dev']}, aliases={'d1/dev': ['d1/vdev']})),
               benchmark_scene_exclusions=FX.pin(dict(schema='benchmark_scene_exclusions_v1', scenes=['d1/benchmark'])))
    return FX.pin(dict(schema=ROUTING_SCHEMA, stream='routing', database=file_pin(p), count=0, division=division,
                       scene_role='train', heldout_overlap=0))


def fake_intake(manifest_path, *, limit=2000, select_types=None):
    manifest = load(manifest_path)
    kind = manifest['family']
    return [dict(row=fixture_row(kind), target={})], dict(family=kind, rows=1, limit=limit)


def native_cfg(names, *, routing_inputs=True, catalog='ok', staged='ok', extra_specs=(), declare=None,
               excl=None, manifests='ok', deferred=False, room=False):
    cfg = {}
    t = {}
    cfg['r1_training'] = t
    specs = {k: dict(source=SRC[k]) for k in names}
    for k in extra_specs:
        specs[k] = dict(source=SRC[k])
    if room:
        specs['room'] = dict(source=SRC['room'])
    t['row_sources'] = FX.pin(specs)
    if deferred:
        t['routing_slices'] = 'deferred_first_boundary'
    srcs = {k: SRC[k] for k in names}
    if catalog == 'ok':
        t['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={
            k: dict(source=SRC[k], qids=['fixture_'+k]) for k in names}))
    elif catalog == 'invalid':
        t['source_membership'] = FX.pin(dict(schema='other', sources={}))
    elif catalog == 'differs':
        t['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={
            k: dict(source=SRC['room'], qids=['fixture_'+k]) for k in names}))
    elif catalog == 'misfiled':
        t['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={
            k: dict(source=SRC[k], qids=[]) for k in names}))
    elif catalog == 'extra':
        t['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={
            k: dict(source=SRC.get(k, SRC['room']), qids=['fixture_'+k]) for k in (*names, 'recovery', 'foreign')}))
    if staged == 'differs':
        t['row_slice_inputs'] = {**srcs, names[0]: SRC['room']} if names else {'x': SRC['room']}
    elif staged == 'extra':
        t['row_slice_inputs'] = {**srcs, 'foreign': SRC['room']}
    elif staged == 'explicit':
        t['row_slice_inputs'] = dict(srcs)
    if routing_inputs:
        man = {}
        for k in names:
            m = dict(schema='r2-family-manifest-v1', family=k, stream='routing', rows=SRC[k],
                     extent_receipt=cfg.get('extent_receipt'))
            if manifests == 'differs' and k == names[0]:
                m['family'] = 'other'
            man[k] = FX.pin(m)
        if manifests == 'missing_kind' and names:
            man.pop(names[-1])
        if manifests == 'extra':
            man['foreign'] = FX_STATIC['empty']
        t['routing_inputs'] = man
    if excl in ('wording', 'both'):
        t['wording_exclusion'] = WORDING
    if excl == 'both':
        t['camera_wording_exclusion'] = CAMEX
        t['launch22'] = LAUNCH22
        cfg['remove_files'] = REMOVE_FILES
    if declare is not None:
        bound, deferred_reasons = declare
        t['routing_slice_declaration'] = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(bound),
                                                     deferred=deferred_reasons))
    return cfg


def reasons(bound):
    return {k: 'Awaiting validated rows' for k in FAMILIES if k not in bound}


def compose_case(name, cfg, *, mock_intake=True, base=True):
    out = TMP/'out'/name.replace('|', '_').replace('+', '.')
    base_pin = tiny_base(cfg) if base else {}

    def body():
        with patch.dict(C.PINS, FIX_PINS), patch.dict(C.EXTRA_PINS, FIX_EXTRA):
            if mock_intake:
                with patch.object(I, 'intake', side_effect=fake_intake):
                    return R.compose_native(cfg, base_pin, out)
            return R.compose_native(cfg, base_pin, out)
    rec = run(name, body, watch=out)
    files = (rec['written']['after'] or {})
    rec['written_files'] = sorted(Path(k).name for k, v in files.items() if v != 'dir')
    for fname in ('receipt.json', 'membership.json'):
        p = out/fname
        if p.is_file():
            rec[fname] = normj(json.loads(p.read_text()))
    return rec


def group_compose_legacy():
    S3 = SLICES
    S5 = SLICES + COVER
    S6 = S5 + ('camera_wording',)
    # deferred configs
    d = dict(r1_training=dict(routing_slices='deferred_first_boundary', row_sources=FX.pin({}),
                              source_membership=FX.pin(dict(sources={}))))
    compose_case('CN|legacy|deferred_min', d, base=False)
    compose_case('CN|legacy|deferred_min_tinybase', copy.deepcopy(d))
    d2 = copy.deepcopy(d)
    d2['r1_training']['row_sources'] = FX.pin({k: dict(source=SRC[k]) for k in AUDIT})
    compose_case('CN|legacy|deferred_audit_names', d2)
    d3 = copy.deepcopy(d)
    d3['r1_training']['row_slice_inputs'] = {}
    compose_case('CN|legacy|deferred_empty_staged', d3)
    d4 = copy.deepcopy(d)
    d4['r1_training']['routing_inputs'] = {}
    compose_case('CN|legacy|deferred_routing_inputs_present', d4)
    d5 = copy.deepcopy(d)
    d5['r1_training']['row_sources'] = FX.pin({k: dict(source=SRC[k]) for k in S3})
    compose_case('CN|legacy|deferred_slices_in_row_sources', d5)
    d6 = copy.deepcopy(d)
    d6['r1_training']['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={}))
    compose_case('CN|legacy|deferred_catalog_schema', d6)
    compose_case('CN|legacy|deferred_native_cfg_s3', native_cfg(S3, deferred=True))
    compose_case('CN|legacy|deferred_native_cfg_noinputs', native_cfg((), deferred=True, routing_inputs=False))
    d7 = copy.deepcopy(d)
    d7['r1_training']['routing_slices'] = 'bogus'
    compose_case('CN|legacy|bogus_routing_slices', d7)
    # legacy without routing_inputs
    for tag, names, excl in (('s3', S3, None), ('s5', S5, 'wording'), ('s6', S6, 'both'), ('s3cam', S3+('camera_wording',), 'both')):
        compose_case('CN|legacy|no_routing_inputs_'+tag, native_cfg(names, routing_inputs=False, excl=excl))
        compose_case('CN|legacy|no_routing_inputs_no_catalog_'+tag,
                     native_cfg(names, routing_inputs=False, catalog=None, excl=excl))
    # full legacy, varying the failure point
    for tag, names, excl in (('s3', S3, None), ('s5', S5, 'wording'), ('s6', S6, 'both'), ('s3cam', S3+('camera_wording',), 'both')):
        compose_case('CN|legacy|full_ok_'+tag, native_cfg(names, excl=excl))
        compose_case('CN|legacy|full_ok_room_'+tag, native_cfg(names, excl=excl, room=True))
        compose_case('CN|legacy|explicit_staged_'+tag, native_cfg(names, excl=excl, staged='explicit'))
        compose_case('CN|legacy|staged_differs_'+tag, native_cfg(names, excl=excl, staged='differs'))
        compose_case('CN|legacy|staged_extra_'+tag, native_cfg(names, excl=excl, staged='extra'))
        compose_case('CN|legacy|no_catalog_'+tag, native_cfg(names, excl=excl, catalog=None))
        compose_case('CN|legacy|catalog_invalid_'+tag, native_cfg(names, excl=excl, catalog='invalid'))
        compose_case('CN|legacy|catalog_differs_'+tag, native_cfg(names, excl=excl, catalog='differs'))
        compose_case('CN|legacy|catalog_extra_'+tag, native_cfg(names, excl=excl, catalog='extra'))
        compose_case('CN|legacy|misfiled_'+tag, native_cfg(names, excl=excl, catalog='misfiled'))
        compose_case('CN|legacy|manifest_differs_'+tag, native_cfg(names, excl=excl, manifests='differs'))
        compose_case('CN|legacy|manifest_missing_kind_'+tag, native_cfg(names, excl=excl, manifests='missing_kind'))
        compose_case('CN|legacy|manifest_extra_'+tag, native_cfg(names, excl=excl, manifests='extra'))
        compose_case('CN|legacy|unmocked_intake_'+tag, native_cfg(names, excl=excl), mock_intake=False)
    compose_case('CN|legacy|missing_slice_units', native_cfg(('recovery', 'absolute_distance')))
    compose_case('CN|legacy|one_coverage', native_cfg(SLICES+('coverage_units',), excl='wording'))
    compose_case('CN|legacy|coverage_no_wording', native_cfg(S5))
    compose_case('CN|legacy|camera_no_exclusion', native_cfg(S3+('camera_wording',), excl='wording'))
    c = native_cfg(S3)
    c['r1_training'].pop('row_sources')
    compose_case('CN|legacy|no_row_sources', c)
    # compose() called directly with a deferred configuration (no production caller does this)
    for tag, srcs in (('empty', {}), ('s3', {k: SRC[k] for k in S3})):
        cfg = dict(r1_training=dict(routing_slices='deferred_first_boundary'))
        base_pin = tiny_base(cfg)
        out = TMP/'out'/('compose_direct_deferred_'+tag)
        run('CD|deferred|'+tag, lambda: R.compose(base_pin, srcs, [], cfg, out), watch=out)


def group_compose_declared():
    cases = (('s4', FAMILIES[:4], 'wording'), ('s5', FAMILIES[:5], 'wording'), ('s6', FAMILIES, 'both'),
             ('cu', ('coverage_units',), 'wording'), ('none', (), None), ('rec', ('recovery',), None),
             ('cam', ('camera_wording',), 'both'), ('s3', SLICES, None), ('ad_u', ('absolute_distance', 'units'), None))
    for tag, names, excl in cases:
        decl = (names, reasons(names))
        compose_case('DC|ok|'+tag, native_cfg(names, excl=excl, declare=decl))
        compose_case('DC|ok_room|'+tag, native_cfg(names, excl=excl, declare=decl, room=True))
        compose_case('DC|staged_differs|'+tag, native_cfg(names, excl=excl, declare=decl, staged='differs'))
        compose_case('DC|staged_extra|'+tag, native_cfg(names, excl=excl, declare=decl, staged='extra'))
        compose_case('DC|no_routing_inputs|'+tag, native_cfg(names, excl=excl, declare=decl, routing_inputs=False))
        compose_case('DC|manifest_missing_kind|'+tag, native_cfg(names, excl=excl, declare=decl, manifests='missing_kind'))
        compose_case('DC|manifest_extra|'+tag, native_cfg(names, excl=excl, declare=decl, manifests='extra'))
        compose_case('DC|catalog_invalid|'+tag, native_cfg(names, excl=excl, declare=decl, catalog='invalid'))
        compose_case('DC|catalog_extra|'+tag, native_cfg(names, excl=excl, declare=decl, catalog='extra'))
        compose_case('DC|catalog_differs|'+tag, native_cfg(names, excl=excl, declare=decl, catalog='differs'))
        compose_case('DC|source_undeclared|'+tag, native_cfg(names, excl=excl, declare=decl,
                     extra_specs=[k for k in FAMILIES if k not in names][:1]))
        if names:
            short = native_cfg(names[:-1], excl=excl, declare=decl)
            compose_case('DC|source_missing|'+tag, short)
        cfg = native_cfg(names, excl=excl, declare=decl)
        cfg['r1_training']['routing_slices'] = 'deferred_first_boundary'
        compose_case('DC|with_deferred|'+tag, cfg)
        cfg = native_cfg(names, excl=excl, declare=decl)
        cfg['r1_training']['routing_slice_declaration'] = dict(cfg['r1_training']['routing_slice_declaration'], sha256='0'*64)
        compose_case('DC|changed_pin|'+tag, cfg)
        if names:
            cfg = native_cfg(names, excl=excl, declare=decl)
            k = names[0]
            cfg['r1_training']['routing_inputs'][k] = dict(path=str(TMP/'MISSING.json'), sha256='0'*64)
            compose_case('DC|envelope_changed|'+tag, cfg)


def group_declarations():
    for sub in subsets(FAMILIES):
        tag = '+'.join(sub) or '-'
        decl = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(sub), deferred=reasons(sub)))
        cfg = dict(r1_training=dict(routing_slice_declaration=decl))
        run('DS|exact|'+tag, lambda: C.source_names({k: dict(source=SRC[k]) for k in sub}, cfg))
        run('DS|audit|'+tag, lambda: C.source_names({k: dict(source=SRC[k]) for k in sub + AUDIT}, cfg))
        run('DS|reversed|'+tag, lambda: C.source_names({k: dict(source=SRC[k]) for k in reversed(sub)}, cfg))
        if sub:
            run('DS|missing|'+tag, lambda: C.source_names({k: dict(source=SRC[k]) for k in sub[1:]}, cfg))
        rest = [k for k in FAMILIES if k not in sub]
        if rest:
            run('DS|undeclared|'+tag, lambda: C.source_names({k: dict(source=SRC[k]) for k in (*sub, rest[0])}, cfg))
        run('DS|foreign|'+tag, lambda: C.source_names({**{k: dict(source=SRC[k]) for k in sub}, 'foreign': {}}, cfg))
        run('DS|command|'+tag, lambda: C.source_names({**{k: dict(source=SRC[k]) for k in sub}, 'command': 'x'}, cfg))
        run('DS|declared_names_staged|'+tag, lambda: C.declared_names({k: SRC[k] for k in sub}, load(decl['path']), 'staged_source')
            if HAS_DECL else 'n/a')
    good = dict(schema='r1-routing-slices-v1', bound=list(FAMILIES[:4]), deferred=reasons(FAMILIES[:4]))
    variants = {
        'good': good, 'schema': dict(good, schema='v0'), 'extra_key': dict(good, note='x'),
        'missing_key': {k: v for k, v in good.items() if k != 'deferred'},
        'bound_not_list': dict(good, bound=tuple(good['bound']) and 'absolute_distance'),
        'bound_nonstr': dict(good, bound=[*good['bound'], 1]), 'duplicate': dict(good, bound=[*good['bound'], 'units']),
        'deferred_not_dict': dict(good, deferred=list(good['deferred'])),
        'missing_reason': dict(good, deferred={'recovery': 'x'}),
        'empty_reason': dict(good, deferred={**good['deferred'], 'recovery': '  '}),
        'nonstr_reason': dict(good, deferred={**good['deferred'], 'recovery': 3}),
        'overlap': dict(good, bound=[*good['bound'], 'recovery']),
        'unknown_bound': dict(good, bound=[*good['bound'], 'foreign']),
        'unknown_deferred': dict(good, deferred={**good['deferred'], 'foreign': 'x'}),
        'list_doc': [1, 2], 'audit_bound': dict(good, bound=[*good['bound'], 'room']),
    }
    for vname, v in variants.items():
        pin = FX.pin(v)
        cfg = dict(r1_training=dict(routing_slice_declaration=pin))
        run('DV|'+vname, lambda: C.source_names({k: dict(source=SRC[k]) for k in FAMILIES[:4]}, cfg))
        run('DV|routing_declaration|'+vname, lambda: C.routing_declaration(cfg) if HAS_DECL else 'n/a')
    pin = FX.pin(good)
    for vname, bad in (('changed_sha', dict(pin, sha256='0'*64)), ('missing_path', dict(path=str(TMP/'nope.json'), sha256=pin['sha256'])),
                       ('not_pin', 'x'), ('extra_field', dict(pin, x=1)), ('relative', dict(path='rel.json', sha256=pin['sha256']))):
        cfg = dict(r1_training=dict(routing_slice_declaration=bad))
        run('DV|pin|'+vname, lambda: C.source_names({k: dict(source=SRC[k]) for k in FAMILIES[:4]}, cfg))
    cfg = dict(r1_training=dict(routing_slice_declaration=pin, routing_slices='deferred_first_boundary'))
    run('DV|mix_source_names', lambda: C.source_names({}, cfg))
    run('DV|mix_deferred', lambda: C.deferred(cfg))
    run('DV|mix_validate_binding', lambda: C.validate_binding(cfg))
    # validate_binding with declarations
    for sub in subsets(FAMILIES):
        tag = '+'.join(sub) or '-'
        decl = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(sub), deferred=reasons(sub)))
        for excl in ('none', 'wording', 'both'):
            cfg = vb_cfg(sub, 'plain', excl)
            cfg['r1_training']['routing_slice_declaration'] = decl
            run('DB|real|%s|%s' % (excl, tag), lambda: C.validate_binding(cfg))
            with patch.dict(C.PINS, FIX_PINS), patch.dict(C.EXTRA_PINS, FIX_EXTRA):
                run('DB|fixpins|%s|%s' % (excl, tag), lambda: C.validate_binding(cfg))
    # Membership identity with declarations
    for sub in (FAMILIES[:4], FAMILIES[:5], ('coverage_units',), (), FAMILIES):
        tag = '+'.join(sub) or '-'
        decl = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(sub), deferred=reasons(sub)))
        moved = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(sub), deferred=reasons(sub)))
        other = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(sub), deferred={k: 'other' for k in reasons(sub)}))
        srcs = {k: dict(source=SRC[k], rows={}) for k in sub}
        doc = dict(schema='r1-source-membership-v1', sources=srcs, routing_slice_declaration=decl, deferred=reasons(sub))
        mpin = FX.pin(doc)
        for cname, cfg in (('none', None), ('legacy', {'r1_training': {}}), ('same', {'r1_training': {'routing_slice_declaration': decl}}),
                           ('moved', {'r1_training': {'routing_slice_declaration': moved}}),
                           ('other', {'r1_training': {'routing_slice_declaration': other}})):
            run('DM|%s|%s' % (cname, tag), lambda: sorted(membership(mpin, False, cfg).sources))
        bad = FX.pin(dict(doc, deferred={}))
        run('DM|deferred_differs|'+tag, lambda: sorted(membership(bad, False, {'r1_training': {'routing_slice_declaration': decl}}).sources))
        nodecl = FX.pin(dict(schema='r1-source-membership-v1', sources=srcs))
        run('DM|undeclared_membership|'+tag, lambda: sorted(membership(nodecl, False, {'r1_training': {'routing_slice_declaration': decl}}).sources))
        notdict = FX.pin(dict(doc, routing_slice_declaration='x'))
        run('DM|decl_not_dict|'+tag, lambda: sorted(membership(notdict, False, {'r1_training': {'routing_slice_declaration': decl}}).sources))


# ---------------------------------------------------------------- real route envelopes
REAL_SPECS = None


def real_cfg(names, *, declare, camera='standin'):
    cfg = copy.deepcopy(ORIG)
    t = cfg['r1_training']
    specs = copy.deepcopy(REAL_SPECS)
    catalog = copy.deepcopy(REAL_CATALOG)
    cam = {'standin': None, 'final': dict(path=str(realmap.FINAL_CAMERA), sha256=realmap.FINAL_SHA),
           'standin_bytes_final_sha': dict(path=str(realmap.STANDIN_CAMERA), sha256=realmap.FINAL_SHA)}[camera]
    if cam is not None:
        specs['camera_wording']['source'] = cam
        catalog['sources']['camera_wording']['source'] = cam
        t['row_slice_inputs'] = dict(t['row_slice_inputs'], camera_wording=cam)
    if declare == 'unprojected':
        t['row_sources'] = FX.pin(specs)
    elif declare == 'legacy_full':
        t['row_sources'] = FX.pin(specs)
    else:
        t['row_sources'] = FX.pin({k: specs[k] for k in names})
    t['source_membership'] = FX.pin(dict(schema='r1-source-catalog-v1', sources={k: catalog['sources'][k] for k in names}))
    for field in ('routing_inputs', 'row_slice_inputs'):
        t[field] = {k: t[field][k] for k in names}
    t['wording_exclusion'] = WORDING
    t['camera_wording_exclusion'] = CAMEX
    cfg['remove_files'] = REMOVE_FILES
    if declare in (True, 'unprojected'):
        t['routing_slice_declaration'] = FX.pin(dict(schema='r1-routing-slices-v1', bound=list(names),
                                                     deferred=reasons(names)))
    if camera == 'standin_bytes_final_sha':
        cfg['_standin_bytes'] = True
    return cfg


COVERAGE_SHAS = None


def isolate_coverage(real_pinned):
    def pinned(pin):
        if isinstance(pin, dict) and pin.get('sha256') in COVERAGE_SHAS:
            return Path(MAPS.get(pin['sha256'], pin['path']))
        return real_pinned(pin)
    return pinned


def maps_for(cfg):
    # The stand-in-bytes case relocates the final hash onto the stand-in file.
    if cfg.get('_standin_bytes'):
        return {**MAPS, realmap.FINAL_SHA: str(realmap.STANDIN_CAMERA)}
    return MAPS


def through_envelopes(cfg, isolate=False):
    def consume(base, sources, batches, cfg, output):
        return [b[0] for b in batches]
    out = TMP/'out'/('real_%05d' % FX.n)
    with r1_persisted.scope(maps_for(cfg)), patch.object(R, 'compose', side_effect=consume):
        if isolate:
            with patch.object(C, 'pinned', isolate_coverage(C.pinned)):
                return R.compose_native(cfg, cfg['streams']['routing'], out)
        return R.compose_native(cfg, cfg['streams']['routing'], out)


def vb_real(cfg, isolate=False):
    with r1_persisted.scope(maps_for(cfg)):
        if isolate:
            with patch.object(C, 'pinned', isolate_coverage(C.pinned)):
                return C.validate_binding(cfg)
        return C.validate_binding(cfg)


def group_real():
    global REAL_SPECS, REAL_CATALOG, COVERAGE_SHAS
    with r1_persisted.scope(MAPS):
        from student_pilot.p3_provenance import pinned
        REAL_SPECS = load(pinned(ORIG['r1_training']['row_sources']))
        REAL_CATALOG = load(pinned(ORIG['r1_training']['source_membership']))
    COVERAGE_SHAS = {REAL_SPECS[k]['source']['sha256'] for k in COVER}
    S3 = SLICES
    for dname, declare in (('legacy', False), ('declared', True)):
        for tag, names in (('s3', S3), ('s3cam', S3+('camera_wording',)), ('s4', FAMILIES[:4]), ('s5', FAMILIES[:5]),
                           ('s6', FAMILIES), ('ad_u', ('absolute_distance', 'units'))):
            for camera in (('standin', 'final', 'standin_bytes_final_sha') if 'camera_wording' in names else ('standin',)):
                for iso in (False, True):
                    cfg = real_cfg(names, declare=declare, camera=camera)
                    key = 'RE|%s|%s|%s|%s' % (dname, tag, camera, 'iso' if iso else 'raw')
                    run(key, lambda: through_envelopes(cfg, iso))
                    run(key.replace('RE|', 'RV|', 1), lambda: vb_real(cfg, iso))
    for camera in ('standin', 'final'):
        cfg = real_cfg(FAMILIES, declare='unprojected', camera=camera)
        run('RE|declared_unprojected|s6|'+camera, lambda: through_envelopes(cfg, True))
        cfg = real_cfg(FAMILIES, declare='legacy_full', camera=camera)
        run('RE|legacy_full_doc|s6|'+camera, lambda: through_envelopes(cfg, True))
    cfg = real_cfg(FAMILIES, declare=True, camera='final')
    cfg['r1_training'].pop('camera_wording_exclusion')
    run('RV|declared|s6|final_no_camera_exclusion', lambda: vb_real(cfg, True))
    cfg = real_cfg(FAMILIES, declare=False, camera='final')
    cfg['r1_training'].pop('camera_wording_exclusion')
    run('RV|legacy|s6|final_no_camera_exclusion', lambda: vb_real(cfg, True))
    orig = copy.deepcopy(ORIG)
    orig['r1_training']['wording_exclusion'] = WORDING
    orig['r1_training']['camera_wording_exclusion'] = CAMEX
    orig['remove_files'] = REMOVE_FILES
    run('RE|original|raw', lambda: through_envelopes(orig, False))
    run('RE|original|iso', lambda: through_envelopes(orig, True))


REAL_CATALOG = None
GROUPS = dict(source_names=group_source_names, validate_binding=group_validate_binding, membership=group_membership,
              compose_legacy=group_compose_legacy, compose_declared=group_compose_declared,
              declarations=group_declarations, real=group_real)
selected = sys.argv[5].split(',') if len(sys.argv) > 5 else list(GROUPS)
meta = dict(tree=str(TREE), label=LABEL, tmp=str(TMP), has_declaration=HAS_DECL, membership_cfg=MEMBERSHIP_CFG,
            camera_pin=C.EXTRA_PINS.get('camera_wording'), removals_local=REMOVALS_LOCAL,
            harness_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            realmap_sha256=hashlib.sha256(Path(realmap.__file__).read_bytes()).hexdigest(), groups=selected)
for g in selected:
    GROUPS[g]()
OUT.write_text(json.dumps(dict(meta=meta, results=RESULTS), indent=0, sort_keys=True)+'\n')
print(LABEL, len(RESULTS), 'cases', json.dumps(meta))
