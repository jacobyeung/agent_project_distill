from support import *

class DriverTests(DriverFixture):
    def test_all_sources_success_and_new_node(self):
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'STAGED trinity-2-28 rc=0', result.stdout)
        self.assertIn(b'verified GitHub lane-code', result.stdout)
        calls = [json.loads(line) for line in (self.root / 'ssh.jsonl').read_text().splitlines()]
        receiver = [args for args in calls if 'trinity-3-30.ib' in args]
        self.assertEqual(len(receiver), 2)
        self.assertTrue(all('ConnectionAttempts=1' in args for args in receiver))

    def test_partial_failed_node_cannot_overwrite_or_delete_previous(self):
        self.env['FAKE_trinity_1_18'] = 'partial'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 stage rc=23', result.stdout)
        print('MEASURE partial_failure_elapsed=%.3fs commit=1 pushes=2 preserved=1' % self.elapsed, flush=True)

    def test_unreachable_skipped_other_sources_publish(self):
        self.env['FAKE_trinity_1_18'] = 'unreachable'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'Connection timed out', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_missing_root_skipped_other_sources_publish(self):
        self.env['FAKE_trinity_1_18'] = 'missing'
        result = self.run_driver()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'SKIP trinity-1-18 (no source root)', result.stdout)
        self.assertNotIn(b'FAIL', result.stdout)
        self.assertFalse(list((self.root / 'events').glob('*_BLOCKER*')))
        self.assertTrue((self.repo / 'lane_code' / 'trinity-2-28' / 'good.py').is_file())

    def test_legacy_substitution_reproduces_held_pipe(self):
        self.env['FAKE_trinity_1_18'] = 'held_exit'
        command = 'out=$(timeout --kill-after=0.1 0.2 ssh trinity-1-18 ignored 2>&1); echo finished'
        started = time.monotonic()
        result = subprocess.run(['bash', '-c', command], env=self.env, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, timeout=4)
        elapsed = time.monotonic() - started
        self.assertEqual(result.returncode, 0)
        self.assertGreater(elapsed, 1)
        print('MEASURE legacy_substitution_elapsed=%.3fs timeout=0.2s holder_lifetime=1.2s' % elapsed, flush=True)

    def test_remote_scanner_timeout_reports_pipestatus(self):
        self.env['FAKE_trinity_1_18'] = 'scanner_hang'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'PIPE 124 0 0', result.stdout)

    def test_receiver_timeout_does_not_block_local_publish(self):
        self.env['FAKE_RECEIVER_HANG'] = '1'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'PIPE 0 0 137', result.stdout)
        self.assertTrue((self.repo / 'lane_code' / 'trinity-3-30' / 'good.py').is_file())
        self.assertIn(b'committed', result.stdout)
        self.assertLess(self.elapsed, 4)

    def test_dry_mode_and_stage_only_keep_existing_semantics(self):
        result = self.run_driver(('--dry',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'PIPE 0', result.stdout)
        self.assertFalse((self.root / 'git.jsonl').exists())
        result = self.run_driver(('--stage-only',))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((self.repo / 'lane_code' / 'trinity-2-28' / 'good.py').is_file())
        self.assertFalse((self.root / 'git.jsonl').exists())

    def test_invalid_zero_timeout_refused(self):
        self.env['LCS_NODE_SECONDS'] = '0'
        result = self.run_driver()
        self.assertEqual(result.returncode, 2)
        self.assertIn(b'invalid LCS_NODE_SECONDS=0', result.stdout)
        self.assertFalse((self.root / 'ssh.jsonl').exists())

    def test_outer_remote_timeout(self):
        self.env.update(FAKE_trinity_1_18='scanner_hang', LCS_SCAN_SECONDS='2',
                        LCS_LEG_SECONDS='2', LCS_REMOTE_SECONDS='0.3')
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 stage rc=124', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_copy_scanner_fifo_is_bounded_per_source(self):
        self.env['FAKE_STAGE_FIFO'] = '1'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertIn(b'trinity-1-18 accept stage rc=1', result.stdout)
        self.assertIn(b'nonregular archive entry', result.stdout)
        self.assertLess(self.elapsed, 3)

    def test_tar_leg_kill_after_and_other_sources_publish(self):
        write(self.bin / 'tar', '#!/bin/bash\n'
              'if [[ "$PWD" == */sources/trinity-1-18 ]] && [[ " $* " == *" -cf "* ]]; then\n'
              '  trap "" TERM; sleep 4\n'
              'else exec /usr/bin/tar "$@"; fi\n', True)
        self.env['LCS_LEG_SECONDS'] = '0.25'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertRegex(result.stdout.decode(), r'PIPE 0 137 (0|2|124|137)')
        self.assertLess(self.elapsed, 3)

    def test_default_off_driver_matches_input_behavior(self):
        self.env['LCS_ROBUST_SYNC'] = '0'
        # Rewrite only fixed source paths in fixture copies; neither driver can touch a real lane.
        baseline = (INPUT / 'lane_code_sync.sh').read_text()
        candidate = (TOOLS / 'lane_code_sync.sh').read_text()
        outputs, trees = [], []
        for name, text in (('baseline', baseline), ('candidate', candidate)):
            script = self.root / (name + '.sh')
            script.write_text(text.replace('/scratch/jjyeung/orch_n30', str(self.local)).replace('code_sync/meta', ''))
            state = self.root / name
            repo = state / 'repo'
            repo.mkdir(parents=True)
            env = dict(self.env, LCS_S=str(state), LCS_R=str(repo))
            result = subprocess.run(['bash', str(script)], env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, timeout=5)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            normalized = result.stdout.decode().replace(str(state), '<STATE>')
            outputs.append(re.sub(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', '<UTC>', normalized))
            trees.append({str(p.relative_to(repo)): p.read_bytes() for p in repo.rglob('*') if p.is_file()})
        self.assertEqual(outputs[0], outputs[1])
        self.assertEqual(trees[0], trees[1])

