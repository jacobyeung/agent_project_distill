"""Real envelope binding to the genuine Trinity veto; store assembly is isolated."""
import copy, itertools, json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from student_pilot.p3_provenance import load, pinned, file_pin
from student_pilot.r1_persisted import scope
from student_pilot import r1_routing as R, r1_coverage as C

ROOT = Path(__file__).resolve().parents[2]
RO = ROOT.parent/'ro'
ROUTE = RO/'orch_n30/fb_pack/route'
ORDER = ('absolute_distance','units','coverage_distance','coverage_units','recovery','camera_wording')

def mapped(path):
    path = str(path)
    for old, new in (('/scratch/jjyeung/orch_n30/', RO/'orch_n30'),
                     ('/scratch/jjyeung/n30_mirror/', RO/'n30_mirror')):
        if path.startswith(old) and not path.startswith(str(RO)+'/'):
            path = str(new/path[len(old):]); break
    p = Path(path)
    if p.is_symlink(): return mapped(os.readlink(p))
    return p

class RealRoute(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.maps = {}
        for entry in load(ROUTE/'out/STAGED_INPUTS_FINAL.json')['files']:
            cls.maps[entry['sha256']] = str(mapped(entry['source_path']))
        # Exact supplied provenance supplements the staged hash map.
        for name in ('COMPOSE_RESULT.json','CONFIG_HANDOFF.json','ENVELOPE_INDEX.json'):
            for path, value in load(ROUTE/'out'/name)['inputs'].items():
                p = mapped(path)
                if p.is_file(): cls.maps[value['sha256']] = str(p)
        cls.original = load(ROUTE/'out/config/FIRST_BOUNDARY_CANDIDATE.json')
        with scope(cls.maps):
            cls.specs = load(pinned(cls.original['r1_training']['row_sources']))
            cls.catalog = load(pinned(cls.original['r1_training']['source_membership']))

    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='real_route_', dir=os.environ['TMPDIR']))
        self.serial = 0
        self.context = scope(self.maps); self.context.__enter__(); self.addCleanup(self.context.__exit__, None,None,None)

    def write(self, value):
        self.serial += 1; p = self.root/(str(self.serial)+'.json')
        p.write_text(json.dumps(value)); return file_pin(p)

    def config(self, names):
        cfg = copy.deepcopy(self.original); value = cfg['r1_training']
        value['row_sources'] = self.write({k:self.specs[k] for k in names})
        value['source_membership'] = self.write(dict(schema='r1-source-catalog-v1',
            sources={k:self.catalog['sources'][k] for k in names}))
        for field in ('routing_inputs','row_slice_inputs'):
            value[field] = {k:value[field][k] for k in names}
        value['routing_slice_declaration'] = self.write(dict(schema='r1-routing-slices-v1',
            bound=list(names), deferred={k:('Recovery contract correction pending' if k=='recovery'
                                          else 'Camera re-rendering and validation pending') for k in ORDER if k not in names}))
        return cfg

    def through_envelopes(self, cfg, expected):
        # Only SQLite/base-store assembly is isolated. compose_native, coverage
        # checks, manifest authentication and intake execute unchanged.
        def consume(base, sources, batches, cfg, output):
            return list(batches)
        with patch.object(R, 'compose', side_effect=consume), self.assertRaisesRegex(ValueError, expected):
            R.compose_native(cfg, cfg['streams']['routing'], self.root/'composition')

    def test_four_real_envelopes_reach_genuine_host_veto(self):
        self.through_envelopes(self.config(ORDER[:4]), 'Local slices must contain at most 2000 rows per family')

    def test_four_plus_recovery_reach_genuine_host_veto(self):
        self.through_envelopes(self.config(ORDER[:5]), 'Local slices must contain at most 2000 rows per family')

    def test_camera_standin_pin_reaches_genuine_host_veto(self):
        cfg = self.config(ORDER)
        actual = file_pin(ROUTE/'out/rows/camera_wording.jsonl')
        self.assertEqual(C.EXTRA_PINS['camera_wording'], actual['sha256'])
        self.through_envelopes(cfg, 'Local slices must contain at most 2000 rows per family')

    def test_each_selected_real_envelope_preserves_host_veto(self):
        from student_pilot.r2_intake import intake
        for names in (ORDER[:4], ORDER[:5], ORDER):
            cfg = self.config(names)
            self.assertEqual(C.source_names({k:self.specs[k] for k in names}, cfg), names)
            for name in names:
                pin = cfg['r1_training']['routing_inputs'][name]
                manifest = load(pinned(pin))
                self.assertEqual(manifest['family'], name)
                self.assertEqual(manifest['rows'], cfg['r1_training']['row_slice_inputs'][name])
                with self.subTest(names=names, family=name), self.assertRaisesRegex(ValueError, 'Local slices must contain at most 2000 rows per family'):
                    intake(pinned(pin), limit=None)

    def test_declared_missing_envelope_names_recovery(self):
        cfg = self.config(ORDER[:5]); cfg['r1_training']['routing_inputs'].pop('recovery')
        self.through_envelopes(cfg, 'R1_ROUTING_ENVELOPE_MISSING:recovery')

    def test_undeclared_envelope_names_recovery(self):
        cfg = self.config(ORDER[:4])
        cfg['r1_training']['routing_inputs']['recovery'] = self.original['r1_training']['routing_inputs']['recovery']
        self.through_envelopes(cfg, 'R1_ROUTING_FAMILY_UNDECLARED:recovery:envelope')

    def test_bound_source_and_manifest_refusals_remain(self):
        cfg = self.config(ORDER[:4])
        specs = load(cfg['r1_training']['row_sources']['path']); specs['coverage_units']['source']['sha256'] = '0'*64
        cfg['r1_training']['row_sources'] = self.write(specs)
        self.through_envelopes(cfg, 'R1_COVERAGE_SOURCE_PIN:coverage_units')
        cfg = self.config(ORDER[:4])
        p = cfg['r1_training']['routing_inputs']['absolute_distance']
        envelope = load(pinned(p)); envelope['family'] = 'units'
        cfg['r1_training']['routing_inputs']['absolute_distance'] = self.write(envelope)
        self.through_envelopes(cfg, 'R1_SLICE_MANIFEST_DIFFERS:absolute_distance')

    def test_deferred_build23_declaration_unchanged(self):
        cfg = load(RO/'orch_n30/tree_rebuild10_w/w24/out/N_LAUNCH_CONFIG.json')
        self.assertEqual(cfg['r1_training']['routing_slices'], 'deferred_first_boundary')
        self.assertTrue(C.deferred(cfg))
