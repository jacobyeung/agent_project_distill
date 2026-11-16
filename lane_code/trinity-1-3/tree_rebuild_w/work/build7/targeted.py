"""Verify pending repairs against the current source after package tests finish."""
import json
import os
from pathlib import Path
import subprocess
import sys

L = Path(__file__).resolve().parents[2]
B = L / 'work/build7'
output = B / 'proofs/final_targeted'
names = [
    'tests.test_r2_build6',
    'tests.test_r2_build3.Build3.test_opener_export_keep_and_reset',
    'generator.derivgen_v7.test_v312_quality.QualityTests.test_qualifier_must_equal_literal_gt_label',
    'tests.test_c1_validation_slice.ValidationPreparation.test_validation_config_is_optional_and_requires_exact_pins',
    'tests.test_gxp_mix.MemoryFallback.test_absent_keys_preserve_normalized_identity_and_fp32_output_bytes',
    'tests.test_s1_launch_kit.LaunchKitTests.test_all_eight_ranks_and_native_configuration_binding_are_required',
    'coverage_cases',
]
env = {**os.environ, 'R2_TREE': str(L / 'work/tree_r1'),
       'R2_LANE_ROOT': str(L), 'R2_ALL_TESTS': '0',
       'R2_SUITE_GROUP': '', 'R2_PACKAGE_MEMBERS': ''}
with (B / 'targeted.log').open('w') as log:
    result = subprocess.run(
        [sys.executable, '-I', '-s', '-B', str(B / 'test_runner.py'), str(output), *names],
        env=env, stdout=log, stderr=subprocess.STDOUT)
if result.returncode < 0:
    raise RuntimeError('Targeted process was killed; stop without retry')
value = json.loads((output / 'results.json').read_text())
print(json.dumps({k: len(value[k]) if isinstance(value[k], list) else value[k]
                  for k in ('tests', 'passed', 'errors', 'failures', 'complete')}))
if result.returncode or not value['complete']:
    raise SystemExit('Targeted verification failed; inspect work/build7/targeted.log')
with (B / 'STATUS.md').open('a') as stream:
    stream.write('\nCurrent-source focused verification passed '
                 '(`work/build7/proofs/final_targeted/results.json`).\n')
