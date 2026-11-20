from pathlib import Path
import shutil
J=Path.cwd();D=J/'work/build24m4z5';K=J/'out/kit_n'
p=K/'b/pc.py';s=(D/'before/kit_n/b/pc.py').read_text()
s=s.replace('import time\n','import time\nimport datetime\nimport runpy\nimport http.client\nfrom concurrent.futures import ThreadPoolExecutor, as_completed\n')
a=s.index('def put(');b=s.index('\ndef beneath',a)
s=s[:a]+'''def atomic_bytes(p, raw, mode=0o600):
    p = Path(p)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + '.part')
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, mode)
    with os.fdopen(fd, 'wb') as stream:
        os.fchmod(stream.fileno(), mode)
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    os.replace(tmp, p)
    fd = os.open(p.parent, os.O_RDONLY | os.O_DIRECTORY)
    try: os.fsync(fd)
    finally: os.close(fd)


def put(p, v):
    atomic_bytes(p, (json.dumps(v, sort_keys=True) + '\\n').encode())


def allocation_end(cfg=None):
    value = os.environ.get('SLURM_JOB_END_TIME', '')
    if value:
        try: return float(value)
        except ValueError:
            try: return datetime.datetime.fromisoformat(value).timestamp()
            except ValueError: pass
    if os.environ.get('TK_JOB_START'):
        recipe = (cfg or {}).get('recipe', {})
        seconds = float(recipe.get('wall_seconds', 86400))
        return float(os.environ['TK_JOB_START']) + seconds
    return time.time() + 150


def deadlines(cfg=None):
    end = allocation_end(cfg)
    # Finish bulk data before TERM@600, with another 180 s for evidence.
    if os.environ.get('TK_JOB_START') or os.environ.get('SLURM_JOB_END_TIME'):
        return end - 780, end - 600
    return end - 20, end - 10

''' +s[b:]
a=s.index('        if not cached.exists():');b=s.index('\n\n    def paths',a)
s=s[:a]+'''        if not cached.exists():
            raw = self.session_bytes()
            atomic_bytes(cached, raw)
        self.session_bytes(cached)
        self.bulk_end, self.final_end = deadlines(self.cfg)

''' +s[b:]
s=s.replace('    def session_bytes(self):','    def session_bytes(self, path=None):\n        path = Path(path) if path is not None else self.sessions')
s=s.replace('os.open(self.sessions.parent,','os.open(path.parent,').replace('os.stat(self.sessions.name,','os.stat(path.name,').replace('os.open(self.sessions.name,','os.open(path.name,')
s=s.replace('                if stat.S_IMODE(current.st_mode) != 0o600:',"                if current.st_uid != os.getuid():\n                    raise ValueError('file owner')\n                if stat.S_IMODE(current.st_mode) != 0o600:")
s=s.replace('            return raw\n        except OSError:', '''            expected = {key+'.j'+self.job+f'.part{i:02d}-of-04'
                        for key in self.names['objects'].values() for i in range(4)}
            if set(values) != expected or len(expected) != 108:
                raise ValueError('E101')
            return raw
        except OSError:''')
a=s.index('        try:\n            raw = (self.spool');b=s.index('        receipts = ',a)
s=s[:a]+'''        local = self.spool/'private/sess.json'
        self.session_bytes(local)
        label, key = self.claim(labels, identity)
        command = [sys.executable, '-B', str(self.writer), 'split', str(local), key, str(archive), '4', '4']
        if self.writer == self.kit/'b/gc.py':
            command = [sys.executable, '-I', '-s', '-B', str(self.kit/'b/pc.py'), '--writer', *command[2:]]
        limit = self.final_end if labels == ['o'] else self.bulk_end
        if time.time() >= limit:
            return
        with open('/dev/null', 'wb') as quiet:
            rc = subprocess.run(command, stdout=quiet, stderr=quiet,
                env={**os.environ, 'TK_COPY_DEADLINE':str(limit)}).returncode
        if rc:
            put(self.state/('gcs_'+directory.name+'.json'), dict(status='upload pending retry', object=key, returncode=rc))
            return
''' +s[b:]
a=s.index('    def exit_archive(self):');b=s.index('    def archive(',a)
s=s[:a]+'''    def exit_archive(self):
        # The embedded shell can make a provisional archive while logs still grow.
        if not self.final_pass or self.priority_pending():
            return
        archive = self.root/'o/o.tar'
        frozen = self.root/'o/frozen.json'
        if not frozen.is_file():
            with open('/dev/null', 'wb') as quiet:
                subprocess.run([sys.executable, '-I', '-s', '-B', str(self.kit/'b/o.py'),
                    str(self.root), str(self.exit_status or 0), '0', '--local', '--freeze'],
                    env={**os.environ, 'SLURM_JOB_ID':self.job},
                    stdout=quiet, stderr=quiet, check=True)
        if archive.is_file():
            if archive.stat().st_size > CAP:
                raise ValueError('E103')
            self.send(archive.parent, archive, ['o'], archive=archive)
            self.attempt('o_copy', self.copy_exit)

    def stop_marker(self):
        markers = list(self.train.glob('checkpoint_*/complete.json'))
        if not markers:
            return None
        latest = max(markers, key=lambda p:(read(p).get('step', -1),p.stat().st_mtime_ns))
        if self.final_pass:
            return latest
        # Native completion markers contain no stop bit. A completed run report
        # is the first unambiguous evidence available without changing the trainer.
        for report in self.train.glob('run_*.json'):
            value = read(report)
            step = value.get('steps', value.get('step', value.get('end_step')))
            if value.get('stop_reason') and step == read(latest).get('step'):
                return latest
        return None

    def stop_export(self):
        marker = self.stop_marker()
        if marker is None:
            return None
        p = self.train/('m'+str(read(marker)['step']))/'artifact.json'
        return p if p.is_file() else None

    def priority_pending(self):
        marker = self.stop_marker()
        if marker is not None and not (self.state/('gcs_'+marker.parent.name+'_stop.done')).is_file():
            return True
        export = self.stop_export()
        return export is not None and not (self.state/('gcs_'+export.parent.name+'.done')).is_file()

    def exports_pending(self):
        return any(not (self.state/('gcs_'+p.parent.name+'.done')).is_file()
                   for p in self.train.glob('m*/artifact.json') if p.parent.name[1:].isdigit())

    def incomplete(self):
        pending = []
        if self.priority_pending(): pending.append('stop')
        if self.exports_pending(): pending.append('exports')
        for p in self.train.glob('checkpoint_*/complete.json'):
            if not (self.state/('gcs_'+p.parent.name+'.done')).is_file(): pending.append(p.parent.name)
        for label in ('logs.done','gcs_o.done','o_copy.done'):
            if not (self.state/label).is_file(): pending.append(label)
        return pending

''' +s[b:]
s=s.replace("        for marker in sorted(self.train.glob('m*/artifact.json')):","        stop = self.stop_export()\n        for marker in sorted(self.train.glob('m*/artifact.json'), key=lambda p:(p != stop, str(p))):")
a=s.index('        markers = list(',s.index('    def stop_checkpoint'));b=s.index('        identity = sha(marker)',a)
s=s[:a]+'''        marker = self.stop_marker()
        if marker is None:
            put(self.state/'ckstop.json', dict(status='no completed checkpoint'))
            return
''' +s[b:]
s=s.replace('    def checkpoints(self):\n', '''    def checkpoints(self):
        if not self.final_pass or self.priority_pending() or self.exports_pending():
            return
''')
a=s.index('            if final:',s.index('    def pass_once'));b=s.index('\n\ndef main',a)
s=s[:a]+'''            phases = [('stop', [self.stop_checkpoint]),
                      ('exports', [self.exports]),
                      ('logs', [self.small] if small else []),
                      ('o', [self.exit_archive]),
                      ('checkpoints', [self.checkpoints])]
            for label, actions in phases:
                if final:
                    with (self.spool/'final_order.jsonl').open('a') as stream:
                        stream.write(json.dumps(dict(phase=label, time=time.time()))+'\\n')
                for action in actions:
                    try:
                        action()
                        if final and label == 'logs': put(self.state/'logs.done', dict(complete=True))
                    except Exception as error:
                        self.note(action.__name__, error)
''' +s[b:]
s=s.replace('def main():\n', "def main():\n    if len(sys.argv) > 1 and sys.argv[1] == '--writer':\n        return writer_main(sys.argv[2:])\n    if len(sys.argv) > 1 and sys.argv[1] == '--seconds':\n        print(max(1, int(deadlines()[1] - time.time()))); return\n")
s=s.replace('    final_end = time.monotonic()+140','    final_end = time.monotonic()+max(0, c.final_end-time.time())')
s=s.replace("            if args.final and time.monotonic() < final_end and not (\n                    (c.state/'gcs_o.done').is_file() and (c.state/'o_copy.done').is_file()):", "            if args.final and time.monotonic() < final_end and c.incomplete():")
s=s.replace('        for _ in range(10):','        for _ in range(1):')
s=s.replace("if __name__ == '__main__':\n    main()", "if __name__ == '__main__':\n    raise SystemExit(main())")
p.write_text(s)
