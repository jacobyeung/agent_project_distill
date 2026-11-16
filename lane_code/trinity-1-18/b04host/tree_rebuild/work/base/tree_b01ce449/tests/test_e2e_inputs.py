"""Explicit real-row admission gate; unavailable inputs never trigger a fetch."""
import json
import os
from pathlib import Path
import unittest

from tests.test_e2e_merge import config


def required(cfg):
    paths = []
    def pins(value):
        if isinstance(value, dict):
            if set(value) == {'path', 'sha256'}:
                paths.append(value['path'])
            else:
                for item in value.values():
                    pins(item)
        elif isinstance(value, list):
            for item in value:
                pins(item)
    pins(cfg)
    paths.extend(cfg['mdg'][key] for key in ('frame_root', 'rasters'))
    paths.extend(str(Path(cfg['mdg']['init_artifact']) / name) for name in ('mdg.json', 'mdg.pt'))
    paths.append(str(Path(cfg['preparation_output']) / 'receipt.json'))
    return sorted(set(paths))


class RealRows(unittest.TestCase):
    def test_real_rows_first_batch_for_each_variant(self):
        from student_pilot import carrier_c1_run as run
        pending = False
        for variant in ('E2E-1G', 'E2E-1C'):
            cfg = config(variant)
            paths = required(cfg)
            missing = [path for path in paths if not Path(path).exists()]
            report = dict(status='PENDING-INPUT' if missing else 'INPUTS-PRESENT',
                          variant=variant, required=paths, missing=missing,
                          unbound=cfg['unbound'])
            pending = pending or bool(missing or cfg['unbound'])
            root = Path(os.environ['LANE_TEST_OUTPUT'])
            (root / (variant + '_real_inputs.json')).write_text(json.dumps(report, indent=2) + '\n')
        # Both config reports are emitted before the test reports its missing inputs.
        if pending:
            self.skipTest('PENDING-INPUT: exact paths in E2E-1G_real_inputs.json and E2E-1C_real_inputs.json')
        for variant in ('E2E-1G', 'E2E-1C'):
            cfg = config(variant)
            records = run.first_batch_check(cfg, [0, 1, 2, 3], root / (variant + '_real_first_batch.json'))
            self.assertTrue(all(record['finite'] for record in records))
            self.assertEqual({record['stream'] for record in records}, set(cfg['streams']))
