"""Legacy native composition must refuse before opening the catalog or output."""
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from student_pilot import r1_coverage as C, r1_routing as R
from student_pilot.p3_provenance import file_pin


class LegacyNative(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix='patch_a2_', dir=os.environ.get('TMPDIR')))
        self.serial = 0

    def pin(self, obj):
        self.serial += 1
        p = self.root/(str(self.serial)+'.json')
        p.write_text(json.dumps(obj))
        return file_pin(p)

    def refuse(self, cfg, key):
        output = self.root/'output'
        with patch.object(R, 'load', wraps=R.load) as loads, patch.object(R, 'compose', wraps=R.compose) as compose:
            with self.assertRaises(KeyError) as raised:
                R.compose_native(cfg, {}, output)
            self.assertEqual(raised.exception.args, (key,))
            self.assertEqual(str(raised.exception), repr(key))
            self.assertEqual(loads.call_count, 1)
            self.assertFalse(compose.called)
        self.assertFalse(output.exists())

    def test_deferred_refuses_recovery_before_catalog_or_output(self):
        cfg = dict(r1_training=dict(routing_slices='deferred_first_boundary',
            row_sources=self.pin({}), source_membership=self.pin(dict(sources={}))))
        self.refuse(cfg, 'recovery')

    def test_legacy_missing_routing_inputs_refuses_before_catalog_or_output(self):
        source = self.pin({})
        cfg = dict(r1_training=dict(row_sources=self.pin({k:dict(source=source)
            for k in ('recovery', 'absolute_distance', 'units')})))
        self.refuse(cfg, 'routing_inputs')

    def test_final_camera_pin_is_fixed(self):
        expected = 'e8cbda99f794540c9c0f716d1ae8ce451fd84e473598795c67237fe051acd2d0'
        self.assertEqual(C.EXTRA_PINS['camera_wording'], expected)
        self.assertEqual(C.CAMERA_SOURCE_SHA256, expected)


if __name__ == '__main__':
    unittest.main()
