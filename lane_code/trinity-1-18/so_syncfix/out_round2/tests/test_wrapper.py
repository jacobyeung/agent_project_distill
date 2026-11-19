from support import *

class WrapperTests(DriverFixture):
    def test_held_stdout_deadline_and_lock_release(self):
        self.env['FAKE_trinity_1_18'] = 'held_hang'
        self.env['LCS_NODE_SECONDS'] = '0.35'
        result = self.run_driver()
        self.check_partial_success(result)
        self.assertLess(self.elapsed, 3)
        pid = int((self.root / 'holder.pid').read_text())
        os.kill(pid, 0)  # The child still holds stdout after the driver has returned.
        ssh_pid = int((self.root / 'ssh.pid').read_text())
        # A zombie has exited; it is waiting for PID 1 to reap it.
        proc = Path('/proc') / str(ssh_pid) / 'stat'
        if proc.exists():
            self.assertEqual(proc.read_text().split(') ', 1)[1].split()[0], 'Z')
        locked = subprocess.run(['flock', '-n', str(self.state / '.sync.lock'), 'true'])
        self.assertEqual(locked.returncode, 0)
        self.assertRegex(result.stdout.decode(), r'trinity-1-18 stage rc=(124|137)')
        slot = self.state / 'stage-robust' / 'trinity-1-18'
        node_elapsed = (slot / 'run.log').stat().st_mtime - (slot / 'program.sh').stat().st_mtime
        self.assertLess(node_elapsed, 0.9)
        self.assertGreater(node_elapsed, 0.35)
        print('MEASURE held_stdout_driver_elapsed=%.3fs node_limit=0.35s kill_after=0.15s holder_alive=1 lock_free=1' % self.elapsed, flush=True)
        print('MEASURE held_stdout_node_elapsed=%.3fs' % node_elapsed, flush=True)

    def test_tssh_rate_lock_wait_is_also_bounded(self):
        wrapper = self.b / 'tools' / 'tssh.sh'
        wrapper.write_text(wrapper.read_text().replace('last + 0', 'last + 35'))
        write(self.root / 'tssh' / 'last', str(int(time.time())))
        self.env['LCS_NODE_SECONDS'] = '0.15'
        result = self.run_driver()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn(b'trinity-1-18 stage rc=124', result.stdout)
        self.assertIn(b'SKIP trinity-2-28 (unreachable or silent; rc=124)', result.stdout)
        self.assertFalse((self.root / 'ssh.jsonl').exists())
        self.assertTrue((self.repo / 'lane_code' / 'trinity-3-30' / 'good.py').is_file())
        self.assertIn(b'committed', result.stdout)
        self.assertLess(self.elapsed, 2)

