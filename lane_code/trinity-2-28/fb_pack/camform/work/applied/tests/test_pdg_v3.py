"""PDG v3 (tools/pdg_v3.py, gated connector): the gated connector starts at zero, its delta norm is tanh(gate) * sqrt(width),
its init loads through init_modules as an exact no-op, and the stage-1 / stage-2 / smoke configs change only their recipe
fields."""
import copy
import json
import math
import tempfile
import unittest
from pathlib import Path

import torch

from student_pilot import full_ft, geometry_input
from tools import pdg_v3

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pdg_v3"


def load(name):
    return json.loads((FIXTURES / name).read_text())


def small_settings():
    settings = copy.deepcopy(load("pdg_s1_config.json")["geometry"])
    settings["feature_dim"] = 4  # merged width 32 keeps the toy connector small
    return geometry_input.normalize(settings)


class GatedConnector(unittest.TestCase):
    def test_zero_at_init_and_bounded_norm(self):
        settings = pdg_v3.gated_block(small_settings())
        module = geometry_input.GeometryInput(settings, 16)
        self.assertIsInstance(module.projector, geometry_input.GatedSpatialMLLMConnector)
        features = torch.randn(7, geometry_input.token_width(settings))
        self.assertEqual(int(module.projector(features).count_nonzero()), 0)
        with torch.no_grad():
            module.projector.fc2.weight.mul_(1000.0)  # toy widths: lift the output variance far above the LayerNorm eps
        for gate in (1e-3, 0.05, -0.3, 2.0):
            with torch.no_grad():
                module.projector.gate.fill_(gate)
                module.projector.fc2.weight.mul_(10.0)  # the connector's own scale does not move the delta norm
            norms = module.projector(features).norm(dim=-1)
            self.assertTrue(torch.allclose(norms, torch.full_like(norms, abs(math.tanh(gate)) * 4.0), rtol=1e-4))

    def test_step1_gradient_reaches_only_the_gate(self):
        settings = pdg_v3.gated_block(small_settings())
        module = geometry_input.GeometryInput(settings, 16)
        features = torch.randn(7, geometry_input.token_width(settings))
        (module.projector(features) * torch.randn(7, 16)).sum().backward()
        grads = {name: p.grad for name, p in module.projector.named_parameters()}
        self.assertGreater(float(grads["gate"].abs().sum()), 0)
        for name, grad in grads.items():
            self.assertIsNotNone(grad, name)
            if name != "gate":
                self.assertEqual(int(grad.count_nonzero()), 0, name)

    def test_same_draws_as_the_source_connector(self):
        torch.manual_seed(3)
        plain = geometry_input.SpatialMLLMConnector(4, 16).state_dict()
        torch.manual_seed(3)
        gated = geometry_input.GatedSpatialMLLMConnector(4, 16).state_dict()
        self.assertEqual(set(gated) - set(plain), {"gate"})
        self.assertTrue(all(torch.equal(plain[k], gated[k]) for k in plain))

    def test_old_spatial_block_unchanged(self):
        settings = small_settings()
        self.assertEqual(settings["injection"], geometry_input.SPATIAL_INJECTION)
        module = geometry_input.GeometryInput(settings, 16)
        self.assertIs(type(module.projector), geometry_input.SpatialMLLMConnector)
        self.assertNotIn("gate", module.projector.state_dict())

    def test_gated_block_shares_the_store_layout(self):
        plain, gated = small_settings(), pdg_v3.gated_block(small_settings())
        self.assertEqual(geometry_input.token_width(plain), geometry_input.token_width(gated))
        self.assertEqual(geometry_input.store_grid(plain, [16, 20, 26]), geometry_input.store_grid(gated, [16, 20, 26]))
        self.assertEqual({k: v for k, v in gated.items() if k not in ("injection", "projector")},
                         {k: v for k, v in plain.items() if k not in ("injection", "projector")})
        mixed = {**gated, "projector": dict(geometry_input.SPATIAL_MLLM)}
        with self.assertRaisesRegex(ValueError, "projector"):
            geometry_input.normalize(mixed)


class GatedInit(unittest.TestCase):
    def test_state_is_source_init_with_zero_gate(self):
        state = pdg_v3.gated_init_state(4, 16, seed=17)
        self.assertEqual(set(state), {"ln_q.weight", "mlp.0.weight", "mlp.0.bias", "mlp.2.weight", "mlp.2.bias", "gate"})
        self.assertTrue(all(value.dtype == torch.float32 for value in state.values()))
        self.assertTrue(torch.equal(state["gate"], torch.zeros(1)))
        self.assertEqual(int(state["mlp.0.bias"].count_nonzero()) + int(state["mlp.2.bias"].count_nonzero()), 0)
        self.assertGreater(int(state["mlp.2.weight"].count_nonzero()), 0)
        self.assertTrue(torch.equal(state["ln_q.weight"], torch.ones(32)))
        self.assertTrue(torch.equal(state["mlp.0.weight"], pdg_v3.gated_init_state(4, 16, seed=17)["mlp.0.weight"]))
        self.assertFalse(torch.equal(state["mlp.0.weight"], pdg_v3.gated_init_state(4, 16, seed=18)["mlp.0.weight"]))

    def test_seed_does_not_move_global_rng(self):
        torch.manual_seed(5)
        expected = torch.rand(3)
        torch.manual_seed(5)
        pdg_v3.gated_init_state(4, 16)
        self.assertTrue(torch.equal(torch.rand(3), expected))

    def test_init_loads_through_init_modules_and_adds_zero(self):
        # The source std is checked on the real widths; toy layers have a noisy std, so draw wide ones.
        settings = pdg_v3.gated_block({**small_settings(), "feature_dim": 64})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g1.safetensors"
            sha = pdg_v3.write_init(path, 64, 512)
            report = pdg_v3.check_init(path, sha, settings, 512)
            self.assertTrue(report["output_zero"])
            self.assertEqual(report["tensors"], 6)
            module = geometry_input.GeometryInput(settings, 512)
            full_ft.load_init_modules({"init_modules": {"geometry": {"path": str(path), "sha256": sha}}}, geometry=module)
            pooled = torch.randn(5, 512)
            features = torch.randn(5, geometry_input.token_width(module.settings))
            self.assertTrue(torch.equal(pooled + module.projector(features), pooled))

    def test_check_init_refuses_nonzero_gate_and_plain_block(self):
        settings = pdg_v3.gated_block({**small_settings(), "feature_dim": 64})
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "g1.safetensors"
            state = pdg_v3.gated_init_state(64, 512)
            state["gate"][0] = 0.1
            from safetensors.torch import save_file
            save_file(state, str(path))
            with self.assertRaisesRegex(ValueError, "gate is not zero"):
                pdg_v3.check_init(path, pdg_v3.sha_file(path), settings, 512)
            with self.assertRaisesRegex(ValueError, "gated connector"):
                pdg_v3.check_init(path, pdg_v3.sha_file(path), geometry_input.normalize({**small_settings(), "feature_dim": 64}), 512)


class Configs(unittest.TestCase):
    INIT = {"path": "/x/g0_000000000000.safetensors", "sha256": "a" * 64}
    GEO = {"path": "/x/geometry_projector.safetensors", "sha256": "b" * 64}
    HEADS = {"path": "/x/auxiliary_heads.pt", "sha256": "c" * 64}

    def test_stage1_changes_only_block_rate_and_init(self):
        source = load("pdg_s1_config.json")
        config = pdg_v3.stage1_config(source, self.INIT)
        self.assertEqual(config["full_ft"]["learning_rates"], {"geometry": 1e-4, "heads": 1e-4})
        self.assertEqual(config["full_ft"]["init_modules"], {"geometry": self.INIT})
        self.assertEqual(config["geometry"], pdg_v3.gated_block(source["geometry"]))
        self.assertEqual(config["geometry"]["injection"], geometry_input.GATED_SPATIAL_INJECTION)
        self.assertEqual(config["camera"], source["camera"])
        self.assertEqual(set(pdg_v3.config_changes(source, config)), pdg_v3.STAGE1_FIELDS)
        self.assertEqual(full_ft.normalize(config["full_ft"])["init_modules"], {"geometry": self.INIT})

    def test_stage1_smoke_source(self):
        source = load("smoke_pdg_s1_config.json")
        config = pdg_v3.stage1_config(source, self.INIT)
        self.assertEqual((config["world_size"], config["max_steps"]), (8, 30))
        self.assertLessEqual(set(pdg_v3.config_changes(source, config)), pdg_v3.STAGE1_FIELDS)

    def test_stage1_refuses_second_application(self):
        config = pdg_v3.stage1_config(load("pdg_s1_config.json"), self.INIT)
        with self.assertRaisesRegex(ValueError, "without init modules"):
            pdg_v3.stage1_config(config, self.INIT)

    def test_stage2_changes_only_block_and_init_modules(self):
        source = load("pdg_s2_v2_config.json")
        config = pdg_v3.stage2_config(source, self.GEO, self.HEADS)
        self.assertEqual(config["full_ft"]["init_modules"], {"geometry": self.GEO, "heads": self.HEADS})
        self.assertEqual(config["geometry"], pdg_v3.gated_block(source["geometry"]))
        self.assertEqual(config["camera"]["weight"], 0.1)
        self.assertEqual(config["full_ft"]["learning_rates"], source["full_ft"]["learning_rates"])
        self.assertEqual(set(pdg_v3.config_changes(source, config)), pdg_v3.STAGE2_FIELDS)

    def test_stage2_refuses_v1_head_weights(self):
        source = load("pdg_s2_v2_config.json")
        source["camera"]["weight"] = 1.0
        with self.assertRaisesRegex(ValueError, "head weights"):
            pdg_v3.stage2_config(source, self.GEO, self.HEADS)

    def test_smoke_fields_match_the_reference_smokes(self):
        full, smoke = load("pdg_s1_config.json"), load("smoke_pdg_s1_config.json")
        self.assertEqual(pdg_v3.smoke_config(full), smoke)


class TrainerRebind(unittest.TestCase):
    def test_rebinds_identical_files_and_refuses_changed_ones(self):
        import hashlib
        with tempfile.TemporaryDirectory() as tmp:
            old, new = Path(tmp) / "aaa", Path(tmp) / "bbb"
            for tree in (old, new):
                (tree / "pkg").mkdir(parents=True)
                (tree / "pkg" / "big.py").write_bytes(b"x" * 100)
            sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()
            stat = lambda path: [Path(path).stat().st_size, Path(path).stat().st_mtime_ns]
            other = str(Path(tmp).parent / "elsewhere.bin")
            recorded = {str(old / "pkg" / "big.py"): {"target": str(old / "pkg" / "big.py"), "sha256": sha(old / "pkg" / "big.py"), "stat": [1, 2]},
                        other: {"target": other, "sha256": "f" * 64, "stat": [3, 4]}}
            self.assertEqual(pdg_v3.rebind_trainer_entries(recorded, new, sha, stat), ["pkg/big.py"])
            self.assertEqual(set(recorded), {str(new / "pkg" / "big.py"), other})
            self.assertEqual(recorded[str(new / "pkg" / "big.py")]["stat"], stat(new / "pkg" / "big.py"))
            (new / "pkg" / "big.py").write_bytes(b"y" * 100)
            recorded = {str(old / "pkg" / "big.py"): {"target": str(old / "pkg" / "big.py"), "sha256": sha(old / "pkg" / "big.py"), "stat": [1, 2]}}
            with self.assertRaisesRegex(ValueError, "byte-identical"):
                pdg_v3.rebind_trainer_entries(recorded, new, sha, stat)


if __name__ == "__main__":
    unittest.main()
