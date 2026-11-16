import ast
import subprocess
import unittest

from student_pilot.common import REPO


BASE = "5b23b728c1a2b2b631777eab0c8862d2aa2d0dc3"
REVIEWED = "294657d1c9783e5a5078ebefdaaec021841f4f03"


def source(commit, path):
    return subprocess.check_output(["git", "show", commit + ":" + path], cwd=REPO)


class IntegratedStartupTests(unittest.TestCase):
    def test_source_receipt_and_warmstart_binding_keep_baseline_bytes(self):
        for path in ("student_pilot/provisional_data.py", "student_pilot/provisional_cli.py",
                     "student_pilot/warmstart.py", "student_pilot/ddp_admission.py",
                     "student_pilot/ddp_checkpoints.py", "student_pilot/fsdp_training.py"):
            with self.subTest(path=path):
                self.assertEqual((REPO / path).read_bytes(), source(BASE, path))

    def test_reviewed_seed_validation_hunks_are_exact(self):
        path = "student_pilot/ddp_config.py"
        reviewed, current = source(REVIEWED, path).decode(), (REPO / path).read_text()
        prefix = reviewed[:reviewed.index("def runtime_bindings():")]
        self.assertTrue(current.startswith(prefix))

    def test_reviewed_batch_plan_block_is_exact_and_broadcast_from_rank_zero(self):
        path = "student_pilot/ddp_training.py"
        reviewed, current = source(REVIEWED, path).decode(), (REPO / path).read_text()
        start = reviewed.index('        batch_plan = {"microbatch_size":')
        block = reviewed[start:reviewed.index("        if checkpoint is not None:", start)]
        self.assertEqual(current.count(block), 1)
        tree = ast.parse(current)
        train = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "train")
        builder = next(node for node in train.body if isinstance(node, ast.FunctionDef) and node.name == "make_batch_plan")
        self.assertEqual(len(builder.body), 2)
        self.assertIsInstance(builder.body[0].value, ast.Dict)
        calls = [node for node in ast.walk(train) if isinstance(node, ast.Call)
                 and isinstance(node.func, ast.Name) and node.func.id == "collective_startup"
                 and node.args and isinstance(node.args[0], ast.Name) and node.args[0].id == "make_batch_plan"]
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.dump(calls[0].args[1]), "Name(id='rank', ctx=Load())")


if __name__ == "__main__":
    unittest.main()
