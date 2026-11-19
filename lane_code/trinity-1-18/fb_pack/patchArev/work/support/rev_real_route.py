"""Real route envelopes, catalogs, removals and exclusions through compose_native on this Trinity node.

Only the routing base is a stand-in (its database and division exist only on the frame host); hostname,
environment, intake and admission are the tree's own. Each case records the refusal it reaches.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sqlite3
import traceback
import unittest

ROUTE = Path('/scratch/jjyeung/orch_n30/fb_pack/route/out')
TREE = Path(os.environ['REVIEW_TREE'])
W = Path(__file__).resolve().parents[1]
FOUR = ('absolute_distance', 'units', 'coverage_distance', 'coverage_units')
FIVE = FOUR + ('recovery',)
SIX = FIVE + ('camera_wording',)
VETO = 'Local slices must contain at most 2000 rows per family'


def read(path):
    return json.loads(Path(path).read_text())


class RealRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from student_pilot.p3_provenance import file_pin
        cls.file_pin = staticmethod(file_pin)
        cls.root = Path(os.environ['TMPDIR']) / 'real_route'
        cls.root.mkdir()
        cls.serial = 0
        cls.maps = read(ROUTE/'STAGED_INPUTS_FINAL.json')['paths']
        cfg = read(ROUTE/'config/FIRST_BOUNDARY_CANDIDATE.json')
        for field, value in read(ROUTE/'CONFIG_HANDOFF.json')['fields'].items():
            if field.startswith('cfg.'):
                target = cfg
                *parents, leaf = field[4:].split('.')
                for p in parents:
                    target = target[p]
                target[leaf] = value
        cls.cfg = cfg
        cls.row_sources = read(cfg['r1_training']['row_sources']['path'])
        cls.catalog = read(cfg['r1_training']['source_membership']['path'])
        cls.base = cls.stand_in_base()
        cls.results = {}

    @classmethod
    def write(cls, value, name='doc'):
        cls.serial += 1
        path = cls.root / f'{cls.serial:03d}_{name}.json'
        path.write_text(json.dumps(value))
        return cls.file_pin(path)

    @classmethod
    def stand_in_base(cls):
        from student_pilot.carrier_c1_routing import ROUTING_SCHEMA
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE rows(i INTEGER PRIMARY KEY,row TEXT,target TEXT)')
        db.commit()
        (cls.root/'base.sqlite').write_bytes(db.serialize()); db.close()
        division = cls.write(dict(train_scenes=['stand_in/train'], heldout_scenes=['stand_in/held']), 'division')
        return cls.write(dict(schema=ROUTING_SCHEMA, stream='routing', database=cls.file_pin(cls.root/'base.sqlite'),
                              count=0, division=division, scene_role='train', heldout_overlap=0), 'base')

    def config(self, bound, *, declare=True, reasons=None, project=('row_sources', 'catalog', 'routing_inputs', 'row_slice_inputs')):
        cfg = deepcopy(self.cfg)
        value = cfg['r1_training']
        if 'row_sources' in project:
            value['row_sources'] = self.write({k: self.row_sources[k] for k in bound}, 'row_sources')
        if 'catalog' in project:
            value['source_membership'] = self.write(dict(schema=self.catalog['schema'],
                sources={k: self.catalog['sources'][k] for k in bound}), 'catalog')
        for field in ('routing_inputs', 'row_slice_inputs'):
            if field in project:
                value[field] = {k: value[field][k] for k in bound}
        if declare:
            deferred = {k: 'Awaiting validated rows' for k in SIX if k not in bound}
            deferred.update(reasons or {})
            value['routing_slice_declaration'] = self.write(dict(schema='r1-routing-slices-v1', bound=list(bound),
                                                                 deferred=deferred), 'declaration')
        return cfg

    def run_case(self, name, cfg, env=None):
        from student_pilot.r1_persisted import scope
        from student_pilot.r1_routing import compose_native
        saved = {k: os.environ.get(k) for k in (env or {})}
        os.environ.update(env or {})
        during = {k: os.environ.get(k) for k in ('STUDENT_R2_FRAME_HOST', 'STUDENT_R2_LOCAL_NODE', 'Q_E7', 'Q_E8')}
        try:
            with scope(self.maps):
                compose_native(cfg, self.base, self.root/('out_'+name))
            outcome = dict(status='RETURNED')
        except Exception as error:
            frames = traceback.extract_tb(error.__traceback__)
            outcome = dict(status='REFUSED', exception=type(error).__name__, message=str(error)[:300],
                           last_frame=f'{Path(frames[-1].filename).name}:{frames[-1].lineno}:{frames[-1].name}',
                           intake_frames=[f'{Path(f.filename).name}:{f.lineno}' for f in frames if f.name == 'batches'])
        finally:
            for k, v in saved.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v
        outcome.update(hostname=os.uname().nodename, environment=during,
                       outputs=sorted(p.name for p in (self.root/('out_'+name)).glob('*')) if (self.root/('out_'+name)).exists() else None)
        self.results[name] = outcome
        return outcome

    def test_cases(self):
        c = self.config
        cases = dict(
            four=c(FOUR), five=c(FIVE), six=c(SIX),
            legacy_six=c(SIX, declare=False, project=()),
            **{'single_'+k: c((k,)) for k in SIX},
            four_qe7_set=c(FOUR),
            four_with_recovery_envelope=c(FOUR), five_missing_recovery_envelope=c(FIVE),
            five_changed_recovery_envelope=c(FIVE),
            four_unprojected_row_sources=c(FOUR, project=('catalog', 'routing_inputs', 'row_slice_inputs')),
            four_unprojected_catalog=c(FOUR, project=('row_sources', 'routing_inputs', 'row_slice_inputs')),
            four_unprojected_staged=c(FOUR, project=('row_sources', 'catalog', 'routing_inputs')),
            four_coverage_units_wrong_source=c(FOUR), four_swapped_envelope=c(FOUR),
            four_no_wording_exclusion=c(FOUR), six_no_camera_exclusion=c(SIX),
            four_with_deferred_flag=c(FOUR), four_removal_order=c(FOUR),
            five_empty_reason=c(FIVE, reasons={'camera_wording': ' '}),
        )
        ri = lambda k: cases[k]['r1_training']['routing_inputs']
        ri('four_with_recovery_envelope')['recovery'] = self.cfg['r1_training']['routing_inputs']['recovery']
        ri('five_missing_recovery_envelope').pop('recovery')
        ri('five_changed_recovery_envelope')['recovery'] = dict(ri('five_changed_recovery_envelope')['recovery'], sha256='0'*64)
        ri('four_swapped_envelope')['absolute_distance'] = self.cfg['r1_training']['routing_inputs']['units']
        bad = {k: deepcopy(self.row_sources[k]) for k in FOUR}
        bad['coverage_units']['source'] = self.row_sources['coverage_distance']['source']
        cases['four_coverage_units_wrong_source']['r1_training']['row_sources'] = self.write(bad, 'row_sources_bad')
        cases['four_no_wording_exclusion']['r1_training'].pop('wording_exclusion')
        cases['six_no_camera_exclusion']['r1_training'].pop('camera_wording_exclusion')
        cases['four_with_deferred_flag']['r1_training']['routing_slices'] = 'deferred_first_boundary'
        files = cases['four_removal_order']['remove_files']
        files[0], files[1] = files[1], files[0]
        for name, cfg in cases.items():
            self.run_case(name, cfg, env={'Q_E7': '1'} if name == 'four_qe7_set' else None)
        label = TREE.name
        (W/'results'/('real_route_cases_'+label+'.json')).parent.mkdir(exist_ok=True)
        (W/'results'/('real_route_cases_'+label+'.json')).write_text(json.dumps(self.results, indent=1)+'\n')


if __name__ == '__main__':
    unittest.main()
