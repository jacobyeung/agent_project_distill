"""CPU checks for the scaled-out global batch options; the default batch keeps its exact settings."""
import math
import unittest

from student_pilot import ddp_config, ddp_core


def config(**changes):
    value = {"world_size": 4, "epochs": 1, "seed": 17, "parallel": "fsdp"}
    value.update(changes)
    return value


class BatchOptions(unittest.TestCase):
    def test_default_batch_unchanged(self):
        settings = ddp_config.normalize_training_config(config(), "qwen35")
        self.assertEqual(settings["effective_batch_size"], 32)
        self.assertNotIn("effective_batch_size", ddp_config.FIXED)
        self.assertEqual(ddp_config.DEFAULTS["effective_batch_size"], 32)

    def test_scaled_batches_accepted_when_divisible(self):
        for batch, world in ((64, 8), (128, 16), (128, 32), (256, 32), (256, 16), (256, 8), (64, 32)):
            settings = ddp_config.normalize_training_config(config(world_size=world, effective_batch_size=batch), "qwen35")
            self.assertEqual((settings["effective_batch_size"], settings["world_size"]), (batch, world))

    def test_rejected(self):
        for batch, world in ((256, 24), (128, 12), (48, 4), (512, 32), (16, 4), (32.0, 4), (True, 4)):
            with self.assertRaises(ValueError, msg=(batch, world)):
                ddp_config.normalize_training_config(config(world_size=world, effective_batch_size=batch), "qwen35")

    def test_default_rule_for_world_above_eight(self):
        with self.assertRaises(ValueError):
            ddp_config.normalize_training_config(config(world_size=12), "qwen35")
        ddp_config.normalize_training_config(config(world_size=16), "qwen35")
        ddp_config.normalize_training_config(config(world_size=6), "qwen35")  # padding stays allowed at batch 32

    def test_global_batches_cover_every_row_once(self):
        for rows in (1, 255, 256, 257, 2000):
            for batch in ddp_config.BATCH_OPTIONS:
                windows = list(ddp_core.global_batches(rows, 0, batch, 17))
                self.assertEqual(len(windows), math.ceil(rows / batch))
                self.assertTrue(all(len(window["indices"]) == batch for window in windows))
                covered = sorted(index for window in windows for index in window["indices"][:window["source_rows"]])
                self.assertEqual(covered, list(range(rows)))


class ExactMultiNodeMicrobatch(unittest.TestCase):
    @staticmethod
    def reports(world, fits, seconds):
        return [{"trials": [{"microbatch": size, "fits": fits.get(size, True), "seconds": seconds[size]}
                            for size in sorted(seconds)]} for _ in range(world)]

    def test_exact_size_even_when_slower(self):
        from student_pilot import ddp_checkpoints as checkpoints
        reports = self.reports(32, {}, {1: 1.0, 2: 1.5, 4: 2.0, 8: 4.5})
        self.assertEqual(checkpoints.resumed_microbatch(reports, 32, 256), 4)  # heuristic: 2 x 2.0 < 4.5
        self.assertEqual(checkpoints.resumed_microbatch(reports, 32, 256, exact=True), 8)
        self.assertEqual(checkpoints.resumed_microbatch(reports, 32, 128, exact=True), 4)

    def test_exact_size_must_fit_everywhere(self):
        from student_pilot import ddp_checkpoints as checkpoints
        reports = self.reports(32, {}, {1: 1.0, 2: 1.5, 4: 2.0, 8: 4.5})
        reports[7]["trials"][-1]["fits"] = False
        with self.assertRaises(ValueError):
            checkpoints.resumed_microbatch(reports, 32, 256, exact=True)
        with self.assertRaises(ValueError):
            checkpoints.resumed_microbatch(self.reports(16, {}, {1: 1.0, 2: 1.5}), 16, 256, exact=True)

    def test_exact_resume(self):
        from student_pilot import ddp_checkpoints as checkpoints
        reports = self.reports(16, {}, {1: 1.0, 2: 1.5, 4: 2.0, 8: 4.5})
        self.assertEqual(checkpoints.resumed_microbatch(reports, 16, 128, {"state": {"microbatch_size": 8}}, exact=True), 8)
        with self.assertRaises(ValueError):
            checkpoints.resumed_microbatch(reports, 16, 128, {"state": {"microbatch_size": 4}}, exact=True)


class EightNodeLimits(unittest.TestCase):
    def test_world_64_accepted_only_with_a_dividing_batch(self):
        for batch in (64, 128, 256):
            settings = ddp_config.normalize_training_config(config(world_size=64, effective_batch_size=batch), "qwen35")
            self.assertEqual(settings["world_size"], 64)
        for world, batch in ((65, 256), (64, 32), (48, 256)):
            with self.assertRaises(ValueError, msg=(world, batch)):
                ddp_config.normalize_training_config(config(world_size=world, effective_batch_size=batch), "qwen35")

    def test_rank_topology_up_to_eight_hosts(self):
        from student_pilot.ddp_admission import rank_topology
        ranks = [{"host": f"node{index // 8}"} for index in range(64)]
        self.assertEqual(rank_topology(ranks)["nnodes"], 8)
        with self.assertRaises(ValueError):
            rank_topology([{"host": f"node{index // 8}"} for index in range(72)])


if __name__ == "__main__":
    unittest.main()
