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
        self.h = self.root/'h'; self.h.mkdir()
        for name in ('b/s.py', 'b/kitx.py'):
            self.host_file(name)
        spec = importlib.util.spec_from_file_location('q_stage', self.h/'b/s.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        self.stage = module.Stage(self.h, self.root/'s')
        import px
        self.px = px
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
            return self.px.resolver(self.kit, self.root, self.sources)(h, field)
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


def stage(kit, root):
    z = attach(kit); start = time.monotonic()
    try:
        root = Path(root)
        source = z.load(Path(kit)/'k/a.json')['source']
        code = root/'c'
        with tarfile.open(z.checked(Path(kit)/source['path'], source['sha256'])) as t:
            t.extractall(code, filter='data')
        sys.path.insert(0, str(code))
        inputs = Inputs(kit, root)
        try:
            inputs.closure()
            inputs.environment()
        finally:
            for a in inputs.archives.values(): a.close()
    finally:
        z.write(Path(root)/'staging.json', dict(seconds=time.monotonic()-start))


def launch(kit, root, job):
    z = attach(kit); root = Path(root)
    e = z.load(root/'env.json')
    logical = '/project/community/jjyeung/c7d31ddd/venvs'
    executable = logical+'/rwtrain_torch211_cu129/bin/python'
    pin = z.load(Path(kit)/'k/l.json')['bwrap']
    binary = z.checked(pin['file'], pin['sha256'])
    cmd = [str(binary), '--ro-bind', '/', '/', '--bind', str(root), str(root),
           '--ro-bind', e['venv'], logical, '--chdir', str(root),
           executable, '-I', '-s', '-B', str(Path(__file__).resolve()), 'run', str(kit), str(root), job]
    return subprocess.run(cmd, check=False, env={**os.environ, "PATH":str(binary.parent)+os.pathsep+os.environ.get("PATH", "")}).returncode


def run(kit, root, job):
    z = attach(kit); root = Path(root); e = z.load(root/'env.json')
    sys.path[:0] = [str(root/'c'), *e['paths']]
    import rb
    from student_pilot.r1_persisted import scope
    plan = z.load(root/'plan.json'); start = time.monotonic()
    result = dict(status='REFUSE'); failure = None
    try:
        with scope(plan['paths']): rb.reconstruct(plan['config'], root, directory='r')
        result['status'] = 'PASS'
    except BaseException as error:
        result['refusal'] = type(error).__name__
        failure = error
    finally:
        result['seconds'] = time.monotonic()-start
        z.write(root/'build.json', result)
        publish(kit, root, job, 1 if failure else 0)
    if failure is not None:
        raise failure


def publish(kit, root, job, rc):
    z = attach(kit); root = Path(root)
    if not job.isdecimal(): raise ValueError('R1_JOB_ID_REQUIRED')
    target = Path(z.load(Path(kit)/'k/p.json')['n_root'])/'o'/job
    target.mkdir(parents=True, exist_ok=True)
    files, errors = {}, []
    for name, p in (('receipt.json', root/'r/receipt.json'), ('materialization.json', root/'r/materialization.json'),
                    ('import_probe.json', root/'r_imports.json')):
        try:
            if p.is_file():
                shutil.copyfile(p, target/name)
                files[name] = dict(sha256=z.sha(p), size=p.stat().st_size)
            else:
                z.write(target/name, dict(status='UNAVAILABLE', returncode=int(rc)))
        except Exception as error:
            errors.append(dict(file=name, error=type(error).__name__))
    rows = []
    p = root/'r/rows.sqlite'
    try:
        if p.is_file():
            with p.open('rb') as f: header = f.read(16).hex()
            rows.append(dict(path='r/rows.sqlite', sha256=z.sha(p), size=p.stat().st_size, header=header))
        z.write(target/'db_bytes.json', dict(files=rows, expected='4e8e6c04e697d8f12ecd9d705e197e94f73f4a9dc508b7a9e9b4f36487336f84'))
    except Exception as error:
        errors.append(dict(file='db_bytes.json', error=type(error).__name__))
    timing = dict(returncode=int(rc), files=files, publication_errors=errors)
    for key, filename in (('staging_seconds','staging.json'), ('build_seconds','build.json')):
        try:
            p = root/filename
            timing[key] = z.load(p)['seconds'] if p.is_file() else None
        except Exception as error:
            timing[key] = None
            errors.append(dict(file=filename, error=type(error).__name__))
    z.write(target/'timings.json', timing)
    if errors:
        raise ValueError('R1_PUBLICATION_INCOMPLETE')
    return 0


if __name__ == '__main__':
    mode, kit, root, job, *rest = sys.argv[1:]
    try:
        if mode == 'stage': stage(kit, root)
        elif mode == 'launch': raise SystemExit(launch(kit, root, job))
        elif mode == 'run': run(kit, root, job)
        elif mode == 'publish': publish(kit, root, job, rest[0])
        else: raise ValueError('R1_MODE_INVALID')
    except Exception as error:
        # Names in private native tracebacks pass through the kit's log guard.
        import traceback
        z = attach(kit)
        print(z.screen(traceback.format_exc(), z.load(Path(kit)/'k/g.json'), z.load(Path(kit)/'b/wh.json')), file=sys.stderr)
        publish(kit, root, job, 1)
        raise SystemExit(1)
