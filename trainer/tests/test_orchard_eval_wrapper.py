"""Shell-level regression for the Orchard eval wrapper's --thinking pass-through.

scripts/orchard/eval_job.py is a Slurm launcher script, not an importable
student_pilot module, so this drives it the way Slurm does: as a subprocess,
through its --print-args dry mode (STEP_7 section 7.2), with EVAL_THINKING
set in the environment exactly as submit_eval.sh's --export=ALL would forward
it. No ORCH/TRAINER/model staging is touched; --print-args exits before any
of that.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

REPO_ROOT = Path(__file__).resolve().parent.parent
EVAL_JOB = REPO_ROOT / 'scripts' / 'orchard' / 'eval_job.py'


def run_print_args(model, variant, env_extra, cell_id='dry-run-cell', extras=()):
    argv = [sys.executable, '-B', str(EVAL_JOB), '--print-args',
            '/prepared/does-not-need-to-exist', model, variant, cell_id, *extras]
    env = dict(os.environ)
    env.pop('EVAL_THINKING', None)
    env.update(env_extra)
    return subprocess.run(argv, capture_output=True, text=True, env=env)


class OrchardEvalThinkingPassThroughTests(unittest.TestCase):
    def test_off_is_refused_for_a_onethinker_cell(self):
        result = run_print_args('onethinker', 'base', {'EVAL_THINKING': 'off'})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('EVAL_THINKING=off is refused outside a Qwen base cell', result.stderr)

    def test_off_is_refused_for_a_distilled_qwen_cell(self):
        result = run_print_args('qwen35', 'distilled', {'EVAL_THINKING': 'off'},
                                 extras=('adapter-path', 'receipt-path', 'base-run-id'))
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('EVAL_THINKING=off is refused outside a Qwen base cell', result.stderr)

    def test_off_is_appended_for_a_qwen_base_cell(self):
        for model in ('qwen35', 'qwen36_27b'):
            with self.subTest(model=model):
                result = run_print_args(model, 'base', {'EVAL_THINKING': 'off'})
                self.assertEqual(result.returncode, 0, result.stderr)
                printed = json.loads(result.stdout)
                self.assertEqual(printed['thinking_args'], ['--thinking', 'off'])
                self.assertIn('student_pilot.orchard_eval', printed['cli'])
                self.assertNotIn('student_pilot.benchmark_eval', printed['cli'])

    def test_printed_cli_invokes_the_orchard_eval_module(self):
        result = run_print_args('onethinker', 'base', {})
        self.assertEqual(result.returncode, 0, result.stderr)
        printed = json.loads(result.stdout)
        self.assertIn('student_pilot.orchard_eval', printed['cli'])
        self.assertNotIn('student_pilot.benchmark_eval', printed['cli'])

    def test_pinned_is_appended_for_any_cell(self):
        result = run_print_args('onethinker', 'base', {'EVAL_THINKING': 'pinned'})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['thinking_args'], ['--thinking', 'pinned'])

    def test_invalid_value_is_refused(self):
        result = run_print_args('qwen35', 'base', {'EVAL_THINKING': 'maybe'})
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn('EVAL_THINKING must be pinned or off', result.stderr)

    def test_unset_adds_no_thinking_flag(self):
        result = run_print_args('qwen35', 'base', {})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)['thinking_args'], [])


if __name__ == '__main__':
    unittest.main()
