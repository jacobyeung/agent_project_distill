"""Prove each new code regression fails on a deliberately broken variant."""
from pathlib import Path
import json, os, subprocess, sys

L = Path(__file__).resolve().parents[1]
prefix = 'tests.test_modep_'
cases = [
    ('sql_reverse_chunks', prefix+'select_sql.SelectSQL.test_multichunk_sparse_events_and_order_sensitive_output'),
    ('sql_reverse_chunks', prefix+'select_sql.SelectSQL.test_multichunk_frame_inventory_bytes_are_order_sensitive'),
    ('sql_reverse_rows', prefix+'select_sql.SelectSQL.test_multichunk_sparse_events_and_order_sensitive_output'),
    ('sql_ignore_on', prefix+'select_sql.SelectSQL.test_multichunk_sparse_events_and_order_sensitive_output'),
    ('paths_ignore_on', prefix+'fast_paths.FastPaths.test_switch_reaches_fast_resolver_only_when_on'),
    ('parser_literal', prefix+'fast_paths.FastPaths.test_mapping_parser_preserves_source_spelling'),
]
results = []
for index, (mutation, test) in enumerate(cases):
    label = f'review1_mutant_{index}_{mutation}'
    env = {**os.environ, 'MODEP_TREE': str(L/'work/delivery_tree'),
           'MODEP_TEST_LABEL': label, 'MODEP_MUTATION': mutation}
    command = [sys.executable, '-I', '-s', '-B', str(L/'work/run_native_tests.py'), test]
    log = L/'out/tests'/(label+'.log')
    with log.open('w') as handle:
        process = subprocess.run(command, env=env, stdout=handle, stderr=subprocess.STDOUT)
    result = json.loads((L/'work/tests'/label/'RESULT.json').read_text())
    assert process.returncode == 1 and len(result['failures']) == 1 and not result['errors'], result
    record = dict(mutation=mutation, test=test, returncode=process.returncode,
                  failures=len(result['failures']), errors=len(result['errors']), log=str(log), command=command)
    results.append(record)
    print('MUTATION_CAUGHT '+json.dumps(record, sort_keys=True), flush=True)
(L/'out/tests/review1_mutations.json').write_text(json.dumps(results, indent=2)+'\n')
