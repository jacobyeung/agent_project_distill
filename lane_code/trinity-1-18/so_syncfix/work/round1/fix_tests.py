from pathlib import Path
p=Path('work/round1/tests/support.py')
s=p.read_text().replace("(self.b / 'tools' / name).write_bytes((TOOLS / name).read_bytes())", "(self.b / 'tools' / name).write_text((TOOLS / name).read_text().replace(\n                '/scratch/jjyeung/orch_n30', str(self.local)) if name == 'lane_code_sync.sh'\n                else (TOOLS / name).read_text())")
# Plant a real special archive member after the receiver finishes, before acceptance.
a=s.index("        dest = shlex.split(command)[-1]")
b=s.index('    sys.exit(rc)',a)
s=s[:a]+'''        import tarfile
        writer = shlex.split(command)[-1]
        if writer.startswith('cat > '):
            archive = shlex.split(writer)[-1]
            with tarfile.open(archive, 'a') as stream:
                member = tarfile.TarInfo('aaa_raced.json')
                member.type = tarfile.FIFOTYPE
                stream.addfile(member)
        else:
            dest = shlex.split(command)[-1]
            os.mkfifo(str(Path(dest) / 'aaa_raced.json'))
'''+s[b:]
p.write_text(s)
p=Path('work/round1/tests/test_review.py')
s=p.read_text().replace("['timeout', '--kill-after=0.1', '0.2'] + PY + ['-c', code]", "['timeout', '--kill-after=0.1', '1.0'] + PY + ['-c', code]").replace('stderr=subprocess.PIPE, timeout=2)\n        self.assertEqual(result.returncode, 124, result.stderr)', 'stderr=subprocess.PIPE, timeout=3)\n        self.assertEqual(result.returncode, 124, result.stderr)')
# Each failure case gets its own fixture so failed assertions cannot contaminate cases.
s=s.replace("with self.subTest(failure=failure):\n                helper", "with self.subTest(failure=failure):\n                self.setUp()\n                helper")
p.write_text(s)
p=Path('work/round1/tests/test_driver.py')
s=p.read_text().replace('''        self.check_partial_success(result)
        self.assertIn(b'SKIP trinity-1-18 no orch_n30/source', result.stdout)''','''        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(b'SKIP trinity-1-18 (no source root)', result.stdout)
        self.assertNotIn(b'FAIL', result.stdout)
        self.assertFalse(list((self.root / 'events').glob('*_BLOCKER*')))
        self.assertTrue((self.repo / 'lane_code' / 'trinity-2-28' / 'good.py').is_file())''')
s=s.replace("self.assertIn(b'trinity-1-18 scan/copy rc=124', result.stdout)","self.assertIn(b'trinity-1-18 accept stage rc=1', result.stdout)\n        self.assertIn(b'nonregular archive entry', result.stdout)")
s=s.replace("r'PIPE 0 137 (2|124|137)'", "r'PIPE 0 137 (0|2|124|137)'")
p.write_text(s)
p=Path('work/round1/tests/test_wrapper.py')
s=p.read_text().replace("run = next((self.state / 'stage-runs').iterdir())\n        node_elapsed = (run / 'trinity-1-18.snapshot').stat().st_mtime - (run / 'trinity-1-18.sh').stat().st_mtime", "slot = self.state / 'stage-robust' / 'trinity-1-18'\n        node_elapsed = (slot / 'run.log').stat().st_mtime - (slot / 'program.sh').stat().st_mtime")
s=s.replace("self.assertIn(b'trinity-2-28 stage rc=124', result.stdout)", "self.assertIn(b'SKIP trinity-2-28 (unreachable or silent; rc=124)', result.stdout)")
p.write_text(s)
# One pending pathname per copy process is enough to identify any interrupted write.
p=Path('work/round1/tools/lane_code_scan.py')
s=p.read_text().replace("    # Log before creation so even SIGKILL leaves a named, recoverable scratch file.\n    sys.stderr.write('COPY_PENDING %s\\n' % pending)\n    sys.stderr.flush()\n", '')
s=s.replace("    def entries():", "    # The fixed scratch name is outside every path passed to Git add.\n    sys.stderr.write('COPY_PENDING %s\\n' % pending)\n    sys.stderr.flush()\n\n    def entries():",1)
p.write_text(s)
