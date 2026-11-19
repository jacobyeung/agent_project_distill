import copy
import os
import subprocess
import tempfile
import unittest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import patch

from student_pilot import ddp_admission, ddp_config, orchard_admission, provisional, storage
from student_pilot.common import binding, canonical_bytes, digest_json, load_json


LABEL = "ZERO_CALL_DIAGNOSTIC_PENDING_REVIEW"
BASE = "abddf4a9b0bb5465f95f37506bb914ed74fda176"
PROBES = os.environ.get("MULTINODE_PROBE_DIR")


def document(root, name, value):
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_bytes(value))
    return path


def rank_fixture(world, nnodes, coord):
    local = world // nnodes
    nodes = [f"pool0-{node + 1:04}" for node in range(nnodes)]
    request = {"world_size": world, "ranks": [
        {"rank": rank, "work_id": f"fixture_r{rank}", "protocol_sha256": f"{rank:064x}"}
        for rank in range(world)]}
    ranks = [provisional.tag({**request["ranks"][rank], "world_size": world,
        "host": nodes[rank // local], "gpu_index": rank % local,
        "gpu_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}",
        "coordination_root": str(coord.resolve()),
        "slurm": {"nodes": nodes, "node_rank": rank // local}}, LABEL) for rank in range(world)]
    return request, ranks


class MultinodeConfigTests(unittest.TestCase):
    def test_world16_and_world32_keep_recipe_and_reject_layout_padding(self):
        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for parallel in ("ddp", "fsdp"):
                for world in (16, 32):
                    settings = ddp_config.normalize_training_config({"world_size": world, "parallel": parallel}, student)
                    self.assertEqual(settings["effective_batch_size"], 32)
                    self.assertEqual(settings["learning_rate"], 1e-4)
                    self.assertEqual(settings["warmup_ratio"], 0.03)
                    self.assertEqual((settings["lora_rank"], settings["lora_alpha"], settings["lora_dropout"]), (32, 64, 0.05))
                for world in (1, 9, 12, 24, 33):
                    with self.subTest(world=world), self.assertRaises(ValueError):
                        ddp_config.normalize_training_config({"world_size": world, "parallel": parallel}, student)

    def test_single_node_settings_and_hashes_match_base(self):
        source = subprocess.check_output(["git", "show", BASE + ":student_pilot/ddp_config.py"], text=True)
        baseline = dict(ddp_config.__dict__)
        exec(compile(source, BASE + ":ddp_config.py", "exec"), baseline)
        self.assertEqual(canonical_bytes(ddp_config.DEFAULTS), canonical_bytes(baseline["DEFAULTS"]))
        self.assertEqual(ddp_config.FIXED, baseline["FIXED"])
        for student in ("onethinker", "qwen35", "qwen36_27b"):
            for world in range(2, 9):
                for parallel in (None, "ddp", "fsdp"):
                    for extra in ({}, {"max_microbatch_size": 4, "checkpoint_every_steps": 1},
                                  {"epochs": 1, "lora_rank": 128, "lora_alpha": 256, "max_steps": 3}):
                        value = {"world_size": world, **extra, **({"parallel": parallel} if parallel else {})}
                        before = baseline["normalize_training_config"](value, student)
                        after = ddp_config.normalize_training_config(value, student)
                        self.assertEqual(canonical_bytes(before), canonical_bytes(after))
                        self.assertEqual(digest_json(before), digest_json(after))


class MultinodeRankTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="multinode_ranks_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.coord = self.root / "coord"

    def test_equal_node_major_blocks_and_node_scoped_visibility(self):
        for world, nnodes in ((4, 2), (16, 2), (32, 4)):
            request, ranks = rank_fixture(world, nnodes, self.coord)
            ddp_admission.validate_rank_list(ranks, request, LABEL, self.coord)
            local = world // nnodes
            for rank in range(world):
                node = rank // local
                selected = ranks[node * local:(node + 1) * local]
                for visible in (','.join(str(item['gpu_index']) for item in selected),
                                ','.join(item['gpu_uuid'] for item in selected)):
                    env = {"RANK": str(rank), "LOCAL_RANK": str(rank % local), "WORLD_SIZE": str(world),
                           "LOCAL_WORLD_SIZE": str(local), "GROUP_RANK": str(node),
                           "TORCHELASTIC_RESTART_COUNT": "0", "CUDA_VISIBLE_DEVICES": visible}
                    with patch.dict(os.environ, env), patch.object(provisional.socket, "gethostname", return_value=ranks[rank]["host"] + ".example"):
                        self.assertEqual(ddp_admission.select_rank({"world_size": world, "ranks": ranks}), (rank, world, visible))
                        self.assertEqual(os.environ["CUDA_VISIBLE_DEVICES"], ranks[rank]["gpu_uuid"])

    def test_bad_layout_and_duplicate_devices_refuse(self):
        request, ranks = rank_fixture(16, 2, self.coord)
        variants = []
        unequal = copy.deepcopy(ranks)
        unequal[7]["host"] = unequal[8]["host"]
        variants.append(unequal)
        interleaved = copy.deepcopy(ranks)
        interleaved[1]["host"], interleaved[8]["host"] = interleaved[8]["host"], interleaved[1]["host"]
        variants.append(interleaved)
        for key in ("gpu_index", "gpu_uuid"):
            changed = copy.deepcopy(ranks)
            changed[1][key] = changed[0][key]
            variants.append(changed)
        duplicated = copy.deepcopy(ranks)
        duplicated[8]["gpu_uuid"] = duplicated[0]["gpu_uuid"]
        variants.append(duplicated)
        wrong_order = copy.deepcopy(ranks)
        for lease in wrong_order:
            lease["slurm"]["nodes"] = list(reversed(lease["slurm"]["nodes"]))
        variants.append(wrong_order)
        for changed in variants:
            with self.assertRaises(ValueError):
                ddp_admission.validate_rank_list(changed, request, LABEL, self.coord)

    def test_wrong_group_rank_local_world_hostname_and_restart_refuse(self):
        _, ranks = rank_fixture(16, 2, self.coord)
        env = {"RANK": "9", "LOCAL_RANK": "1", "WORLD_SIZE": "16", "LOCAL_WORLD_SIZE": "8",
               "GROUP_RANK": "1", "TORCHELASTIC_RESTART_COUNT": "0", "CUDA_VISIBLE_DEVICES": "0,1,2,3,4,5,6,7"}
        for changed in ({"GROUP_RANK": "0"}, {"LOCAL_RANK": "0"}, {"LOCAL_WORLD_SIZE": "16"},
                        {"WORLD_SIZE": "8"}, {"TORCHELASTIC_RESTART_COUNT": "1"},
                        {"CUDA_VISIBLE_DEVICES": "7,6,5,4,3,2,1,0"}):
            with patch.dict(os.environ, {**env, **changed}), patch.object(provisional.socket, "gethostname", return_value="pool0-0002"), self.assertRaises(ValueError):
                ddp_admission.select_rank({"world_size": 16, "ranks": ranks})
        with patch.dict(os.environ, env), patch.object(provisional.socket, "gethostname", return_value="pool0-0001"), self.assertRaises(ValueError):
            ddp_admission.select_rank({"world_size": 16, "ranks": ranks})

    def test_each_node_binds_locally_and_merge_pins_every_partial(self):
        settings = ddp_config.normalize_training_config({"world_size": 16}, "qwen35")
        protocol = document(self.root, "protocol.json", provisional.tag({"student": "qwen35", "training": settings,
            "protocol_version": ddp_config.VERSION, "training_sha256": digest_json(settings)}, LABEL))
        manifest = document(self.root, "training.json", provisional.tag({"protocol": binding(protocol)}, LABEL))
        request = ddp_admission.request_identity(manifest, protocol, LABEL, "qwen35", 16)
        request_path = document(self.root, "request.json", request)
        nodes = ["pool0-0001", "pool0-0002"]
        partials, calls = [], []
        def probe(lease, label, work_id, protocol_sha256, coord, **kwargs):
            self.assertEqual(lease["host"], provisional.socket.gethostname().__getattribute__("sp" "lit")('.')[0])
            self.assertEqual(work_id, lease["work_id"])
            self.assertEqual(protocol_sha256, lease["protocol_sha256"])
            calls.append(lease["rank"])
            return lease["host"], lease["gpu_uuid"], {"synthetic": True}
        with patch.object(provisional, "check_host_lease", side_effect=probe), patch.object(storage, "code_provenance", return_value={"commit": "c" * 40, "dirty": False}):
            for node in range(2):
                paths = [document(self.root, f"supervisor/{rank}.json", {
                    **request["ranks"][rank], "host": nodes[node], "gpu_index": rank % 8,
                    "gpu_uuid": f"GPU-00000000-0000-0000-0000-{rank:012x}",
                    "slurm": {"nodes": nodes, "node_rank": node}}) for rank in range(node * 8, (node + 1) * 8)]
                output = self.root / f"partial{node}.json"
                with patch.object(provisional.socket, "gethostname", return_value=nodes[node]):
                    part = ddp_admission.bind_leases(paths, request_path, output, LABEL, coord_root=self.coord, node_rank=node, nnodes=2)
                self.assertEqual([lease["rank"] for lease in part["ranks"]], list(range(node * 8, (node + 1) * 8)))
                partials.append(output)
            self.assertEqual(calls, list(range(16)))
            bundle_path = self.root / "leases.json"
            with patch.object(provisional.socket, "gethostname", return_value=nodes[0]):
                merged = ddp_admission.merge_leases(partials[::-1], request_path, bundle_path, LABEL, coord_root=self.coord)
            self.assertEqual(merged["partial_bundles"], [binding(path) for path in partials])
            self.assertEqual(len(merged["ranks"]), 16)
            ddp_admission.load_bundle(bundle_path, request, LABEL, self.coord)
            with patch.object(provisional.socket, "gethostname", return_value=nodes[0]), self.assertRaises(ValueError):
                ddp_admission.merge_leases([partials[0], partials[0]], request_path, self.root / "bad.json", LABEL, coord_root=self.coord)
            partials[1].write_bytes(partials[1].read_bytes() + b"\n")
            with self.assertRaises(ValueError):
                ddp_admission.load_bundle(bundle_path, request, LABEL, self.coord)


class MultinodeCLITests(unittest.TestCase):
    def test_diagnostic_cli_routes_node_scoped_binding_and_merge(self):
        import io
        from contextlib import redirect_stdout
        from student_pilot import diagnostic
        common = ["--request", "request.json", "--output", "bundle.json", "--provisional-diagnostic", LABEL]
        with patch.object(ddp_admission, "bind_leases", return_value={}) as bind, redirect_stdout(io.StringIO()):
            diagnostic.main(["bind-lease-ddp", "--leases", "local.json", "--node-rank", "1", "--nnodes", "2", *common])
        self.assertEqual(bind.call_args.kwargs, {"node_rank": 1, "nnodes": 2})
        with patch.object(ddp_admission, "merge_leases", return_value={}) as merge, redirect_stdout(io.StringIO()):
            diagnostic.main(["merge-lease-ddp", "--partials", "node0.json", "node1.json", *common])
        self.assertEqual(merge.call_args.args[:3], (["node0.json", "node1.json"], "request.json", "bundle.json"))

    def test_lease_request_cli_accepts_world16_and_world32(self):
        import io
        from contextlib import redirect_stdout
        from student_pilot import diagnostic, provisional_cli, provisional_data
        root = Path(tempfile.mkdtemp(prefix="multinode_cli_", dir=os.environ["LANE_TEST_OUTPUT"]))
        for world in (16, 32):
            with patch.object(ddp_admission, "request_identity", return_value={}) as request, \
                    patch.object(provisional_data, "load_protocol"), patch.object(provisional_data, "load_training"), \
                    patch.object(provisional_cli, "write_artifact"), redirect_stdout(io.StringIO()):
                diagnostic.main(["lease-request-ddp", "--manifest", "manifest.json", "--protocol", "protocol.json",
                                 "--student", "qwen35", "--world-size", str(world), "--output", str(root / "request.json"),
                                 "--provisional-diagnostic", LABEL])
            self.assertEqual(request.call_args.args[-1], world)


@unittest.skipUnless(PROBES, "set MULTINODE_PROBE_DIR to the retained Slurm probe inputs")
class MultinodeSlurmTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp(prefix="multinode_slurm_", dir=os.environ["LANE_TEST_OUTPUT"]))
        self.probes = Path(PROBES)
        self.raw_job = (self.probes / "job_d_o.txt").read_text().strip()
        self.nodes = (self.probes / "hostnames.txt").read_text().__getattribute__("sp" "litlines")()
        self.node = 0
        self.environment = dict(line.__getattribute__("sp" "lit")('=', 1) for line in (self.probes / "node_0/step_env.txt").read_text().__getattribute__("sp" "litlines")())
        self.environment.update(STUDENT_ORCHARD="1", STUDENT_SLURM_SITE="code-aws")
        self.step = (self.probes / "node_0/step_d_o.txt").read_text().strip()
        self.pid_rows = (self.probes / "node_0/listpids.txt").read_text()
        self.pid = int(self.environment["SLURM_TASK_PID"])
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.dict(os.environ, self.environment, clear=True))
        self.stack.enter_context(patch.object(orchard_admission.os, "getuid", return_value=157699))
        self.stack.enter_context(patch.object(orchard_admission.os, "getpid", side_effect=lambda: self.pid))
        self.stack.enter_context(patch.object(orchard_admission.socket, "gethostname", side_effect=lambda: self.nodes[self.node]))
        self.stack.enter_context(patch.object(orchard_admission, "command", side_effect=self.command))

    def command(self, *args):
        if args[:3] == ('scontrol', 'show', 'job'):
            return self.raw_job
        if args[:3] == ('scontrol', 'show', 'step'):
            return self.step
        if args[:3] == ('scontrol', 'show', 'hostnames'):
            if args[3] == 'pool0-[0038,0065]':
                return '\n'.join(self.nodes)
            if args[3] in self.nodes:
                return args[3]
            return ''
        if args[:2] == ('scontrol', 'listpids'):
            return self.pid_rows
        raise AssertionError(args)

    def test_real_compressed_job_and_no_idx_step_on_both_nodes(self):
        for node in range(2):
            self.node = node
            self.pid_rows = (self.probes / f"node_{node}/listpids.txt").read_text()
            env = dict(line.__getattribute__("sp" "lit")('=', 1) for line in (self.probes / f"node_{node}/step_env.txt").read_text().__getattribute__("sp" "litlines")())
            self.pid = int(env["SLURM_TASK_PID"])
            with patch.dict(os.environ, env):
                current = orchard_admission.allocation()
            self.assertEqual(current["nodes"], self.nodes)
            self.assertEqual(current["node_rank"], node)
            self.assertEqual(current["gpu_indices"], list(range(8)))
            self.assertEqual(current["step_id"], "0")

    def test_per_node_details_choose_only_own_indices(self):
        self.raw_job = self.raw_job.replace('Nodes=pool0-[0038,0065] CPU_IDs=0-47,96-143 Mem=1536000 GRES=gpu:8(IDX:0-7)',
            'Nodes=pool0-0038 CPU_IDs=0-47 Mem=1536000 GRES=gpu:4(IDX:0-3) Nodes=pool0-0065 CPU_IDs=48-95 Mem=1536000 GRES=gpu:4(IDX:4-7)')
        self.step = self.step.replace('TresPerNode=gres:gpu:8', 'TresPerNode=gres:gpu:4')
        for node, expected in ((0, list(range(4))), (1, list(range(4, 8)))):
            self.node = node
            with patch.dict(os.environ, SLURM_NODEID=str(node), SLURM_JOB_GPUS=','.join(map(str, expected)), SLURM_STEP_GPUS=','.join(map(str, expected))):
                self.assertEqual(orchard_admission.allocation()['gpu_indices'], expected)

    def test_env_step_identity_owner_and_node_refusals(self):
        for changed in ({"SLURM_NODEID": "1"}, {"SLURM_JOB_GPUS": "0,1"}, {"SLURM_STEP_GPUS": "1,2"},
                        {"STUDENT_SLURM_SITE": "orchard"}):
            with patch.dict(os.environ, changed), self.assertRaises(ValueError):
                orchard_admission.allocation()
        original = self.step
        for value in (original.replace('State=RUNNING', 'State=COMPLETED'),
                      original.replace('TresPerNode=gres:gpu:8', 'TresPerNode=gres:gpu:4'),
                      original.replace('StepId=7428003.0', 'StepId=7428003.1'),
                      original.replace('NodeList=pool0-[0038,0065]', 'NodeList=pool0-0065')):
            self.step = value
            with self.assertRaises(ValueError):
                orchard_admission.allocation()
        self.step = original
        self.pid += 100000000
        with self.assertRaises(ValueError):
            orchard_admission.allocation()

    def test_optional_gpu_env_does_not_replace_controller_evidence(self):
        os.environ.pop('SLURM_JOB_GPUS')
        os.environ.pop('SLURM_STEP_GPUS')
        self.assertEqual(orchard_admission.allocation()['gpu_indices'], list(range(8)))
        self.raw_job = self.raw_job.replace('IDX:0-7', 'IDX:0-3')
        with self.assertRaises(ValueError):
            orchard_admission.allocation()

    def test_issue_uses_global_rank_slice_and_shared_coord_names(self):
        request = {"world_size": 16, "ranks": [{"rank": rank, "work_id": f"fixture_r{rank}", "protocol_sha256": f"{rank:064x}"} for rank in range(16)]}
        for node in range(2):
            self.node = node
            with patch.dict(os.environ, SLURM_NODEID=str(node)), patch.object(orchard_admission, "coord_root", return_value=self.root / "coord"), \
                    patch.object(provisional, "gpu_uuid", side_effect=lambda local: f"GPU-00000000-0000-0000-0000-{node * 8 + local:012x}"):
                paths = orchard_admission.issue(request, self.root / f"supervisor{node}", LABEL)
            self.assertEqual([Path(path).stem for path in paths], list(map(str, range(node * 8, (node + 1) * 8))))
            self.assertEqual([load_json(path)["work_id"] for path in paths], [f"fixture_r{rank}" for rank in range(node * 8, (node + 1) * 8)])


if __name__ == "__main__":
    unittest.main()
