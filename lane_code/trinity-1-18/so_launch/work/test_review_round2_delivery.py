"""Review contracts for planning claims, real staging coverage and clean kits."""
import ast
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OUT = Path(os.environ.get('REVIEW_OUT', ROOT / 'out'))
TREE = Path(os.environ.get('REVIEW_TREE', ROOT / 'work/tree'))


class ReviewRound2Tests(unittest.TestCase):
    def test_finding_1_prepare_only_planning_number_and_unmeasured_floor(self):
        design = (OUT / 'CROSS_RUN_STORE_DESIGN.md').read_text()
        self.assertIn('about 70 min, the prepare half, until measured', design)
        self.assertNotRegex(design, r'110[–-]135|10[–-]30 minutes')
        for phrase in ('node-local', 'verify_frames', 'pinned()', 'run.prepared',
                       'complete journal', 'not measured', 'physical paths'):
            self.assertIn(phrase, design)

    def test_finding_2_transport_and_checkpoint_identity_are_concrete(self):
        design = (OUT / 'CROSS_RUN_STORE_DESIGN.md').read_text()
        for phrase in ('GCS', 'login-node', '/project/community/jjyeung/distill/okit/in',
                       'project_community_write_bytes == 0', 'session',
                       'content-derived phase directory names', 'derived config identity',
                       'preparation pin', '13–22 engineering days'):
            self.assertIn(phrase, design)

    def test_finding_3_warm_pass_estimate_and_first_resume_measurement(self):
        for name in ('REPORT.md', 'NOTE_FOR_TREE_REBUILD.md'):
            text = (OUT / name).read_text()
            self.assertIn('about 4–5 min (inferred)', text)
            self.assertIn('up to about 9 only if the page cache does not keep the checkpoint', text)
            self.assertNotRegex(text, r'4[–-]10 min|571 s|evenly')
            self.assertIn('TK_LAUNCH_TIMING=1', text)
            self.assertIn('first resume', text)

    def test_finding_4_real_stage_lock_branch_has_packaged_regression(self):
        tests = ast.parse((TREE / 'tests/test_launch_phase_timing.py').read_text())
        methods = {node.name: node for node in ast.walk(tests) if isinstance(node, ast.FunctionDef)}
        name = 'test_real_stage_lock_timing_prep_and_preflight_on_off'
        self.assertIn(name, methods)
        body = ast.unparse(methods[name])
        for phrase in ('preflight', 'prep', 'wait_seconds=0', 'pipefail', 'TIMING_INPUT_C'):
            self.assertIn(phrase, body)

    def test_finding_5_documented_all_four_application_leaves_no_backups(self):
        scratch = Path(tempfile.mkdtemp(prefix='patch-order-', dir=os.environ['TEST_TMP_ROOT']))
        # Copy only paths touched by these diffs; all are small local code files.
        import json
        manifest = json.loads((ROOT / 'out/patches/manifest.json').read_text())
        source = ROOT / 'in/tree/work/tree_r1'
        for rel in {p for entry in manifest.values() for p in entry['files']}:
            dest = scratch / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            if (source / rel).is_file():
                shutil.copyfile(source / rel, dest)
        lines = [line for line in (OUT / 'NOTE_FOR_TREE_REBUILD.md').read_text().splitlines()
                 if line.startswith('patch ')]
        self.assertEqual(len(lines), 3)
        commands = [shlex.split(line.replace('$L', str(ROOT))) for line in lines]
        optional = commands[-1].copy()
        optional[-1] = str(ROOT / 'out/patches/01_prepared_input_cache.diff')
        for command in [*commands, optional]:
            result = subprocess.run(command, cwd=scratch, capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertNotIn('with fuzz', result.stdout)
        self.assertEqual(list(scratch.rglob('*.orig')), [])
        self.assertEqual(list(scratch.rglob('*.rej')), [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
