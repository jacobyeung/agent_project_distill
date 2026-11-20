"""Stage authenticated inputs and publish one CPU result."""
from pathlib import Path
import base64
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tarfile
import time
import runpy
import sqlite3
from contextlib import contextmanager

DB = '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'
RD = 'bc2db7747322d4c3eda8372ce4c9a3e74d457baa609f2798c465bf4054e75d92'
LIMIT = 5_000_000


def attach(kit):
    sys.path.insert(0, str(Path(kit)/'b'))
    import z
    z.seal(kit)
    return z


class Parts:
    def __init__(self, paths):
        self.paths = iter(paths)
        self.stream = None
    def read(self, size=-1):
        if size < 0:
            return b''.join(iter(lambda: self.read(8 << 20), b''))
        out = bytearray()
        while len(out) < size:
            if self.stream is None:
                p = next(self.paths, None)
                if p is None:
                    break
                self.stream = open(p, 'rb')
            raw = self.stream.read(size-len(out))
            if raw:
                out.extend(raw)
            else:
                self.stream.close(); self.stream = None
        return bytes(out)
    def close(self):
        if self.stream is not None:
            self.stream.close()


class Inputs:
    def __init__(self, kit, root):
        self.kit, self.root = Path(kit), Path(root)
        self.z = attach(kit)
        self.spec = self.z.load(self.kit/'k/p.json')
        self.current = self.z.load(self.kit/'k/l.json')
        self.sources, self.records, self.archives = {}, {}, {}
        self.h = self.root/'h'; self.h.mkdir(exist_ok=True)
        for name in ('b/s.py', 'b/kitx.py'):
            self.host_file(name)
        spec = importlib.util.spec_from_file_location('q_stage', self.h/'b/s.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.stage = module.Stage(self.h, self.root/'s')
        import px
        self.px = px
        self.resolve = px.resolver
        os.environ['Q_ROOT'] = str(self.root)

    def host_file(self, name):
        h = self.spec['p_files'][name]
        source = (Path(self.spec['n_root'])/self.spec['p_sources'][name] if name in self.spec.get('p_sources', {})
                  else Path(self.spec['pool'])/self.spec['p_root']/name)
        target = self.z.inside(self.h, name); target.parent.mkdir(parents=True, exist_ok=True)
        self.z.checked(source, h)
        shutil.copyfile(source, target); self.z.checked(target, h)
        return target

    def put(self, source, h, size, dest, field):
        self.stage.publish(source, dest, h, size)
        self.sources[h] = str(dest)
        self.records[h] = dict(bytes=size, field=field)
        return str(dest)

    def file(self, source, h, field, size=None, dest=None):
        source = Path(source)
        size = source.stat().st_size if size is None else size
        if source.stat().st_size != size:
            raise ValueError('R1_STAGED_PIN_SIZE_DIFFERS:'+h)
        with source.open('rb') as stream:
            return self.put(stream, h, size, dest or self.root/'u'/h, field)

    def member(self, paths, h, field, names=None, dest=None):
        # A single-file tar stays open so separate requested members do not
        # restage the archive or materialize its unrelated payloads.
        if len(paths) == 1:
            key = str(paths[0])
            if key not in self.archives:
                self.archives[key] = tarfile.open(paths[0], 'r:*')
            archive = self.archives[key]
            members = archive.getmembers()
            def finish(): pass
        else:
            stream = Parts(paths)
            archive = tarfile.open(fileobj=stream, mode='r|*')
            members = archive
            def finish(): archive.close(); stream.close()
        try:
            for m in members:
                if not m.isfile() or m.issym() or m.islnk():
                    continue
                if names is not None and m.name not in names:
                    continue
                # Small metadata lookup is content-addressed. Large row bodies
                # always have an explicit member name in the sealed inventory.
                if names is None and m.size > 50_000_000:
                    continue
                if names is None:
                    with archive.extractfile(m) as f:
                        raw = f.read()
                    if hashlib.sha256(raw).hexdigest() != h:
                        continue
                    payload = io.BytesIO(raw)
                else:
                    payload = archive.extractfile(m)
                with payload:
                    return self.put(payload, h, m.size, dest or self.root/'u'/h, field)
        finally:
            finish()
        raise ValueError('R1_STAGED_PIN_MISSING:'+h+':'+field)

    def need(self, h, field='p'):
        if h in self.sources:
            return self.sources[h]
        uploads = {r['sha256']: r for r in self.spec['uploads']}
        if h in uploads:
            return self.file(Path(self.spec['n_root'])/'u'/h, h, field, uploads[h]['bytes'])
        for name, expected in self.spec['p_files'].items():
            if expected == h:
                source = (Path(self.spec['n_root'])/self.spec['p_sources'][name] if name in self.spec.get('p_sources', {})
                          else Path(self.spec['pool'])/self.spec['p_root']/name)
                return self.file(source, h, field)
        for entry in self.current.get('extra', []) + ([self.current['a1rows']] if 'a1rows' in self.current else []):
            if entry['sha256'] == h:
                dest = self.px.staged_path(entry['dest'], self.root)
                stream = Parts(entry['parts'])
                try:
                    self.put(stream, h, sum(Path(p).stat().st_size for p in entry['parts']), dest, field)
                finally:
                    stream.close()
                return self.px.resolver(self.kit, self.root, self.sources)(h, field)
        for entry in self.current.get('tars', []):
            names = [n for n, v in entry['files'].items() if v == h]
            if names:
                dest = self.px.staged_path(self.px.AWS+'/'+names[0], self.root, True)
                self.member(entry['parts'], h, field, names, dest)
                return self.px.resolver(self.kit, self.root, self.sources)(h, field)
        staged = self.current.get('staged_inputs', {})
        for entry in staged.get('files', []):
            if entry['sha256'] == h:
                self.stage.file(entry)
                p = self.stage.destination(entry['destination'])
                self.sources[h] = str(p); self.records[h] = dict(bytes=p.stat().st_size, field=field)
                return self.px.resolver(self.kit, self.root, self.sources)(h, field)
        for entry in staged.get('packages', []):
            for item in entry['inventory']:
                if item['sha256'] == h:
                    dest = self.stage.destination(entry['destination']+'/'+item['name'])
                    self.member([entry['source']], h, field, [item['name']], dest)
                    return self.px.resolver(self.kit, self.root, self.sources)(h, field)
        # Resolve selected metadata through the kit's authenticated handover
        # reader. No checkpoint part or weight file is opened or copied here.
        handover = self.z.pool_file(self.spec['pool'], Path(self.spec['pool'])/self.spec['milestone']/'s.tar')
        with tarfile.open(handover) as archive:
            raw = archive.extractfile('MANIFEST.json').read()
        if hashlib.sha256(raw).hexdigest() != self.spec['m4']['v']:
            raise ValueError('R1_STAGED_PIN_MANIFEST_DIFFERS')
        manifest = json.loads(raw)
        if h in {item['sha256'] for item in manifest['files']}:
            values, metadata = self.z.small_archive(handover, roots=[dict(path='p.json', sha256=h)])
            if h in values:
                return self.member([str(handover)], h, field, [values[h]['member']])
        # The same pinned small archive used by the kit supplies metadata;
        # retain only the requested member, authenticated by its content pin.
        small = self.current.get('small')
        if small:
            try:
                return self.member([small['file']], h, field)
            except ValueError as error:
                if not str(error).startswith('R1_STAGED_PIN_MISSING:'):
                    raise
        raise ValueError('R1_STAGED_PIN_MISSING:'+h+':'+field)

    def value(self, pin):
        return self.z.load(self.need(pin['sha256']))

    def visit(self, value):
        if isinstance(value, dict):
            if 'path' in value and 'sha256' in value:
                self.need(value['sha256'])
            else:
                for v in value.values(): self.visit(v)
        elif isinstance(value, list):
            for v in value: self.visit(v)

    def model_file(self, name, h):
        try:
            return self.need(h)
        except ValueError as error:
            if not str(error).startswith('R1_STAGED_PIN_MISSING:'): raise
        archive_path = self.current['model']['file']
        if archive_path not in self.archives:
            self.archives[archive_path] = tarfile.open(archive_path, 'r:*')
        names = [m.name for m in self.archives[archive_path].getmembers()
                 if m.isfile() and '/snapshots/'+self.revision+'/' in m.name and m.name.endswith('/'+name)]
        if len(names) != 1:
            raise ValueError('R1_STAGED_PIN_MISSING:'+h+':p')
        return self.member([archive_path], h, 'p', names)

    def closure(self):
        cfg = self.z.load(self.kit/'k/n.json')
        p = self.value(cfg['r1_training']['p_run']['config'])
        receipt = self.value(p['streams']['routing'])
        if receipt['database']['sha256'] != '4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84':
            raise ValueError('R1_RECONSTRUCTION_DATABASE_DIFFERS')
        if receipt['materialization']['sha256'] != '0c38bc96bb4566c2dc5aa17e1543995954b51401032fad02f0ce67e15f5d898a':
            raise ValueError('R1_RECONSTRUCTION_RECIPE_DIFFERS')
        recipe = self.value(receipt['materialization'])
        self.visit(p['code']); self.visit(cfg['r1_training']['p_tree'])
        for key in ('remove_files', 'dev_scene_exclusions', 'benchmark_scene_exclusions', 's1_route_policy'):
            self.visit(p.get(key))
        for key in ('inputs', 'legacy', 'division', 'base_model'): self.visit(recipe[key])
        for h in recipe['inputs'].get('catalog', {}): self.need(h)
        legacy = self.value(recipe['legacy'])
        self.visit({k:legacy[k] for k in ('database', 'division')})
        selection = self.value(recipe['inputs']['selection'])
        for key in ('manifest', 'remove_files', 'tokenizer'): self.visit(selection.get(key))
        for item in selection['sources'].values():
            if item['status'] == 'ELIGIBLE': self.visit({k:item[k] for k in ('source', 'selection')})
        manifest = self.value(selection['manifest'])
        for item in manifest['exclusions'].values():
            if isinstance(item, dict):
                for key in ('list', 'withhold', 'v2'):
                    if key in item: self.need(item[key+'_sha256'])
        model = self.value(recipe['base_model'])
        self.revision = model['base_identity']
        for name, h in model['files'].items():
            if name.endswith(('.json', '.txt', '.jinja', '.model')): self.model_file(name, h)
        import rb
        from student_pilot.r1_persisted import scope
        with scope(self.sources):
            mounts = rb.mount_inputs(p, recipe)
        self.z.write(self.root/'plan.json', dict(config=cfg, paths=self.sources, mounts=mounts, inputs=self.records))

    def environment(self):
        v = self.current['venv']
        subprocess.run([sys.executable, '-I', '-s', '-B', str(self.h/'b/kitx.py'), v['file'], v['sha256'], str(self.root/'v')], check=True)
        np = self.current['np']
        source = self.need(np['sha256'], 'e')
        subprocess.run([sys.executable, '-I', '-s', '-B', str(self.h/'b/kitx.py'), source, np['sha256'], str(self.root/'np')], check=True)
        # The overlay is authenticated by its pinned member manifest, as in j.sh.
        a = Path(self.current['small']['file']).parent/'d00'
        f = self.root/'f'; f.mkdir()
        with tarfile.open(a) as t:
            t.extractall(f, filter='data')
        manifests = list(f.rglob('m.sha'))
        matches = [p for p in manifests if self.z.sha(p) == self.current['fla']['sha256']]
        if len(matches) != 1: raise ValueError('R1_STAGED_PIN_MISSING:'+self.current['fla']['sha256'])
        m = matches[0]; overlay = m.parent/'p'
        for line in m.read_text().splitlines():
            h, name = line.split(None, 1)
            self.z.checked(self.z.inside(overlay, name.lstrip('*')), h)
        self.z.write(self.root/'env.json', dict(venv=str(self.root/'v'), paths=[str(overlay), str(self.root/'np')]))


def stage(kit, root, job='', mode='b'):
    z = attach(kit); start = time.monotonic()
    try:
        root = Path(root)
        if mode not in ('b', 'r'): raise ValueError('R1_MODE_INVALID')
        z.write(root/'mode.json', dict(mode=mode))
        source = z.load(Path(kit)/'k/a.json')['source']
        code = root/'c'
        with tarfile.open(z.checked(Path(kit)/source['path'], source['sha256'])) as t:
            t.extractall(code, filter='data')
        sys.path.insert(0, str(code))
        inputs = Inputs(kit, root)
        try:
            if mode == 'b':
                inputs.closure()
                inputs.environment()
            else:
                # Resolve the authenticated handover exactly as the kit does.
                # Its native staging hook requires the export parts, too.
                resolved = z.resolve(kit, inputs.spec['pool'], None, root/'resolved.json')
                inputs.environment()
                e = z.load(root/'env.json')
                v = inputs.current['closure']
                subprocess.run([sys.executable, '-I', '-s', '-B', str(inputs.h/'b/kitx.py'), v['file'], v['sha256'], str(root/'cl')], check=True)
                e['paths'] += [str(Path(kit)/'b'), str(root/'cl'), str(root/'cl/site_alias')]
                m = root/'m'; m.mkdir()
                supplied = {v['sha256']:v['path'] for v in resolved.get('external_metadata', [])}
                with tarfile.open(resolved['archive']['path']) if resolved['archive'] else context_empty() as archive:
                    for name, h in resolved['model_files'].items():
                        if not name.endswith(('.json', '.txt', '.jinja', '.model')): continue
                        dest = z.inside(m, name); dest.parent.mkdir(parents=True, exist_ok=True)
                        if h in supplied:
                            inputs.file(supplied[h], h, 'e', dest=dest)
                        elif h in resolved['small_files']:
                            item = resolved['small_files'][h]
                            if archive:
                                with archive.extractfile(item['member']) as f:
                                    inputs.put(f, h, item['bytes'], dest, 'e')
                            else: inputs.file(item['path'], h, 'e', item['bytes'], dest)
                        else: raise ValueError('R1_STAGED_PIN_MISSING:'+h)
                # Mode r resolves frame metadata but never opens RGB payloads.
                # The native planner still walks these two unpinned directory
                # arguments, so expose their empty mountpoints, as in discovery.
                g = root/'g'; g.mkdir()
                if root.is_relative_to('/scratch'):
                    (g/root.relative_to('/scratch')).mkdir(parents=True)
                for location in resolved['request']['frame_roots']:
                    p = Path(location)
                    if not p.is_relative_to('/scratch'): raise ValueError('R1_FRAME_ROOT_LOCATION_DIFFERS')
                    (g/p.relative_to('/scratch')).mkdir(parents=True, exist_ok=True)
                alias = g/'fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/8865619b/models'
                suffix = resolved['model_root'].split('/models/', 1)[1]
                snapshot = alias/suffix; snapshot.mkdir(parents=True)
                for p in m.rglob('*'):
                    if p.is_file():
                        dest = snapshot/p.relative_to(m); dest.parent.mkdir(parents=True, exist_ok=True); os.link(p,dest)
                v = inputs.current['record']
                record = root/'e.json'; inputs.file(inputs.need(v['sha256'], 'e'), v['sha256'], 'e', dest=record)
                e.update(mounts=[[str(m), resolved['model_root']]], scratch=str(g), record=str(record))
                z.write(root/'env.json', e)
                (root/'dr').mkdir()
                rc = launch(kit, root, job, action='plan')
                if rc: raise ValueError('R1_PLAN_REFUSED:'+str(rc))
        finally:
            for a in inputs.archives.values(): a.close()
    finally:
        z.write(Path(root)/'staging.json', dict(seconds=time.monotonic()-start))


@contextmanager
def context_empty():
    yield None


def host_root():
    out = []
    for name in sorted(os.listdir('/')):
        if name in ('proc', 'dev', 'tmp', 'scratch'): continue
        p = '/' + name
        if os.path.islink(p): out += ['--symlink', os.readlink(p), p]
        elif os.path.isdir(p): out += ['--ro-bind', p, p]
    return out


def launch(kit, root, job, action='run'):
    z = attach(kit); root = Path(root)
    e = z.load(root/'env.json')
    logical = '/project/community/jjyeung/c7d31ddd/venvs'
    executable = logical+'/rwtrain_torch211_cu129/bin/python'
    pin = z.load(Path(kit)/'k/l.json')['bwrap']
    binary = z.checked(pin['file'], pin['sha256'])
    if str(binary) != '/project/community/jjyeung/cp4tk_rt/kit/bwrap':
        raise ValueError('R1_BINARY_LOCATION_DIFFERS')
    mode = z.load(root/'mode.json')['mode'] if (root/'mode.json').is_file() else 'b'
    if mode == 'r':
        # The host has no /scratch and its / cannot take new mountpoints: build the root
        # from the host's top-level entries so /scratch can be created inside the sandbox.
        cmd = [str(binary), *host_root(), '--dev-bind', '/dev', '/dev', '--proc', '/proc']
        cmd += ['--tmpfs', '/project/community/jjyeung/c7d31ddd', '--tmpfs', '/tmp', '--ro-bind', e['scratch'], '/scratch']
    else:
        cmd = [str(binary), '--ro-bind', '/', '/', '--dev-bind', '/dev', '/dev', '--proc', '/proc']
    cmd += ['--bind', str(root), str(root)]
    cmd += ['--ro-bind', e['venv'], logical]
    for source, dest in e.get('mounts', []): cmd += ['--ro-bind', source, dest]
    if mode == 'r':
        for path in e['paths']:
            if Path(path).is_relative_to(root): cmd += ['--ro-bind', path, path]
        namespace = z.load(Path(kit)/'k/p.json')['namespace']
        cmd += ['--bind', str(root/'dr'), namespace,
                '--remount-ro', '/tmp',
                '--remount-ro', '/project/community/jjyeung/c7d31ddd',
                '--setenv', 'PYTHONPATH', os.pathsep.join(e['paths']),
                '--setenv', 'PATH', '/project/community/jjyeung/cp4tk_rt/kit:'+str(root/'cl/provenance_bin')+':'+logical+'/rwtrain_torch211_cu129/bin:/usr/local/bin:/usr/bin:/bin',
                '--setenv', 'R1_TRAINER', str(root/'c') if action=='plan' else namespace+'/p/s',
                '--setenv', 'TRAINER', str(root/'c') if action=='plan' else namespace+'/p/s',
                '--setenv', 'ANYHOST_JOBS', str(root/'cl'),
                '--setenv', 'R1_RUNTIME_RECORD', e['record'], '--setenv', 'ANYHOST_NEUTRAL_RUNTIME', e['record']]
    flags = ['-s', '-B'] if mode=='r' else ['-I', '-s', '-B']
    cmd += ['--chdir', str(root), executable, *flags, str(Path(__file__).resolve()), action, str(kit), str(root), job]
    return subprocess.run(cmd, check=False, env={**os.environ, 'Q_ROOT':str(root), "PATH":"/project/community/jjyeung/cp4tk_rt/kit:/usr/local/bin:/usr/bin:/bin"}).returncode


def plan_r(kit, root, job):
    """Ask the actual planner for its pins; stage each requested source once."""
    z = attach(kit); root = Path(root); e = z.load(root/'env.json')
    sys.path[:0] = [str(root/'c'), *e['paths']]
    import px
    from pl import plan_payload
    inputs = Inputs(kit, root)
    original = px.resolver
    def selected(k, r, sources):
        def need(h, field):
            if h not in sources:
                sources[h] = inputs.need(h, field)
            return sources[h]
        return need
    px.resolver = selected
    planned = Path(inputs.spec['namespace'])/'z'; planned.mkdir()
    try:
        resolved = z.load(root/'resolved.json')
        request, paths, hook = plan_payload(kit, resolved, planned, regeneration=True)
        hook.close()
        value = z.load(planned/'plan.json')
        z.write(root/'pins.json', dict(entries=value['entries'], requested=inputs.records,
            paths=inputs.sources, generated=value['generated'], parts=resolved['parts']))
        z.write(root/'dr/r.json', dict(_resolved=resolved))
    finally:
        px.resolver = original
        for a in inputs.archives.values(): a.close()


def run_r(kit, root, job):
    z = attach(kit); root = Path(root)
    import px
    original = px.resolver
    paths = z.load(root/'pins.json')['paths']
    def selected(k, r, sources):
        for h, p in paths.items():
            z.checked(p, h); sources.setdefault(h, p)
        return original(k, r, sources)
    px.resolver = selected
    namespace = z.load(Path(kit)/'k/p.json')['namespace']
    old_argv = sys.argv
    sys.argv = [str(Path(kit)/'b/a.py'), 'r', namespace+'/p', namespace+'/r.json']
    try:
        runpy.run_path(sys.argv[0], run_name='__main__')
    except SystemExit as error:
        if error.code not in (None, 0): raise
    finally:
        sys.argv = old_argv
        px.resolver = original


def run(kit, root, job):
    z = attach(kit); root = Path(root); e = z.load(root/'env.json')
    mode = z.load(root/'mode.json')['mode'] if (root/'mode.json').is_file() else 'b'
    sys.path[:0] = ([str(root/'c')] if mode=='b' else []) + e['paths']
    start = time.monotonic()
    result = dict(status='REFUSE'); failure = None
    try:
        if mode == 'r': run_r(kit, root, job)
        else:
            import rb
            from student_pilot.r1_persisted import scope
            plan = z.load(root/'plan.json')
            with scope(plan['paths']): rb.reconstruct(plan['config'], root, directory='r')
        result['status'] = 'PASS'
    except BaseException as error:
        result['refusal'] = type(error).__name__
        failure = error
    finally:
        result['seconds'] = time.monotonic()-start
        z.write(root/'build.json', result)
    if failure is not None:
        raise failure


def sample(database, request, output, expected=DB):
    """Publish a bounded query only after authenticating the entire input."""
    database, request, output = map(Path, (database, request, output))
    with database.open('rb') as f: actual = hashlib.file_digest(f, 'sha256').hexdigest()
    if actual != expected: raise ValueError('R1_SAMPLE_GATE_FAILED')
    if request.stat().st_size > LIMIT: raise ValueError('R1_SAMPLE_TOO_LARGE')
    value = json.loads(request.read_text())
    ordinals = value.get('i') if isinstance(value, dict) else value
    if not isinstance(ordinals, list) or any(type(i) is not int or i < 0 for i in ordinals):
        raise ValueError('R1_SAMPLE_I_INVALID')
    if len(ordinals) != len(set(ordinals)): raise ValueError('R1_SAMPLE_I_INVALID')
    rows = []; size = 2
    with sqlite3.connect(database.resolve().as_uri()+'?mode=ro', uri=True) as conn:
        # Bound each value before fetching TEXT into Python, including escaped JSON.
        for offset in range(0, len(ordinals), 500):
            group = ordinals[offset:offset+500]
            marks = ','.join('?' for _ in group)
            for i, a, b in conn.execute('SELECT i,length(CAST(row AS BLOB)),length(CAST(target AS BLOB)) FROM rows WHERE i IN ('+marks+')', group):
                if (a or 0)+(b or 0) > LIMIT: raise ValueError('R1_SAMPLE_TOO_LARGE')
            for row in conn.execute('SELECT i,row,target FROM rows WHERE i IN ('+marks+') ORDER BY i', group):
                raw = json.dumps(list(row), ensure_ascii=True, separators=(',', ':')).encode()
                size += len(raw)+(1 if rows else 0)
                if size > LIMIT: raise ValueError('R1_SAMPLE_TOO_LARGE')
                rows.append((row[0], raw))
    rows.sort(key=lambda row: row[0])
    raw = b'['+b','.join(row[1] for row in rows)+b']'
    if len(raw) > LIMIT: raise ValueError('R1_SAMPLE_TOO_LARGE')
    with output.open('xb') as f: f.write(raw)
    return dict(status='PASS', rows=len(rows), bytes=len(raw))


def rdiff(kit, root, target):
    z = attach(kit); root, target = Path(root), Path(target)
    script = z.checked(Path(z.load(Path(kit)/'k/p.json')['n_root'])/'rdiff.py', RD)
    pin = z.load(Path(kit)/'k/l.json')['bwrap']; binary = z.checked(pin['file'], pin['sha256'])
    namespace = z.load(Path(kit)/'k/p.json')['namespace']
    q = root/'dr/p/q'
    cmd = [str(binary), '--ro-bind', '/', '/', '--dev-bind', '/dev', '/dev', '--proc', '/proc',
           '--tmpfs', '/tmp', '--ro-bind', str(root), str(root), '--ro-bind', str(root/'dr'), namespace,
           '--remount-ro', '/tmp', '--bind', str(target), str(target),
           sys.executable, '-I', '-s', '-B', str(script), str(q/'selection/rows.sqlite'), str(q/'base/rows.sqlite'),
           '--tree', str(root/'dr/p/s'), '--removal-manifest', str(q/'n.json'), '--base', str(q), '--out', str(target/'rd0')]
    with (root/'rd.log').open('xb') as log:
        return subprocess.run(cmd, stdout=log, stderr=-2, check=False).returncode


def publish(kit, root, job, rc):
    z = attach(kit); root = Path(root)
    if not job.isascii() or not job.isdecimal(): raise ValueError('R1_JOB_ID_REQUIRED')
    target = Path(z.load(Path(kit)/'k/p.json')['n_root'])/'o'/job
    files, errors = {}, []
    try: target.mkdir(parents=True, exist_ok=True)
    except Exception as error: errors.append(dict(file='o', error=type(error).__name__))
    mode = z.load(root/'mode.json')['mode'] if (root/'mode.json').is_file() else 'b'
    native = root/'dr/p/q' if mode=='r' else root/'r'
    primary = native/'selection' if mode=='r' else native
    entries = [('receipt.json', primary/'receipt.json'), ('materialization.json', primary/'materialization.json'),
               ('import_probe.json', native/'base_imports.json' if mode=='r' else root/'r_imports.json')]
    if mode=='r':
        entries.append(('routing_selection.json', root/'dr/p/routing_selection.json'))
        import ep
        entries += [('k_'+name, p) for name, p in ep.artifact_entries(root)]
    for name, p in entries:
        try:
            if p.is_file():
                if p.is_symlink() or p.stat().st_size > 2_000_000: raise ValueError('R1_ARTIFACT_INVALID')
                shutil.copyfile(p, target/name)
                files[name] = dict(source=str(p.relative_to(root)), sha256=z.sha(p), size=p.stat().st_size)
            else:
                z.write(target/name, dict(status='UNAVAILABLE', returncode=int(rc)))
        except Exception as error:
            errors.append(dict(file=name, error=type(error).__name__))
    rows = []
    bases = [native/'base/rows.sqlite', native/'selection/rows.sqlite'] if mode=='r' else [native/'rows.sqlite']
    gate = False
    for index, p in enumerate(bases):
        try:
            if p.is_file():
                with p.open('rb') as f: header = f.read(16).hex()
                h = z.sha(p)
                row = dict(path=str(p.relative_to(root)), sha256=h, size=p.stat().st_size, header=header)
                if index==0:
                    gate = h==DB
                    row['equal_target'] = gate
                rows.append(row)
            else: rows.append(dict(path=str(p.relative_to(root)), status='UNAVAILABLE'))
        except Exception as error: errors.append(dict(file='db_bytes.json', error=type(error).__name__))
    try: z.write(target/'db_bytes.json', dict(files=rows, expected=DB, equal_target=gate))
    except Exception as error: errors.append(dict(file='db_bytes.json', error=type(error).__name__))
    post_rc = int(int(rc)==0 and (not gate or not all(p.is_file() for p in bases)))
    timing = dict(returncode=int(rc), mode=mode, files=files, publication_errors=errors, rdiff_seconds=None)
    # These publications are independent of the producer and of each other.
    request = target.parents[1]/'rcj/P_SAMPLE_I.json'
    if request.is_file():
        try:
            if gate: timing['sample'] = sample(bases[0], request, target/'p_sample.json')
            else: timing['sample'] = dict(status='SKIPPED', reason='R1_SAMPLE_GATE_FAILED')
        except Exception as error:
            timing['sample'] = dict(status='REFUSE', reason=str(error)); post_rc = 1
    if mode=='r' and gate and all(p.is_file() for p in bases):
        start = time.monotonic()
        try:
            timing['rdiff_returncode'] = rdiff(kit, root, target)
            if timing['rdiff_returncode']: post_rc = 1
        except Exception as error:
            timing['rdiff_refusal'] = type(error).__name__; post_rc = 1
        finally: timing['rdiff_seconds'] = time.monotonic()-start
    elif mode=='r': timing['rdiff_status'] = 'UNAVAILABLE'
    for key, filename in (('staging_seconds','staging.json'), ('mode_r_seconds' if mode=='r' else 'build_seconds','build.json')):
        try:
            p = root/filename
            timing[key] = z.load(p)['seconds'] if p.is_file() else None
        except Exception as error:
            timing[key] = None
            errors.append(dict(file=filename, error=type(error).__name__))
    timing['post_returncode'] = post_rc
    # Retain a local publication report even if the destination is read-only.
    z.write(root/'publication.json', timing)
    try: z.write(target/'timings.json', timing)
    except Exception as error:
        errors.append(dict(file='timings.json', error=type(error).__name__))
        z.write(root/'publication.json', timing)
    if errors:
        raise ValueError('R1_PUBLICATION_INCOMPLETE')
    return post_rc


if __name__ == '__main__':
    mode, kit, root, job, *rest = sys.argv[1:]
    try:
        if mode == 'stage': stage(kit, root, job, rest[0] if rest else 'b')
        elif mode == 'launch': raise SystemExit(launch(kit, root, job))
        elif mode == 'plan': plan_r(kit, root, job)
        elif mode == 'run': run(kit, root, job)
        elif mode == 'publish': raise SystemExit(publish(kit, root, job, rest[0]))
        else: raise ValueError('R1_MODE_INVALID')
    except Exception as error:
        # Names in private native tracebacks pass through the kit's log guard.
        import traceback
        z = attach(kit)
        print(z.screen(traceback.format_exc(), z.load(Path(kit)/'k/g.json'), z.load(Path(kit)/'b/wh.json')), file=sys.stderr)
        raise SystemExit(1)
