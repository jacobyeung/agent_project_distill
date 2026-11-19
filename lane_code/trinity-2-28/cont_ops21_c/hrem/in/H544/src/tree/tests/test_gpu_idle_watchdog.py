import json
import subprocess
import unittest
from unittest.mock import patch

from scripts.orchard import gpu_idle_watchdog as watchdog


POLICY = {'utilization_threshold': 5.0, 'idle_seconds': 480.0, 'max_gap_seconds': 90.0}
DETAIL = ('JobId=42 JobName=fixture UserId=tester(1001) JobState=RUNNING Restarts=0 '
          'StartTime=2026-10-04T00:00:00 NumNodes=2 NodeList=node[01-02] AllocTRES=cpu=8,gres/gpu=4 '
          'Nodes=node[01-02] CPU_IDs=0-3 Mem=256 GRES=gpu:a100:2(IDX:1,3)')


def expand(value):
    return ['node01', 'node02'] if value == 'node[01-02]' else [value]


def job(clock, utilizations=(0, 90), restart='0', errors=()):
    return {'job_id': '42', 'allocation_id': '42', 'name': 'fixture', 'start_time': '2026-10-04T00:00:00',
            'restarts': restart, 'expected_gpu_count': 2, 'errors': list(errors), 'samples': [
                {'node': 'node01', 'index': index, 'uuid': 'GPU-' + str(index), 'utilization_pct': utilization,
                 'memory_used_mib': 79000, 'clock': float(clock), 'observed_at': 'synthetic'}
                for index, utilization in enumerate(utilizations)]}


def evaluate(samples, previous=None):
    return watchdog.evaluate(samples, previous, 'observer:boot', POLICY)


class MetadataTests(unittest.TestCase):
    def test_maps_every_node_and_only_the_allocated_gpu_indices(self):
        result = watchdog.parse_job(DETAIL, '42', 'tester', 1001, expand)
        self.assertEqual(result['expected_gpu_count'], 4)
        self.assertEqual(result['nodes']['node02'], {'indices': [1, 3], 'gres': 'gpu:a100:2'})

    def test_rejects_foreign_owners_and_wrong_job_ids(self):
        for text in (DETAIL.replace('tester(1001)', 'other(1001)'), DETAIL.replace('tester(1001)', 'tester(1002)'), DETAIL.replace('JobId=42', 'JobId=43')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                watchdog.parse_job(text, '42', 'tester', 1001, expand)

    def test_rejects_incomplete_allocation_and_mig(self):
        for text in (DETAIL.replace('gres/gpu=4', 'gres/gpu=5'), DETAIL.replace('IDX:1,3', 'IDX:N/A'), DETAIL.replace('a100:2', 'a100_1g.5gb:2')):
            with self.subTest(text=text), self.assertRaises(ValueError):
                watchdog.parse_job(text, '42', 'tester', 1001, expand)

    def test_array_task_resolves_to_its_internal_allocation_id(self):
        text = DETAIL.replace('JobId=42', 'JobId=142 ArrayJobId=42 ArrayTaskId=3')
        result = watchdog.parse_job(text, '42_3', 'tester', 1001, expand)
        self.assertEqual(result['allocation_id'], '142')

    def test_queue_parsing_rejects_ambiguous_or_foreign_rows(self):
        self.assertEqual(watchdog.parse_queue('42|tester\n43_2|tester\n', 'tester'), ['42', '43_2'])
        for text in ('42|other', '42;bad|tester', '42|tester\n42|tester'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                watchdog.parse_queue(text, 'tester')

    def test_probe_is_bounded_and_uses_only_the_existing_job(self):
        args = watchdog.probe_command('42', 'node01', 'gpu:a100:2')
        self.assertIn('--jobid=42', args)
        self.assertIn('--overlap', args)
        self.assertIn('--nodelist=node01', args)
        self.assertIn('--gres=gpu:a100:2', args)
        self.assertIn('--immediate=3', args)
        self.assertIn('nvidia-smi', args)
        self.assertFalse(any(name in args for name in ('sbatch', 'scancel', 'update')))


class GpuCsvTests(unittest.TestCase):
    def test_filters_unallocated_devices_and_preserves_per_gpu_values(self):
        rows = watchdog.parse_gpu_csv('0, GPU-0, 99, 12\n1, GPU-1, 5, 60000\n3, GPU-3, 0, 0\n', [1, 3])
        self.assertEqual([row['index'] for row in rows], [1, 3])
        self.assertEqual([row['utilization_pct'] for row in rows], [5, 0])

    def test_refuses_missing_duplicate_and_malformed_devices(self):
        for text in ('', '1, GPU-1, 0, 2\n', '1, GPU-1, 0, 2\n1, GPU-1, 0, 2\n', '1, MIG-a, 0, 2\n3, GPU-3, 0, 2\n', 'garbled'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                watchdog.parse_gpu_csv(text, [1, 3])

    def test_unavailable_nonfinite_and_out_of_range_utilization_stays_unknown(self):
        for value in ('N/A', 'NaN', 'inf', '-1', '101'):
            with self.subTest(value=value):
                rows = watchdog.parse_gpu_csv(f'1, GPU-1, {value}, 100\n', [1])
                self.assertIsNone(rows[0]['utilization_pct'])


class HistoryTests(unittest.TestCase):
    def low_history(self, stop=480):
        result = None
        for when in range(0, stop + 1, 60):
            result = evaluate([job(when)], result)
        return result

    def test_one_snapshot_never_invents_eight_minutes_of_history(self):
        result = evaluate([job(100000)])
        gpu = result['jobs'][0]['gpus'][0]
        self.assertEqual(gpu['sampled_idle_seconds'], 0)
        self.assertFalse(result['jobs'][0]['flagged'])

    def test_strict_eight_minute_limit_is_per_gpu_not_an_average(self):
        result = self.low_history()
        self.assertFalse(result['jobs'][0]['flagged'])
        result = evaluate([job(540)], result)
        value = result['jobs'][0]
        self.assertTrue(value['flagged'])
        self.assertFalse(value['all_gpus_flagged'])
        self.assertEqual([gpu['flagged'] for gpu in value['gpus']], [True, False])
        self.assertEqual(value['gpus'][0]['sampled_idle_seconds'], 540)

    def test_five_percent_counts_as_low_and_high_memory_does_not_excuse_it(self):
        result = None
        for when in range(0, 601, 60):
            result = evaluate([job(when, (5, 5))], result)
        self.assertTrue(result['jobs'][0]['all_gpus_flagged'])

    def test_active_sample_unknown_utilization_and_probe_failure_reset_history(self):
        for util, errors in ((6, ()), (None, ()), (0, ('probe failed',))):
            with self.subTest(util=util, errors=errors):
                previous = self.low_history()
                current = job(540, (util, 90), errors=errors)
                if errors:
                    current['samples'] = []
                middle = evaluate([current], previous)
                result = evaluate([job(600)], middle)
                self.assertFalse(result['jobs'][0]['flagged'])
                self.assertEqual(result['jobs'][0]['gpus'][0]['sampled_idle_seconds'], 0)

    def test_sampling_gap_clock_reversal_requeue_and_gpu_replacement_reset(self):
        for mutate in ('gap', 'clock', 'restart', 'uuid', 'start'):
            with self.subTest(mutate=mutate):
                previous = self.low_history()
                current = job(540)
                if mutate == 'gap':
                    current = job(900)
                elif mutate == 'clock':
                    current = job(100)
                elif mutate == 'restart':
                    current['restarts'] = '1'
                elif mutate == 'uuid':
                    current['samples'][0]['uuid'] = 'GPU-a'
                else:
                    current['start_time'] = '2026-10-04T01:00:00'
                result = evaluate([current], previous)
                self.assertFalse(result['jobs'][0]['flagged'])
                self.assertEqual(result['jobs'][0]['gpus'][0]['sampled_idle_seconds'], 0)

    def test_different_observer_or_policy_and_malformed_state_do_not_carry_history(self):
        for mutate in ('observer', 'policy', 'corrupt'):
            previous = self.low_history()
            if mutate == 'observer':
                previous['state']['observer'] = 'another:boot'
            elif mutate == 'policy':
                previous['state']['policy']['utilization_threshold'] = 90
            else:
                key = next(iter(previous['state']['gpus']))
                previous['state']['gpus'][key]['since'] = float('nan')
            result = evaluate([job(540)], previous)
            self.assertFalse(result['jobs'][0]['flagged'])

    def test_absent_jobs_are_removed_and_errors_are_not_reported_as_health(self):
        previous = self.low_history()
        result = evaluate([], previous)
        self.assertEqual(result['state']['gpus'], {})
        broken = job(540, errors=['allocation changed'])
        broken['samples'] = []
        value = evaluate([broken], previous)['jobs'][0]
        self.assertEqual(value['status'], 'UNKNOWN')
        self.assertFalse(value['flagged'])


class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.details = [DETAIL, DETAIL]
        self.calls = []
        self.fail_node = None

    def runner(self, command, timeout=5):
        self.calls.append(command)
        if command[:3] == ['scontrol', 'show', 'job']:
            return self.details.pop(0)
        if command[:3] == ['scontrol', 'show', 'hostnames']:
            return 'node01\nnode02\n'
        if command[0] == 'srun':
            node = next(value.__getattribute__("sp" "lit")('=')[1] for value in command if value.startswith('--nodelist='))
            if node == self.fail_node:
                raise subprocess.TimeoutExpired(command, timeout)
            prefix = 'a' if node == 'node01' else 'b'
            return f'1, GPU-{prefix}1, 0, 79000\n3, GPU-{prefix}3, 90, 79000\n'
        raise AssertionError(command)

    def collect(self):
        with patch.object(watchdog, 'run_command', side_effect=self.runner):
            return watchdog.collect_job('42', 'tester', 1001)

    def test_reads_both_nodes_and_rechecks_allocation_after_probing(self):
        value = self.collect()
        self.assertEqual(len(value['samples']), 4)
        self.assertEqual(value['errors'], [])
        self.assertEqual(self.calls[0][:3], ['scontrol', 'show', 'job'])
        self.assertEqual(self.calls[-1][:3], ['scontrol', 'show', 'job'])
        self.assertEqual(len([call for call in self.calls if call[0] == 'srun']), 2)
        json.dumps(evaluate([value]), allow_nan=False)

    def test_requeue_during_probe_discards_every_sample(self):
        self.details[1] = DETAIL.replace('Restarts=0', 'Restarts=1')
        value = self.collect()
        self.assertEqual(value['samples'], [])
        self.assertIn('Allocation changed', value['errors'][0])

    def test_timeout_is_unknown_not_an_idle_or_healthy_job(self):
        self.fail_node = 'node01'
        value = self.collect()
        self.assertEqual(len(value['samples']), 2)
        result = evaluate([value])['jobs'][0]
        self.assertEqual(result['status'], 'UNKNOWN')
        self.assertFalse(result['complete_coverage'])
        self.assertFalse(result['flagged'])

    def test_foreign_owner_is_never_probed(self):
        self.details[0] = DETAIL.replace('tester(1001)', 'other(1001)')
        value = self.collect()
        self.assertTrue(value['errors'])
        self.assertEqual(len(self.calls), 1)

    def test_cpu_jobs_do_not_start_steps(self):
        self.details[0] = DETAIL.replace(',gres/gpu=4', '')
        self.assertIsNone(self.collect())
        self.assertEqual(len(self.calls), 1)

    def test_malformed_history_container_cannot_crash_or_flag(self):
        for value in (None, [], 4, 'corrupt'):
            with self.subTest(value=value):
                result = evaluate([job(540)], {'state': value})
                self.assertFalse(result['jobs'][0]['flagged'])


if __name__ == '__main__':
    unittest.main()
