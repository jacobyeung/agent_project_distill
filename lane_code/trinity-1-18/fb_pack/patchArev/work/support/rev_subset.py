"""Subset/ordering checks and legacy outcome probes; outcomes are written per tree for a base/new diff."""
from copy import deepcopy
import itertools
import json
import os
from pathlib import Path
import random
import sqlite3
import unittest

TREE = Path(os.environ['REVIEW_TREE'])
W = Path(__file__).resolve().parents[1]
FAMILIES = ('absolute_distance', 'units', 'coverage_distance', 'coverage_units', 'recovery', 'camera_wording')
REAL = {'coverage_units': '/scratch/jjyeung/orch_n30/fb_pack/route/u/8ec1efd2c1851fb856caa3631653390d76796f8c31cd8366d54df52916c7de82',
        'coverage_distance': '/scratch/jjyeung/orch_n30/fb_pack/route/u/15387646fd4ac47b43c107129db3109545a981c1bd45a3910ac038d8c5432022',
        'camera_wording': '/scratch/jjyeung/orch_n30/fb_pack/route/u/31914ba5470c1b5b7fac4ba52a13482cb6ce2965a732b69f6f57a55ed1fbe814'}


def outcome(fn):
    try:
        value = fn()
        return ['OK', value if isinstance(value, (str, int, bool, type(None))) else list(value) if isinstance(value, tuple) else repr(value)[:200]]
    except Exception as error:
        return [type(error).__name__, str(error)[:200]]


class Probe(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from student_pilot.p3_provenance import file_pin
        cls.file_pin = staticmethod(file_pin)
        cls.root = Path(os.environ['TMPDIR'])/'probe'
        cls.root.mkdir()
        cls.serial = 0
        cls.legacy, cls.declared = {}, {}

    @classmethod
    def tearDownClass(cls):
        (W/'results').mkdir(exist_ok=True)
        (W/'results'/('probe_cases_'+TREE.name+'.json')).write_text(json.dumps(dict(legacy=cls.legacy, declared=cls.declared), indent=0, sort_keys=True)+'\n')

    def write(self, value, name='doc'):
        type(self).serial += 1
        path = self.root/f'{self.serial:05d}_{name}.json'
        path.write_text(json.dumps(value))
        return self.file_pin(path)

    def declaration(self, bound, **extra):
        value = dict(schema='r1-routing-slices-v1', bound=list(bound),
                     deferred={k: 'Awaiting validated rows' for k in FAMILIES if k not in bound})
        value.update(extra)
        return dict(r1_training=dict(routing_slice_declaration=self.write(value, 'decl')))

    def tiny(self, cfg):
        from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
        db = sqlite3.connect(':memory:'); db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)'); db.commit()
        path = self.root/f'base_{self.serial}.sqlite'; path.write_bytes(db.serialize()); db.close()
        cfg.update(dev_scene_exclusions=self.write(dict(schema='dev_s1_withhold_v1', natives=['d1/dev'], rooms=['d1/dev'],
                       physical_groups=['scannet/dev'], canonical={'d1/dev': ['scannet/dev']}, aliases={'d1/dev': ['d1/vdev']})),
                   benchmark_scene_exclusions=self.write(dict(schema='benchmark_scene_exclusions_v1', scenes=['d1/benchmark'])))
        division = self.write(dict(train_scenes=['d1/clean'], heldout_scenes=['d1/held']))
        return self.write(dict(schema=ROUTING_SCHEMA, stream='routing', database=self.file_pin(path), count=0,
                               division=division, scene_role='train', heldout_overlap=0))

    def test_legacy_source_names(self):
        from student_pilot import r1_coverage as C
        keys = FAMILIES + ('room', 'foreign')
        cfgs = dict(none=None, empty={}, no_r1=dict(r1_training={}), deferred=dict(r1_training=dict(routing_slices='deferred_first_boundary')),
                    other_flag=dict(r1_training=dict(routing_slices='other')))
        for n in range(len(keys)+1):
            for names in itertools.combinations(keys, n):
                for label, cfg in cfgs.items():
                    self.legacy['source_names:'+label+':'+','.join(names)] = outcome(lambda: C.source_names(dict.fromkeys(names, {}), deepcopy(cfg)))

    def test_legacy_validate_binding_and_membership(self):
        from student_pilot import r1_coverage as C
        from student_pilot.r1_population import Membership
        src = {k: self.file_pin(Path(v)) for k, v in REAL.items()}
        tiny = self.write({}, 'src')
        for n in range(4):
            for names in itertools.combinations(('coverage_units', 'coverage_distance', 'camera_wording'), n):
                rows = {k: dict(source=src[k]) for k in names}
                rows.update({k: dict(source=tiny) for k in ('absolute_distance', 'units', 'recovery')})
                cfg = dict(r1_training=dict(row_sources=self.write(rows, 'rows')))
                self.legacy['validate_binding:'+','.join(names)] = outcome(lambda: C.validate_binding(cfg))
                member = self.write(dict(schema='r1-source-membership-v1', sources={k: dict(source=v['source'], rows={}) for k, v in rows.items()}))
                self.legacy['membership:none:'+','.join(names)] = outcome(lambda: sorted(Membership(member).sources))
                self.legacy['membership:cfg:'+','.join(names)] = outcome(lambda: sorted(Membership(member, cfg=dict(r1_training={})).sources))

    def test_legacy_compose_native(self):
        from student_pilot.r1_routing import compose_native
        tiny = self.write({}, 'src')
        for label, flag in (('deferred', {'routing_slices': 'deferred_first_boundary'}), ('full', {})):
            names = () if flag else ('recovery', 'absolute_distance', 'units')
            cfg = dict(r1_training=dict(flag, row_sources=self.write({k: dict(source=tiny) for k in names}),
                       source_membership=self.write(dict(schema='r1-source-catalog-v1', sources={k: dict(source=tiny, qids=[]) for k in names}))))
            base = self.tiny(cfg)
            out = self.root/('compose_'+label)
            self.legacy['compose_native_without_routing_inputs:'+label] = outcome(lambda: sorted(compose_native(cfg, base, out)))
            self.legacy['compose_native_without_routing_inputs:'+label+':outputs'] = sorted(p.name for p in out.glob('*')) if out.exists() else None

    def test_declared_subsets_any_order(self):
        from student_pilot import r1_coverage as C
        rng = random.Random(0)
        for n in range(7):
            for names in itertools.combinations(FAMILIES, n):
                key = ','.join(names)
                results = set()
                for trial in range(4):
                    bound = list(names); rng.shuffle(bound)
                    order = list(names) + (['room', 'room_programs_excluded'] if trial % 2 else []); rng.shuffle(order)
                    cfg = self.declaration(bound)
                    results.add(tuple(outcome(lambda: C.source_names({k: {} for k in order}, cfg))[1]))
                self.declared['order:'+key] = sorted(map(list, results))
                cfg = self.declaration(names)
                for f in FAMILIES:
                    if f in names:
                        self.declared['missing:'+key+':'+f] = outcome(lambda: C.source_names({k: {} for k in names if k != f}, cfg))
                        both = dict(schema='r1-routing-slices-v1', bound=list(names),
                                    deferred={k: 'r' for k in FAMILIES if k not in names} | {f: 'r'})
                        self.declared['overlap:'+key+':'+f] = outcome(lambda: C.source_names({k: {} for k in names},
                            dict(r1_training=dict(routing_slice_declaration=self.write(both)))))
                    else:
                        self.declared['undeclared:'+key+':'+f] = outcome(lambda: C.source_names({k: {} for k in names + (f,)}, cfg))
                        gap = dict(schema='r1-routing-slices-v1', bound=list(names),
                                   deferred={k: 'r' for k in FAMILIES if k not in names and k != f})
                        self.declared['gap:'+key+':'+f] = outcome(lambda: C.source_names({k: {} for k in names},
                            dict(r1_training=dict(routing_slice_declaration=self.write(gap)))))
                        for bad in ('', ' ', None, 1, ['x']):
                            value = dict(schema='r1-routing-slices-v1', bound=list(names),
                                         deferred={k: 'r' for k in FAMILIES if k not in names} | {f: bad})
                            self.declared['reason:'+key+':'+f+':'+repr(bad)] = outcome(lambda: C.source_names({k: {} for k in names},
                                dict(r1_training=dict(routing_slice_declaration=self.write(value)))))

    def test_declared_shape_and_identity(self):
        from student_pilot import r1_coverage as C
        good = dict(schema='r1-routing-slices-v1', bound=list(FAMILIES[:4]), deferred={'recovery': 'r', 'camera_wording': 'r'})
        variants = dict(extra_key=dict(good, note='x'), schema=dict(good, schema='r1-routing-slices-v2'), bound_dict=dict(good, bound={}),
                        bound_int=dict(good, bound=[1]), deferred_list=dict(good, deferred=[]), duplicate=dict(good, bound=good['bound']+['units']),
                        foreign_bound=dict(good, bound=good['bound']+['foreign']), foreign_deferred=dict(good, deferred=dict(good['deferred'], foreign='r')),
                        not_dict=[1], good=good)
        for name, value in variants.items():
            self.declared['shape:'+name] = outcome(lambda: C.source_names({k: {} for k in FAMILIES[:4]},
                dict(r1_training=dict(routing_slice_declaration=self.write(value)))))
        pin = self.write(good)
        for name, p in dict(changed_sha=dict(pin, sha256='0'*64), extra_field=dict(pin, size=1), missing=dict(path=str(self.root/'absent.json'), sha256=pin['sha256'])).items():
            self.declared['pin:'+name] = outcome(lambda: C.source_names({k: {} for k in FAMILIES[:4]}, dict(r1_training=dict(routing_slice_declaration=p))))
        self.declared['deferred_flag_plus_declaration'] = outcome(lambda: C.deferred(dict(r1_training=dict(routing_slices='deferred_first_boundary', routing_slice_declaration=pin))))
        from student_pilot.carrier_c1_run import identity
        base = dict(schema='x', r1_training=dict(row_sources=pin))
        a = deepcopy(base); a['r1_training']['routing_slice_declaration'] = pin
        b = deepcopy(base); b['r1_training']['routing_slice_declaration'] = self.write(dict(good, bound=list(FAMILIES[:5]), deferred={'camera_wording': 'r'}))
        self.declared['identity_distinct'] = len({identity(base), identity(a), identity(b)}) == 3

    def test_declared_membership(self):
        from student_pilot.r1_population import Membership
        from student_pilot.p3_provenance import load
        cfg = self.declaration(FAMILIES[:4]); decl = cfg['r1_training']['routing_slice_declaration']
        tiny = self.write({}, 'src')
        def member(sources=FAMILIES[:4], declaration=decl, deferred=None):
            value = dict(schema='r1-source-membership-v1', sources={k: dict(source=tiny, rows={}) for k in sources})
            if declaration is not None:
                value.update(routing_slice_declaration=declaration, deferred=load(decl['path'])['deferred'] if deferred is None else deferred)
            return self.write(value, 'member')
        other = self.declaration(FAMILIES[:4])['r1_training']['routing_slice_declaration']
        relocated = self.write(load(decl['path']), 'decl_copy')
        cases = dict(cfg_match=(member(), cfg), cfg_none=(member(), None), cfg_legacy=(member(), dict(r1_training={})),
                     cfg_other_reason_same_bound=(member(), dict(r1_training=dict(routing_slice_declaration=self.write(dict(schema='r1-routing-slices-v1', bound=list(FAMILIES[:4]), deferred={'recovery': 'other', 'camera_wording': 'r'}))))),
                     cfg_relocated=(member(), dict(r1_training=dict(routing_slice_declaration=relocated))),
                     legacy_member_declared_cfg=(member(declaration=None), cfg), deferred_differs=(member(deferred={}), cfg),
                     extra_source=(member(sources=FAMILIES[:5]), cfg), missing_source=(member(sources=FAMILIES[:3]), cfg),
                     none_cfg_extra_source=(member(sources=FAMILIES[:5]), None), copy_of_other=(member(), dict(r1_training=dict(routing_slice_declaration=other))))
        for name, (pin, c) in cases.items():
            self.declared['membership:'+name] = outcome(lambda: sorted(Membership(pin, cfg=c).sources))


if __name__ == '__main__':
    unittest.main()
