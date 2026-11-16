import unittest

import numpy as np

from generator.derivgen_v7.derivgen import room_v314 as generator
from trace_format import room_v314 as runtime


class RoomFormattingTests(unittest.TestCase):
    def result(self, height):
        return dict(frames=[1, 3], floor_height_m=height, floor_cells=400,
                    supported_cells=400, min_frames=2, area_m2=1.)

    def test_generator_and_runtime_share_one_formatter(self):
        self.assertIs(generator.format_result, runtime.format_result)

    def test_rounded_zero_is_positive(self):
        for height in (-0., -0.0049, -0.000001, 0., 0.000001):
            for module in (runtime, generator):
                body = module.format_result(self.result(height))
                self.assertIn("floor height 0.00 m\n", body)
                self.assertNotIn("-0.00", body)
                self.assertEqual(module.parse_response(body)["floor_height_m"], 0.)

    def test_nonzero_height_and_area_do_not_change(self):
        for height, printed in ((-0.0051, "-0.01"), (0.0051, "0.01"), (-1.234, "-1.23")):
            body = runtime.format_result(self.result(height))
            self.assertIn("floor height "+printed+" m\n", body)
            self.assertTrue(body.endswith("area 1.00 m^2"))
            self.assertEqual(body, generator.format_result(self.result(height)))

    def test_native_kernel_roundoff_prints_canonically(self):
        x, y = np.meshgrid(np.linspace(0, 1, 20), np.linspace(0, 1, 20))
        points = np.column_stack((x.ravel(), y.ravel(), np.full(x.size, np.float32(.09999999))))
        result = runtime.from_points([points, points], [1, 3], "predicted", gravity_source="fixture")
        self.assertLess(result["floor_height_m"], 0.)
        self.assertIn("floor height 0.00 m\n", runtime.format_result(result))


if __name__ == "__main__":
    unittest.main()
