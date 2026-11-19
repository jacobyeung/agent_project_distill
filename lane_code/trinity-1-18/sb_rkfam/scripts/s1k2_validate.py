"""Synthetic existing-kit tests and fail-closed CPU dry run; no evaluation items."""
from common import *
import importlib.util
import resource
import unittest


def main():
    resource.setrlimit(resource.RLIMIT_AS, (39 << 30, 39 << 30))
    p = W/'tests/test_roomkit.py'
    spec = importlib.util.spec_from_file_location('s1k2_existing_tests', p)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The original setUpClass loads prohibited R0-dev/direct items. These selected
    # methods need no direct rows, and their bodies are used without modification.
    class SyntheticTests(module.Tests):
        @classmethod
        def setUpClass(cls):
            pass
    names = ['test_trim_exact_far_tenth', 'test_refusal_preserved', 'test_ft2',
             'test_resume_all_three_states_and_binding', 'test_incomplete_receipt_stops',
             'test_go_binds_actual_host_card_run', 'test_no_go_rejected_before_cuda',
             'test_budget_exhausted_and_interrupted', 'test_budget_load_and_retry_cumulative',
             'test_budget_exclusive', 'test_missing_provenance_blocks']
    result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(SyntheticTests(n) for n in names))
    inputs = module.input_code()
    inputs.update({str(p): sha(p) for p in [Path(__file__), W/'scripts/cpu.sh', p,
                                         W/'out/S1K2_GT_AUDIT.json', W/'out/S1K2_RULE.md']})
    audit = read(W/'out/S1K2_GT_AUDIT.json')
    for p in [W/'configs/KERNEL_PROVENANCE.json', W/'configs/KERNEL_FROZEN.json']:
        assert sha(p) == audit['input_sha256'][str(p)], 'Old provenance was modified'
        inputs[str(p)] = sha(p)
    write(W/'out/S1K2_TESTS.json', dict(verdict='PASS' if result.wasSuccessful() else 'FAIL',
          tests=result.testsRun, failures=len(result.failures), errors=len(result.errors),
          methods=names, old_provenance_unchanged=True,
          scope='Existing synthetic methods only; original setUpClass disabled because it reads prohibited real evaluation items.',
          full_suite='NOT_RUN: real R0-dev/direct and mixed-split dependencies are forbidden for this task',
          command='bash scripts/cpu.sh scripts/s1k2_validate.py'), inputs)
    from gates import prerequisites
    provenance = W/'configs/KERNEL_PROVENANCE_S1K2.json'
    assert read(provenance)['status'] == 'MISSING'
    try:
        # This file serves both arguments: the gate must reject provenance before
        # any reader-receipt, evaluation-manifest or inference access is needed.
        prerequisites(provenance, provenance)
    except ValueError as exc:
        assert str(exc) == 'MISSING kernel provenance'
        rejection = str(exc)
    else:
        raise AssertionError('Blocked S1k2 provenance was accepted')
    write(W/'out/S1K2_DRYRUN.json', dict(verdict='PASS', mode='CPU fail-closed provenance gate',
          rejection=rejection, inference_executed=False, new_kernel_validation='MISSING: no selected kernel',
          full_cpu_dry_run='NOT_RUN: independent GT and selected kernel missing',
          command='bash scripts/cpu.sh scripts/s1k2_validate.py'),
          {**inputs, str(provenance): sha(provenance)})
    status('S1k2 remains blocked by missing independent room-area GT for all 110 training captures. Synthetic kit tests and a CPU provenance-gate dry run are recorded in out/S1K2_TESTS.json and out/S1K2_DRYRUN.json. No family was scored and no kernel was rebound. Packaging remains.')
    raise SystemExit(not result.wasSuccessful())


if __name__ == '__main__':
    main()
