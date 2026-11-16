"""Run the scoped S9 suites while retaining every TemporaryDirectory fixture."""
import argparse
import datetime
import json
import os
from pathlib import Path
import tempfile
import time
import unittest


MODULES = (
    'tests.test_gxp_mix', 'tests.test_gx_dense_binding', 'tests.test_gx_carrier', 'tests.test_gx_s6', 'tests.test_gx_s7',
    'tests.test_gx_s8', 'tests.test_c1_pose_warm', 'tests.test_carrier_c1_final',
    'tests.test_carrier_c1_single_image', 'tests.test_carrier_c1_run', 'tests.test_carrier_c1_data',
    'tests.test_c1_validation_slice', 'tests.test_carrier_c1_routing', 'tests.test_cpu_startup',
    'tests.test_carrier_c1', 'tests.test_carrier_c1_layout', 'tests.test_carrier_c1_t0',
)
FIXTURES = Path('/scratch/jjyeung/orch_cd/gx_build/work/fixtures')


class RetainedTemporaryDirectory(tempfile.TemporaryDirectory):
    paths = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paths.append(self.name)

    def cleanup(self):
        self._finalizer.detach()

    @classmethod
    def _cleanup(cls, name, warn_message, ignore_errors=False, **kwargs):
        # Weakref finalization also retains the fixture when no context was used.
        pass


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--log', required=True)
    parser.add_argument('--receipt', required=True)
    parser.add_argument('tests', nargs='*')
    args = parser.parse_args()
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '' or os.environ.get('PYTHONDONTWRITEBYTECODE') != '1':
        raise ValueError('Use the supplied CPU py.sh wrapper')
    if Path(os.environ['TMPDIR']).resolve() != FIXTURES.resolve():
        raise ValueError('TMPDIR must be the authorized fixtures directory')
    tempfile.TemporaryDirectory = RetainedTemporaryDirectory
    selected = args.tests or list(MODULES)
    start = time.monotonic()
    with Path(args.log).open('x') as log:
        suite = unittest.defaultTestLoader.loadTestsFromNames(selected)
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    receipt = dict(schema='gxp-mix-cpu-tests-v1', tests=selected,
        utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        exit_code=0 if result.wasSuccessful() else 1, tests_run=result.testsRun,
        failures=len(result.failures), errors=len(result.errors),
        skipped=[dict(test=str(test), reason=reason) for test, reason in result.skipped],
        seconds=time.monotonic()-start, retained_temporary_directories=RetainedTemporaryDirectory.paths,
        CUDA_VISIBLE_DEVICES=os.environ['CUDA_VISIBLE_DEVICES'], TMPDIR=os.environ['TMPDIR'])
    with Path(args.receipt).open('x') as out:
        json.dump(receipt, out, indent=2)
        out.write('\n')
    print(json.dumps({k: receipt[k] for k in ('exit_code', 'tests_run', 'failures', 'errors', 'seconds')}))
    return receipt['exit_code']


if __name__ == '__main__':
    raise SystemExit(main())
