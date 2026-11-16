"""Run a kit's real batch entry with its production config on CPU, before review or submission.

CLI:
  dryrun.py run --kit KITDIR --config CONFIG.json --pins PINS.json [--map SRC=DST[:rw] ...]
                --out OUTDIR [options] -- <argv of the batch entry>

The entry runs exactly as the job would, with four differences and no others:
  1. Sandbox. bwrap hides /home, /data, /data2, /data3 (and every other /data*), gives a private
     /tmp and unshares the network. Only the kit copy, OUTDIR, the entry's interpreter tree, --ro
     paths and --map sources are visible under /scratch. --map binds staged files at the job's
     logical paths (read-only unless the DST ends in :rw).
  2. Config identity. The production CONFIG file is bound, unchanged, at the logical path of the
     pin with role "config"; its sha256 must equal that pin. No option edits, overlays or
     replaces a config field. Only an input or weights pin with a "standin" may be served by that
     stand-in, and the report lists every stand-in used.
  3. Transport shims. OUTDIR/shims/bin heads PATH, and is also bound over the absolute system
     paths of gcloud, gsutil, sbatch, squeue, sacct, scontrol, nvidia-smi, ssh and curl. Each shim
     serves pinned objects from local files (URI and generation honoured), or an exact-argv fixture
     from --calls, logs every call to OUTDIR/shim_calls.jsonl and fails an unplanned call.
  4. No GPU. CUDA_VISIBLE_DEVICES is empty; lines only a GPU runs are listed under not_proven.

Checks, in the order fail_reason reports them: pins_mismatch, config_mismatch, pin_mismatch,
config_lint, sandbox, unplanned_call, hidden_path, timeout, entry_failed, stage_not_reached,
items_short, dir_collision, closure_missing, closure_mismatch, closure_unpinned, tar_member_type,
row_schema, hardcoded_cap, unclassified_lines. The report is OUTDIR/DRYRUN_REPORT.json in the
orchkit-dryrun-v1 format, plus "fail_reasons" and "checks" with the detail of every check.

Classification file (--classify, orchkit-dryrun-classify-v1):
  {"schema": "orchkit-dryrun-classify-v1",
   "ranges": [{"file": "<kit-relative path>", "start": 1, "end": 9,
               "class": "unit_test|gpu_only|error_path", "test": "<test id>", "reason": "<text>"}],
   "caps": [{"file": "<kit-relative path>", "name": "<constant or option>", "reason": "<text>"}]}
A never-run range in a kit module the entry imported must lie inside one classified range of
its file; unit_test needs "test", error_path and gpu_only need "reason".

Standard library only; Python 3.6-safe. Nothing here removes a file.
"""
import argparse
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tarfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
try:
    from . import util
except ImportError:
    import util

SCHEMA = 'orchkit-dryrun-v1'
CLASSIFY_SCHEMA = 'orchkit-dryrun-classify-v1'
SHIM_NAMES = ('gcloud', 'gsutil', 'sbatch', 'squeue', 'sacct', 'scontrol', 'nvidia-smi', 'ssh',
              'curl')
SYSTEM_BIN = ('/usr/local/bin', '/usr/bin', '/bin', '/usr/sbin', '/sbin')
HIDDEN_FIXED = ('/home', '/data', '/data2', '/data3')
SKIP_ROOT = ('proc', 'dev', 'tmp', 'scratch', 'home')
STANDIN_ROLES = ('input', 'weights')
CLOSURE_ROLES = ('code', 'config', 'input', 'weights', 'record', 'env')
REASONS = ('pins_mismatch', 'config_mismatch', 'pin_mismatch', 'config_lint', 'sandbox',
           'unplanned_call', 'hidden_path', 'timeout', 'entry_failed', 'stage_not_reached',
           'items_short', 'dir_collision', 'closure_missing', 'closure_mismatch',
           'closure_unpinned', 'tar_member_type', 'row_schema', 'hardcoded_cap',
           'unclassified_lines')
TAR_TYPES = {tarfile.REGTYPE: 'file', tarfile.AREGTYPE: 'file', tarfile.DIRTYPE: 'dir',
             tarfile.SYMTYPE: 'symlink', tarfile.LNKTYPE: 'hardlink', tarfile.CHRTYPE: 'char',
             tarfile.BLKTYPE: 'block', tarfile.FIFOTYPE: 'fifo', tarfile.CONTTYPE: 'contiguous'}
HIDDEN_ERROR = re.compile(r"(?:No such file|Permission denied|Errno|not found|cannot access)"
                          r".*?['\"]?((?:/home|/data[0-9]*)/[^'\"\s]*)")


class Usage(Exception):
    pass


def under(path, root):
    root = root.rstrip('/') or '/'
    return path == root or path.startswith(root + '/') or root == '/'


def hidden_roots():
    roots = set(HIDDEN_FIXED)
    for name in os.listdir('/'):
        if re.match(r'^data[0-9]*$', name):
            roots.add('/' + name)
    return sorted(roots)


def parse_map(text):
    if '=' not in text:
        raise Usage('--map needs SRC=DST: ' + text)
    src, dst = text.split('=', 1)
    mode = 'ro'
    if dst.endswith(':rw'):
        dst, mode = dst[:-3], 'rw'
    src = os.path.abspath(src)
    if not os.path.isabs(dst) or '..' in dst.split('/'):
        raise Usage('--map DST must be a clean absolute path: ' + dst)
    if not os.path.exists(src):
        raise Usage('--map SRC does not exist: ' + src)
    return {'src': src, 'dst': os.path.normpath(dst), 'mode': mode}


def parse_kv(text, what):
    if '=' not in text:
        raise Usage('%s needs NAME=VALUE: %s' % (what, text))
    return text.split('=', 1)


def walk_strings(value, path=''):
    if isinstance(value, dict):
        for key in sorted(value):
            for item in walk_strings(value[key], '%s.%s' % (path, key) if path else str(key)):
                yield item
    elif isinstance(value, list):
        for i, item in enumerate(value):
            for sub in walk_strings(item, '%s[%d]' % (path, i)):
                yield sub
    elif isinstance(value, str):
        yield path, value


def check_pins(manifest):
    problems = []
    if manifest.get('schema') != 'orchkit-pins-v1':
        problems.append('schema is not orchkit-pins-v1')
    entries = manifest.get('entries')
    if not isinstance(entries, list):
        return problems + ['entries is not a list']
    paths = [e.get('logical_path') for e in entries]
    if paths != sorted(paths):
        problems.append('entries are not sorted by logical_path')
    if len(set(paths)) != len(paths):
        problems.append('a logical_path repeats')
    for e in entries:
        if not re.match(r'^[0-9a-f]{64}$', str(e.get('sha256'))):
            problems.append('%s: sha256 is not 64 hex' % e.get('logical_path'))
        if e.get('standin') and e.get('role') not in STANDIN_ROLES:
            problems.append('%s: a stand-in is allowed only for input or weights' % e.get('logical_path'))
    return problems


def bake(src, dst, values, first_line=None, mode=0o755):
    with open(src) as handle:
        text = handle.read()
    for name, value in values.items():
        line = '%s = %r' % (name, value)
        text, n = re.subn(r"(?m)^%s = .*$" % name, lambda m: line, text, count=1)
        if n != 1:
            raise RuntimeError('cannot bake %s into %s' % (name, src))
    if first_line is not None:
        text = first_line + '\n' + text.split('\n', 1)[1]
    with open(dst, 'w') as handle:
        handle.write(text)
    os.chmod(dst, mode)


def copy_kit(kit, dest):
    shutil.copytree(kit, dest, symlinks=True)


class DryRun(object):
    def __init__(self, args):
        self.args = args
        self.out = os.path.abspath(args.out)
        self.checks = {}
        self.reasons = []
        self.not_proven = []
        self.standins = []

    def fail(self, reason, detail=None):
        if reason not in self.reasons:
            self.reasons.append(reason)
        if detail is not None:
            self.checks.setdefault(reason, []).append(detail)

    # ---- inputs ----------------------------------------------------------------------------
    def load(self):
        a = self.args
        if os.path.exists(self.out) and os.listdir(self.out):
            raise Usage('--out must be a fresh directory: ' + self.out)
        for name in ('shims/bin', 'shims/pysite', 'shims/lib/orchkit', 'shims/wrap', 'traces',
                     'uploads', 'store'):
            os.makedirs(os.path.join(self.out, name))
        self.kit = os.path.abspath(a.kit)
        self.kit_at = os.path.normpath(a.kit_at or self.kit)
        self.config_path = os.path.abspath(a.config)
        with open(self.config_path, 'rb') as handle:
            self.config_bytes = handle.read()
        self.config_sha = util.sha256_bytes(self.config_bytes)
        self.config = json.loads(self.config_bytes.decode('utf-8'))
        self.pins = util.read_json(a.pins)
        self.kit_pins_sha = util.canonical_sha256(self.pins)
        self.maps = [parse_map(m) for m in a.map]
        self.argv = list(a.entry)
        if self.argv and self.argv[0] == '--':
            self.argv = self.argv[1:]
        if not self.argv:
            raise Usage('no entry argv after --')
        self.items_total = a.items_total if a.items_total is not None else self.config.get('n_items')
        self.hidden = hidden_roots()

    def check_identity(self):
        problems = check_pins(self.pins)
        if problems:
            self.fail('pins_mismatch', {'problems': problems})
        declared = self.config.get('kit_pins_sha256')
        if declared is not None and declared != self.kit_pins_sha:
            self.fail('pins_mismatch', {'config_kit_pins_sha256': declared,
                                        'manifest': self.kit_pins_sha})
        configs = [e for e in self.pins.get('entries', []) if e.get('role') == 'config']
        self.config_at = self.args.config_at and os.path.normpath(self.args.config_at)
        if len(configs) > 1:
            self.fail('config_mismatch', {'problem': 'the pins name %d config entries' % len(configs)})
        if configs:
            if self.config_at and self.config_at != configs[0]['logical_path']:
                self.fail('config_mismatch', {'problem': '--config-at differs from the config pin',
                                              'config_at': self.config_at,
                                              'logical_path': configs[0]['logical_path']})
            self.config_at = configs[0]['logical_path']
            if configs[0]['sha256'] != self.config_sha:
                self.fail('config_mismatch', {'config_sha256': self.config_sha,
                                              'pinned_sha256': configs[0]['sha256'],
                                              'logical_path': configs[0]['logical_path']})
        elif not self.config_at:
            raise Usage('--config-at is needed when the pins hold no config entry')
        expect = self.args.expect_config_sha256
        if expect and expect != self.config_sha:
            self.fail('config_mismatch', {'config_sha256': self.config_sha,
                                          'production_sha256': expect})
        for m in self.maps:
            if under(m['dst'], self.config_at) or under(self.config_at, m['dst']) and m['mode'] == 'rw':
                self.fail('config_mismatch', {'problem': '--map covers the config path',
                                              'dst': m['dst']})

    def local_for(self, entry):
        """Local bytes for a pin: a --map at its logical path, the --store copy, else a stand-in."""
        for m in self.maps:
            if m['dst'] == entry['logical_path'] and os.path.isfile(m['src']):
                return m['src'], False
        if self.args.store:
            candidate = os.path.join(self.args.store, entry['sha256'])
            if os.path.isfile(candidate):
                return candidate, False
        if entry.get('standin') and entry.get('role') in STANDIN_ROLES:
            return os.path.abspath(entry['standin']), True
        return None, False

    def plan(self):
        """Shim plan, bound pin files and the closure list."""
        objects, self.bound, self.closure, self.served = {}, [], [], []
        for entry in self.pins.get('entries', []):
            local, standin = self.local_for(entry)
            source = entry.get('source') or {}
            if local is not None and not standin:
                digest, _ = util.sha256_file(local)
                if digest != entry['sha256']:
                    self.fail('pin_mismatch', {'logical_path': entry['logical_path'],
                                               'local': local, 'actual': digest,
                                               'pinned': entry['sha256']})
            if standin:
                if not os.path.isfile(local):
                    self.fail('pin_mismatch', {'logical_path': entry['logical_path'],
                                               'problem': 'stand-in file missing', 'standin': local})
                    local = None
                else:
                    self.standins.append(entry['logical_path'])
            if local is not None:
                self.served.append({'logical_path': entry['logical_path'], 'path': local})
            if source.get('kind') == 'gcs' and local is not None:
                objects[source['uri']] = {'path': local, 'generation': source.get('generation'),
                                          'standin': standin, 'logical_path': entry['logical_path']}
                self.bound.append({'src': local, 'dst': local, 'mode': 'ro'})
            elif entry['role'] == 'config':
                pass
            elif local is not None and not any(m['dst'] == entry['logical_path'] for m in self.maps):
                self.bound.append({'src': local, 'dst': entry['logical_path'], 'mode': 'ro'})
            if entry.get('role') in CLOSURE_ROLES:
                expect = util.sha256_file(local)[0] if (standin and local) else entry['sha256']
                self.closure.append({'source': 'pin:' + entry['role'],
                                     'logical_path': entry['logical_path'],
                                     'path': self.alias(entry['logical_path']), 'sha256': expect})
        self.bound.append({'src': self.config_path, 'dst': self.config_at, 'mode': 'ro'})
        if not any(c['logical_path'] == self.config_at for c in self.closure):
            self.closure.append({'source': 'config', 'logical_path': self.config_at,
                                 'path': self.config_at, 'sha256': self.config_sha})
        pinned_uris = set((e.get('source') or {}).get('uri') for e in self.pins.get('entries', []))
        pinned_paths = set(e['logical_path'] for e in self.pins.get('entries', []))
        for path, value in walk_strings(self.config):
            if value.startswith('gs://'):
                base = value.split('#', 1)[0]
                if base not in pinned_uris and not any(u and u.startswith(base.rstrip('/') + '/')
                                                       for u in pinned_uris):
                    self.fail('closure_unpinned', {'config_path': path, 'uri': value})
            elif (value.startswith('/') and not re.search(r'\s', value) and value not in pinned_paths
                  and value != self.config_at):
                self.closure.append({'source': 'config:' + path, 'logical_path': value,
                                     'path': self.alias(value), 'sha256': None})
        calls = util.read_json(self.args.calls) if self.args.calls else []
        self.plan_path = os.path.join(self.out, 'shims', 'plan.json')
        util.write_json(self.plan_path, {
            'objects': objects, 'calls': calls, 'uploads': list(self.args.upload_prefix),
            'upload_dir': os.path.join(self.out, 'uploads'),
            'log': os.path.join(self.out, 'shim_calls.jsonl')})
        fixture_cmds = sorted(set(c['argv'][0] for c in calls if c.get('argv')))
        if fixture_cmds:
            self.not_proven.append('exact-argv fixtures stand in for: ' + ', '.join(fixture_cmds))

    def alias(self, logical):
        for item in self.args.alias:
            prefix, target = parse_kv(item, '--alias')
            if under(logical, prefix):
                return os.path.normpath(target + logical[len(prefix.rstrip('/')):])
        return logical

    # ---- sandbox ---------------------------------------------------------------------------
    def install(self):
        shims = os.path.join(self.out, 'shims')
        lib = os.path.join(shims, 'lib', 'orchkit')
        for name in ('__init__.py', 'util.py'):
            shutil.copyfile(os.path.join(HERE, name), os.path.join(lib, name))
        self.trace_py = os.path.join(shims, 'trace.py')
        roots = [self.kit_at] + [os.path.normpath(r) for r in self.args.trace_root]
        bake(os.path.join(HERE, 'shims', 'trace.py'), self.trace_py,
             {'TRACE_DIR': os.path.join(self.out, 'traces'), 'ROOTS': roots,
              'HIDDEN': self.hidden, 'TRACE_PY': self.trace_py}, mode=0o644)
        bake(os.path.join(HERE, 'shims', 'sitecustomize.py'),
             os.path.join(shims, 'pysite', 'sitecustomize.py'), {'TRACE_PY': self.trace_py},
             mode=0o644)
        shutil.copyfile(os.path.join(HERE, 'shims', 'runner.py'), os.path.join(shims, 'runner.py'))
        for name in SHIM_NAMES:
            bake(os.path.join(HERE, 'shims', 'shim.py'), os.path.join(shims, 'bin', name),
                 {'PLAN_PATH': self.plan_path, 'ORCHKIT_DIR': lib})
        self.wrapped = []
        for i, path in enumerate(self.args.wrap_python):
            real = os.path.realpath(path)
            inside = '/.orchkit_real/%d_%s' % (i, os.path.basename(real))
            wrapper = os.path.join(shims, 'wrap', '%d_%s' % (i, os.path.basename(real)))
            bake(os.path.join(HERE, 'shims', 'pywrap.py'), wrapper,
                 {'REAL': inside, 'TRACE_PY': self.trace_py}, first_line='#!%s -IS' % inside)
            self.wrapped.append({'real': real, 'inside': inside, 'wrapper': wrapper})

    def env_roots(self):
        """Interpreter trees under /scratch that the entry needs to start."""
        roots = []
        exe = self.argv[0]
        for candidate in (exe, os.path.realpath(exe)):
            if os.path.isabs(candidate) and under(candidate, '/scratch'):
                prefix = os.path.dirname(os.path.dirname(candidate))
                if prefix not in roots:
                    roots.append(prefix)
                cfg = os.path.join(prefix, 'pyvenv.cfg')
                if os.path.isfile(cfg):
                    with open(cfg) as handle:
                        for line in handle:
                            if line.split('=')[0].strip() == 'home':
                                home = os.path.dirname(os.path.realpath(line.split('=', 1)[1].strip()))
                                if under(home, '/scratch') and home not in roots:
                                    roots.append(home)
        return roots

    def bwrap_argv(self):
        argv = [self.args.bwrap, '--unshare-net', '--die-with-parent', '--proc', '/proc',
                '--dev', '/dev', '--tmpfs', '/tmp']
        hidden_names = set(h.lstrip('/') for h in self.hidden)
        for name in sorted(os.listdir('/')):
            full = '/' + name
            if name in SKIP_ROOT or name in hidden_names:
                continue
            if os.path.islink(full):
                argv += ['--symlink', os.readlink(full), full]
            elif os.path.isdir(full):
                argv += ['--ro-bind', full, full]
        for h in self.hidden:
            argv += ['--dir', h]
        argv += ['--dir', '/scratch', '--dir', '/tmp/home']
        binds = []
        for root in self.env_roots() + [os.path.abspath(r) for r in self.args.ro]:
            binds.append({'src': root, 'dst': root, 'mode': 'ro'})
        binds.append({'src': self.out, 'dst': self.out, 'mode': 'rw'})
        binds.append({'src': self.kit_copy, 'dst': self.kit_at, 'mode': 'rw'})
        binds += self.maps + self.bound
        for w in self.wrapped:
            binds.append({'src': w['real'], 'dst': w['inside'], 'mode': 'ro'})
            binds.append({'src': w['wrapper'], 'dst': w['real'], 'mode': 'ro'})
        for name in SHIM_NAMES:
            seen = set()
            for d in SYSTEM_BIN:
                target = os.path.join(d, name)
                real = os.path.realpath(target)
                if os.path.exists(target) and real not in seen:
                    seen.add(real)
                    binds.append({'src': os.path.join(self.out, 'shims', 'bin', name),
                                  'dst': real, 'mode': 'ro'})
        binds.sort(key=lambda b: b['dst'].count('/'))
        for b in binds:
            argv += ['--bind' if b['mode'] == 'rw' else '--ro-bind', b['src'], b['dst']]
        self.binds = binds
        return argv

    def environment(self):
        env = {'PATH': os.path.join(self.out, 'shims', 'bin') + ':/usr/local/bin:/usr/bin:/bin',
               'HOME': '/tmp/home', 'TMPDIR': '/tmp', 'LANG': 'C.UTF-8', 'LC_ALL': 'C.UTF-8',
               'CUDA_VISIBLE_DEVICES': '', 'PYTHONPATH': os.path.join(self.out, 'shims', 'pysite')}
        for item in self.args.env:
            key, value = parse_kv(item, '--env')
            if key in ('CUDA_VISIBLE_DEVICES', 'PATH', 'PYTHONPATH'):
                raise Usage('--env may not set ' + key)
            env[key] = value
        return env

    def run(self):
        self.kit_copy = os.path.join(self.out, 'kit')
        copy_kit(self.kit, self.kit_copy)
        spec = {'argv': self.argv, 'cwd': self.args.cwd or self.kit_at, 'trace': True,
                'trace_py': self.trace_py,
                'stages': [{'name': n, 'regex': r} for n, r in
                           (parse_kv(s, '--stage') for s in self.args.stage)],
                'item_regex': self.args.item_regex, 'timeout_s': self.args.timeout,
                'closure': self.closure, 'log': os.path.join(self.out, 'entry.log'),
                'result': os.path.join(self.out, 'runner.json')}
        util.write_json(os.path.join(self.out, 'run.json'), spec)
        argv = self.bwrap_argv() + ['--chdir', '/', '--', '/usr/bin/python3', '-I',
                                    os.path.join(self.out, 'shims', 'runner.py'),
                                    os.path.join(self.out, 'run.json')]
        util.write_json(os.path.join(self.out, 'bwrap_argv.json'), argv)
        start = time.time()
        with open(os.path.join(self.out, 'bwrap.log'), 'wb') as log:
            proc = subprocess.Popen(argv, env=self.environment(), stdout=log,
                                    stderr=subprocess.STDOUT)
            try:
                rc = proc.wait(timeout=self.args.timeout + 120)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait()
                self.fail('timeout', {'problem': 'sandbox did not exit'})
        self.seconds = time.time() - start
        path = os.path.join(self.out, 'runner.json')
        if not os.path.isfile(path):
            with open(os.path.join(self.out, 'bwrap.log'), 'rb') as handle:
                tail = handle.read()[-2000:].decode('utf-8', 'replace')
            self.fail('sandbox', {'rc': rc, 'log_tail': tail})
            self.result = None
            return
        self.result = util.read_json(path)

    # ---- after the run ---------------------------------------------------------------------
    def check_run(self):
        r = self.result
        self.stages = []
        if r is None:
            return
        for s in self.args.stage:
            name = s.split('=', 1)[0]
            seen = r['stages'].get(name)
            self.stages.append({'name': name, 'rc': 0 if seen is not None else None,
                                'seconds': seen})
            if seen is None and r['rc'] == 0:
                self.fail('stage_not_reached', {'stage': name})
        self.stages.append({'name': 'entry', 'rc': r['rc'], 'seconds': r['seconds']})
        if r.get('timed_out'):
            self.fail('timeout', {'timeout_s': self.args.timeout})
        elif r['rc'] != 0:
            self.fail('entry_failed', {'rc': r['rc'], 'error': r.get('error'),
                                       'log_tail': self.log_tail()})
        if self.args.item_regex and self.items_total is not None and r['items'] < self.items_total:
            self.fail('items_short', {'prepared': r['items'], 'total': self.items_total})
        for row in r['closure']:
            if row.get('problem') == 'missing':
                self.fail('closure_missing', row)
            elif row.get('problem'):
                self.fail('closure_mismatch', row)

    def log_tail(self):
        try:
            with open(os.path.join(self.out, 'entry.log'), 'rb') as handle:
                return handle.read()[-1500:].decode('utf-8', 'replace')
        except (IOError, OSError):
            return ''

    def check_shims(self):
        self.shim_calls = 0
        path = os.path.join(self.out, 'shim_calls.jsonl')
        if not os.path.isfile(path):
            return
        with open(path) as handle:
            for line in handle:
                row = json.loads(line)
                self.shim_calls += 1
                if not row.get('planned'):
                    self.fail('unplanned_call', {'argv': row['argv'], 'reason': row.get('reason')})

    def trace_rows(self):
        folder = os.path.join(self.out, 'traces')
        out = {'trace': [], 'hidden': [], 'mkdir': []}
        for name in sorted(os.listdir(folder)):
            full = os.path.join(folder, name)
            if name.startswith('trace_') and name.endswith('.json'):
                out['trace'].append(util.read_json(full))
            elif name.endswith('.jsonl'):
                kind = name.split('_', 1)[0]
                pid = int(name.rsplit('_', 1)[1].split('.')[0])
                with open(full) as handle:
                    for line in handle:
                        row = json.loads(line)
                        row['pid'] = pid
                        out.setdefault(kind, []).append(row)
        return out

    def check_fs(self, rows):
        for row in rows['hidden']:
            self.fail('hidden_path', {'event': row['event'], 'path': row['path'], 'pid': row['pid']})
        text = self.log_tail()
        for m in HIDDEN_ERROR.finditer(text):
            self.fail('hidden_path', {'from': 'entry.log', 'path': m.group(1)})
        creators = {}
        for row in rows['mkdir']:
            creators.setdefault(row['path'], {})[row['pid']] = row.get('argv')
        for path, pids in sorted(creators.items()):
            if (len(pids) > 1 and not under(path, os.path.join(self.out, 'traces'))
                    and os.path.basename(path) != '__pycache__'):
                self.fail('dir_collision', {'path': path, 'processes': [
                    {'pid': p, 'argv': a} for p, a in sorted(pids.items())]})
        if not rows['trace']:
            self.not_proven.append('no traced Python process: coverage, hidden-path and directory '
                                   'checks saw nothing')

    def kit_relative(self, path):
        if under(path, self.kit_at):
            return os.path.relpath(path, self.kit_at)
        return path

    def coverage(self, rows):
        classify = util.read_json(self.args.classify) if self.args.classify else {'ranges': [],
                                                                                   'caps': []}
        if classify.get('schema', CLASSIFY_SCHEMA) != CLASSIFY_SCHEMA:
            raise Usage('--classify is not ' + CLASSIFY_SCHEMA)
        files, imported = {}, set()
        for t in rows['trace']:
            imported.update(t.get('modules', []))
            for name, row in t['files'].items():
                key = (name, row['sha256'])
                agg = files.setdefault(key, {'executed': set(), 'possible': set(row['possible'])})
                agg['executed'].update(row['executed'])
                if row['executed']:
                    imported.add(name)
        never = []
        gpu = []
        for (name, digest), agg in sorted(files.items()):
            if name not in imported:
                continue
            rel = self.kit_relative(name)
            for start, end in ranges(sorted(agg['possible']), agg['executed']):
                rule = classified(classify.get('ranges', []), rel, start, end)
                cls = rule['class'] if rule else 'unclassified'
                never.append({'file': rel, 'start': start, 'end': end, 'class': cls})
                if cls == 'gpu_only':
                    gpu.append('%s:%d-%d (%s)' % (rel, start, end, rule.get('reason', '')))
                if cls == 'unclassified':
                    self.fail('unclassified_lines', {'file': rel, 'start': start, 'end': end})
        if gpu:
            self.not_proven.append('lines only a GPU runs: ' + '; '.join(gpu))
        self.check_caps(sorted(set(n for n, _ in files if n in imported)), classify.get('caps', []))
        return {'files': len(set(n for n, _ in files if n in imported)), 'lines_never_run': never}

    def check_caps(self, names, allowed):
        try:
            import lint_config
        except ImportError:
            self.not_proven.append('hard-coded caps not checked: lint_config is missing')
            return
        for name in names:
            rel = self.kit_relative(name)
            host = os.path.join(self.kit_copy, rel) if not os.path.isabs(rel) else rel
            try:
                with open(host) as handle:
                    source = handle.read()
            except (IOError, OSError):
                continue
            for item in lint_config.hardcoded_caps(source, rel):
                text = json.dumps(item, sort_keys=True)
                if not any(a.get('file') == rel and a.get('name') and a['name'] in text
                           and a.get('reason') for a in allowed):
                    self.fail('hardcoded_cap', dict(item, file=rel))

    def check_lint(self):
        try:
            import lint_config
        except ImportError:
            self.not_proven.append('config lint not run: lint_config is missing')
            return
        schema = util.read_json(self.args.schema) if self.args.schema else None
        words = lint_config.read_words(self.args.opacity_words) if self.args.opacity_words else None
        for item in lint_config.lint(self.config, schema, self.pins if self.args.lint_pins else None,
                                     words):
            self.fail('config_lint', item)

    def check_rows(self):
        if not self.args.rows:
            return
        import rowschema
        profile = rowschema.load_profile(self.args.row_profile)
        result = rowschema.check(rowschema.iter_rows(self.args.rows), profile, self.config)
        self.checks['rowschema'] = result
        if not result.get('ok', not result.get('violations')):
            self.fail('row_schema', {'rows': self.args.rows})

    def check_tars(self):
        allow_links = set(self.args.tar_links)
        files = [(s['logical_path'], s['path']) for s in self.served]
        upload_dir = os.path.join(self.out, 'uploads')
        files += [('upload:' + n, os.path.join(upload_dir, n)) for n in sorted(os.listdir(upload_dir))]
        scanned = 0
        for logical, path in files:
            try:
                if not os.path.isfile(path) or not tarfile.is_tarfile(path):
                    continue
            except (IOError, OSError):
                continue
            scanned += 1
            allowed = {'file', 'dir'} | ({'symlink', 'hardlink'} if logical in allow_links else set())
            bad = {}
            with tarfile.open(path, 'r:*') as archive:
                for member in archive:
                    kind = TAR_TYPES.get(member.type, 'other:%r' % member.type)
                    if kind not in allowed:
                        bad.setdefault(kind, []).append(member.name)
            for kind, names in sorted(bad.items()):
                self.fail('tar_member_type', {'archive': logical, 'type': kind, 'count': len(names),
                                              'first': names[:5]})
        self.checks['tar_archives_scanned'] = scanned

    def report(self, coverage):
        r = self.result or {}
        ordered = [x for x in REASONS if x in self.reasons]
        if self.standins:
            self.not_proven.append('stand-ins served instead of pinned bytes: '
                                   + ', '.join(self.standins))
        self.not_proven.append('GPU code paths, real transport and real batch-host mounts are '
                               'proven only by the GPU canary')
        rep = {'schema': SCHEMA, 'utc': util.utc_iso(), 'kit_pins_sha256': self.kit_pins_sha,
               'config_sha256': self.config_sha, 'entry': self.argv,
               'stages': getattr(self, 'stages', []), 'items_total': self.items_total,
               'items_prepared': r.get('items', 0) if self.args.item_regex else None,
               'standins': self.standins, 'shim_calls': getattr(self, 'shim_calls', 0),
               'coverage': coverage, 'not_proven': self.not_proven,
               'verdict': 'FAIL' if ordered else 'PASS',
               'fail_reason': ordered[0] if ordered else None, 'fail_reasons': ordered,
               'checks': self.checks}
        util.write_json(os.path.join(self.out, 'DRYRUN_REPORT.json'), rep)
        return rep


def ranges(possible, executed):
    """Group never-run lines into ranges of consecutive possible lines."""
    out, start, prev = [], None, None
    for line in possible:
        if line in executed:
            if start is not None:
                out.append((start, prev))
                start = None
            continue
        if start is None:
            start = line
        prev = line
    if start is not None:
        out.append((start, prev))
    return out


def classified(rules, rel, start, end):
    for rule in rules:
        if rule.get('file') != rel or not (rule['start'] <= start and end <= rule['end']):
            continue
        cls = rule.get('class')
        if cls == 'unit_test' and rule.get('test'):
            return rule
        if cls in ('gpu_only', 'error_path') and rule.get('reason'):
            return rule
    return None


def run(args):
    d = DryRun(args)
    d.load()
    d.check_identity()
    d.check_lint()
    d.plan()
    d.install()
    coverage = {'files': 0, 'lines_never_run': []}
    if 'config_mismatch' in d.reasons or 'pins_mismatch' in d.reasons:
        d.not_proven.append('entry not run: the config or pins do not match')
        d.result = None
    else:
        d.run()
        d.check_run()
        d.check_shims()
        rows = d.trace_rows()
        d.check_fs(rows)
        coverage = d.coverage(rows)
    d.check_tars()
    d.check_rows()
    return d.report(coverage)


def parser():
    p = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = p.add_subparsers(dest='cmd')
    r = sub.add_parser('run')
    r.add_argument('--kit', required=True)
    r.add_argument('--kit-at', help='logical path where the job sees the kit (default: KITDIR)')
    r.add_argument('--config', required=True)
    r.add_argument('--config-at', help='logical path where the job reads CONFIG (default: the '
                   'config pin)')
    r.add_argument('--expect-config-sha256', help='production config identity, for example from '
                   'the launch record')
    r.add_argument('--pins', required=True)
    r.add_argument('--map', action='append', default=[])
    r.add_argument('--out', required=True)
    r.add_argument('--store', help='directory of local copies named by sha256')
    r.add_argument('--calls', help='JSON list of exact-argv shim fixtures {argv, stdout, rc}')
    r.add_argument('--upload-prefix', action='append', default=[])
    r.add_argument('--classify')
    r.add_argument('--stage', action='append', default=[], help='NAME=REGEX on the entry output')
    r.add_argument('--item-regex')
    r.add_argument('--items-total', type=int)
    r.add_argument('--alias', action='append', default=[],
                   help='LOGICAL_PREFIX=PATH: where the closure check looks for a logical path')
    r.add_argument('--tar-links', action='append', default=[],
                   help='logical path of an archive allowed to hold links')
    r.add_argument('--ro', action='append', default=[], help='extra read-only host path')
    r.add_argument('--trace-root', action='append', default=[])
    r.add_argument('--wrap-python', action='append', default=[],
                   help='system interpreter path to trace through a wrapper (children run -I)')
    r.add_argument('--env', action='append', default=[])
    r.add_argument('--cwd')
    r.add_argument('--schema')
    r.add_argument('--opacity-words')
    r.add_argument('--lint-pins', action='store_true')
    r.add_argument('--rows')
    r.add_argument('--row-profile')
    r.add_argument('--timeout', type=int, required=True)
    r.add_argument('--bwrap', default='/usr/bin/bwrap')
    r.add_argument('entry', nargs=argparse.REMAINDER)
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    if args.cmd != 'run':
        parser().print_help()
        return 2
    if args.rows and not args.row_profile:
        sys.stderr.write('dryrun: --rows needs --row-profile\n')
        return 2
    try:
        rep = run(args)
    except Usage as err:
        sys.stderr.write('dryrun: %s\n' % err)
        return 2
    sys.stdout.write('%s %s %s\n' % (rep['verdict'], rep['fail_reason'] or '-',
                                     os.path.join(os.path.abspath(args.out), 'DRYRUN_REPORT.json')))
    return 0 if rep['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
