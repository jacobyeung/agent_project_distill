import copy
from pathlib import Path
import unittest

from student_pilot import carrier_c1_data as data
from student_pilot.carrier_c1_sweep import recipe_for
from student_pilot.p3_provenance import load
from tests.test_orchard_w4 import configuration


class WorldFourTests(unittest.TestCase):
    def test_world_four_preserves_global_row_order_and_optimizer_step_size(self):
        template = load(Path(__file__).resolve().parents[1] / "configs/stageb_cp1rv_mdg_w4.json")
        cfg = configuration(8)
        cfg.update(mdg=template["mdg"], mix=template["mix"], steps=200, milestones=[1, 100, 200])
        eight = recipe_for(cfg)
        four = recipe_for({**copy.deepcopy(cfg), "world_size": 4})
        self.assertEqual(eight["global_batch"], four["global_batch"])
        self.assertEqual(len(four["mix"]), 2*len(eight["mix"]))
        self.assertEqual(eight["milestones"], four["milestones"])
        counts = {stream: 113 for stream in cfg["mix"]}
        plans = []
        for recipe in (four, eight):
            value = data.mixed_indices(counts, 3, training_mode="final",
                                       mix=recipe["mix"], world=recipe["world_size"])
            plans.append([[(stream, int(index)) for stream, indices in plan for index in indices]
                          for plan in value])
        self.assertEqual(plans[0], plans[1])


if __name__ == "__main__":
    unittest.main()
