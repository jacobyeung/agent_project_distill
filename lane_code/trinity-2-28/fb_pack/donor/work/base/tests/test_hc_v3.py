"""HC/HX v3 configs (tools/hc_v3.py): PDG v3's stage-2 config with only the init, init modules and headcall block
changed; HC and HX differ only in the headcall block; the smokes derive from the smoke stage-2 config."""
import copy
import json
import unittest
from pathlib import Path

from tools import hc_v3, pdg_v3

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "pdg_v3" / "pdg_s2_v2_config.json"


def pin(name):
    return {"path": f"/project/community/jjyeung/fixture/{name}", "sha256": (name.encode().hex() * 64)[:64]}


def stage2(smoke=False):
    config = pdg_v3.stage2_config(json.loads(FIXTURE.read_text()), pin("s1_geometry.safetensors"), pin("s1_heads.pt"))
    return pdg_v3.smoke_config(config) if smoke else config


INIT = {"full_weights": pin("full_weights.json"), "geometry": pin("geometry_projector.safetensors"),
        "heads": pin("auxiliary_heads.pt")}
SIDECARS = {"HC": {"path": "/project/community/jjyeung/ap_shared/hc/542f552b3120.jsonl.gz", "sha256": "5" * 64},
            "HX": {"path": "/project/community/jjyeung/ap_shared/hc/f42c40c9a80d.jsonl.gz", "sha256": "f" * 64}}


class HcV3ConfigTests(unittest.TestCase):
    def test_arms_change_only_init_modules_and_headcall(self):
        base = stage2()
        configs = hc_v3.pair(base, SIDECARS, INIT)
        for arm, config in configs.items():
            changed = hc_v3.config_changes(base, config)
            self.assertTrue(all(key.startswith(hc_v3.ARM_PREFIXES) or key in hc_v3.ARM_FIELDS for key in changed), changed)
            self.assertEqual(config["full_ft"]["init"], {"kind": "full_export", **INIT["full_weights"]})
            self.assertEqual(config["full_ft"]["init_modules"], {"geometry": INIT["geometry"], "heads": INIT["heads"]})
            self.assertEqual(config["geometry"], base["geometry"])
            self.assertEqual(config["camera"], base["camera"])
            self.assertEqual(config["full_ft"]["learning_rates"], hc_v3.STAGE2_RATES)
            self.assertEqual((config["world_size"], config["effective_batch_size"], config["seed"]), (32, 256, 17))
            self.assertEqual(config["headcall"]["arm"], arm)
        self.assertEqual(configs["HC"]["headcall"]["scheduled_sampling"], {**hc_v3.SAMPLING, "seed": 17})
        self.assertIsNone(configs["HX"]["headcall"]["scheduled_sampling"])
        self.assertTrue(all(key.startswith("headcall.") for key in hc_v3.config_changes(configs["HC"], configs["HX"])))

    def test_smoke_samples_from_step_0_and_checkpoints_at_25(self):
        configs = hc_v3.pair(stage2(smoke=True), SIDECARS, INIT, smoke=True)
        self.assertEqual(configs["HC"]["headcall"]["scheduled_sampling"]["end_step"], 20)
        self.assertEqual(configs["HC"]["checkpoint_every_steps"], 25)
        self.assertEqual(configs["HX"]["max_steps"], 30)
        with self.assertRaisesRegex(ValueError, "smoke stage-2 config"):
            hc_v3.pair(stage2(), SIDECARS, INIT, smoke=True)

    def test_refuses_other_sources(self):
        base = stage2()
        ungated = json.loads(FIXTURE.read_text())
        with self.assertRaisesRegex(ValueError, "gated G3T connector"):
            hc_v3.arm_config(ungated, "HC", SIDECARS["HC"], INIT)
        heavy = copy.deepcopy(base)
        heavy["camera"]["weight"] = 1.0
        with self.assertRaisesRegex(ValueError, "head weights"):
            hc_v3.arm_config(heavy, "HC", SIDECARS["HC"], INIT)
        with self.assertRaisesRegex(ValueError, "arm must be"):
            hc_v3.arm_config(base, "HA", SIDECARS["HC"], INIT)

    def test_g3t_prior_pins_camera_sidecar_store_on_both_arms(self):
        base = stage2()
        cam_store = pin("camera_manifest.jsonl")
        configs = hc_v3.pair(base, SIDECARS, {**INIT, "camera_store": cam_store, "g3t_prior": True})
        for arm, config in configs.items():
            self.assertTrue(config["camera"]["g3t_prior"], arm)
            self.assertEqual(config["geometry"]["store"]["camera_manifest"], cam_store["path"], arm)
            self.assertEqual(config["geometry"]["store"]["camera_manifest_sha256"], cam_store["sha256"], arm)
            changed = hc_v3.config_changes(base, config)
            self.assertTrue(all(key.startswith(hc_v3.ARM_PREFIXES) or key in hc_v3.ARM_FIELDS for key in changed), changed)


if __name__ == "__main__":
    unittest.main()
