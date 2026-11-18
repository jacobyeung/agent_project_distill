"""Authenticated, minimal dependency overlay and exhaustive selection import preflight."""
import ast
from email.parser import BytesParser
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import tarfile

ROOT = 'rwtrain_torch211_cu129'
SITE = ROOT + '/lib/python3.12/site-packages/'
# Lazy imports reached by prepare -> source_tokenizer / normalize_room /
# ground_rows.validate. Other functions in routing/generation are not called.
SEEDS = ['ast', 'student_pilot.s1_pool', 'trace_format.ground_v312', 'trace_format.room_v314',
         'generator.derivgen_v7.derivgen.ground_v313_tokens',
         'generator.derivgen_v7.derivgen.ground_v313_distance',
         'generator.derivgen_v7.derivgen.gaps_v314',
         'generator.derivgen_v7.derivgen.room_rows_v314', 'tokenizers']


def closure(tree):
    """Follow module-level imports, including package initializers, from all call-path seeds."""
    tree = Path(tree)
    def source(name):
        p = tree.joinpath(*name.split('.'))
        for candidate in (p.with_suffix('.py'), p / '__init__.py'):
            if candidate.is_file():
                return candidate
    local, external, pending = set(), set(), list(SEEDS)
    class Imports(ast.NodeVisitor):
        def visit_FunctionDef(self, node): pass
        def visit_AsyncFunctionDef(self, node): pass
        def visit_Import(self, node): pending.extend(a.name for a in node.names)
        def visit_ImportFrom(self, node):
            base = (importlib.util.resolve_name('.' * node.level + (node.module or ''), package)
                    if node.level else node.module)
            if not base: return
            pending.append(base)
            for alias in node.names:
                child = base + '.' + alias.name
                if source(child): pending.append(child)
                # scipy's from-imports are modules; explicit probes expose every
                # missing compiled submodule instead of stopping at the first.
                elif base == 'scipy' or (base.startswith('scipy.') and alias.name[:1].islower()
                                         and alias.name in ('distance', 'ndimage')):
                    pending.append(child)
    while pending:
        name = pending.pop()
        if name in local or name in external: continue
        path = source(name)
        if path is None:
            # Namespace packages in the source tree have no initializer.
            if tree.joinpath(*name.split('.')).is_dir():
                local.add(name)
            else: external.add(name)
            continue
        local.add(name)
        package = name if path.name == '__init__.py' else name.rpartition('.')[0]
        for i in range(1, len(name.split('.'))):
            parent = '.'.join(name.split('.')[:i])
            if source(parent): pending.append(parent)
        Imports().visit(ast.parse(path.read_text()))
    return dict(local=sorted(local), external=sorted(external))


def probe(names):
    failures, versions = [], {}
    for name in sorted(set(names)):
        try:
            module = importlib.import_module(name)
            if name in ('torch', 'numpy', 'tokenizers', 'scipy'):
                versions[name] = str(getattr(module, '__version__', 'unknown'))
        except Exception as exc:
            failures.append(dict(module=name, missing=getattr(exc, 'name', None),
                                 error=type(exc).__name__ + ': ' + str(exc)))
    return failures, versions


def checked_name(member):
    name = member.name
    # tar commonly prefixes members with './' and terminates directories with '/'.
    while name.startswith('./'): name = name[2:]
    if member.isdir(): name = name.rstrip('/')
    if name in ('', '.') and member.isdir(): return ''
    p = PurePosixPath(name)
    if (p.is_absolute() or '..' in p.parts or str(p) != name or '\\' in name
            or any(ord(c) < 32 for c in name) or not (name == ROOT or name.startswith(ROOT + '/'))):
        raise ValueError('Unsafe venv member name')
    return name


class Archive:
    """Hash the whole pinned tar, then seek only to selected members on that descriptor."""
    def __init__(self, pin):
        fd = os.open(pin['file'], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        self.source = os.fdopen(fd, 'rb')
        self.before = os.fstat(fd)
        if not stat.S_ISREG(self.before.st_mode):
            self.source.close(); raise ValueError('Venv is not a regular file')
        h, size = hashlib.sha256(), 0
        for block in iter(lambda: self.source.read(1 << 20), b''):
            h.update(block); size += len(block)
        if size != pin['bytes'] or h.hexdigest() != pin['sha256']:
            self.source.close(); raise ValueError('Venv bytes or SHA256 differ')
        self.source.seek(0)
        self.tar = tarfile.open(fileobj=self.source, mode='r:')
        self.members = {}
        try:
            for member in self.tar:
                name = checked_name(member)
                if name in self.members: raise ValueError('Duplicate venv member')
                self.members[name] = member
            self.metadata = {}
            for name, member in self.members.items():
                rel = name[len(SITE):] if name.startswith(SITE) else ''
                if re.fullmatch(r'[^/]+\.dist-info/METADATA', rel):
                    data = BytesParser().parsebytes(self.read(member, 1 << 20))
                    key = re.sub('[-_.]+', '_', data['Name'] or '').lower()
                    if key in self.metadata: raise ValueError('Duplicate distribution metadata')
                    self.metadata[key] = dict(version=data['Version'], directory=rel.split('/')[0])
        except Exception:
            self.close(); raise

    def read(self, member, limit):
        if not member.isfile() or member.issparse() or member.size > limit:
            raise ValueError('Venv member is not a bounded regular file')
        return self.tar.extractfile(member).read()

    def extract(self, module, destination):
        if not re.fullmatch('[A-Za-z_][A-Za-z_0-9]*', module):
            raise ValueError('Unsafe dependency name')
        distribution = self.metadata.get(module.lower())
        if distribution is None:
            # Import names can differ from distribution names (e.g. PIL).
            matches = []
            for record in self.metadata.values():
                top = self.members.get(SITE + record['directory'] + '/top_level.txt')
                if top and module in self.read(top, 65536).decode().split(): matches.append(record)
            if len(matches) != 1: raise ValueError('No unambiguous distribution for ' + module)
            distribution = matches[0]
        dist = distribution['directory']
        selected = []
        for name, member in self.members.items():
            if not name.startswith(SITE): continue
            rel = name[len(SITE):]
            extension = '/' not in rel and rel.startswith(module + '.') and rel.endswith('.so')
            if not (rel == module or rel.startswith(module + '/') or rel == module + '.py' or extension
                    or rel == dist or rel.startswith(dist + '/')): continue
            if member.isdir(): continue
            if not member.isfile() or member.issparse(): raise ValueError('Nonregular dependency member')
            # Bytecode is interpreter-specific and never needed for this overlay.
            if '__pycache__' in PurePosixPath(rel).parts or rel.endswith('.pyc'): continue
            if ('.so' in Path(rel).name and not rel.endswith('.abi3.so')) or rel.endswith(('.dll', '.dylib', '.pyd')):
                raise ValueError('Dependency requires a non-abi3 native extension: ' + module)
            selected.append((rel, member))
        if not any(rel in (module + '.py', module + '.abi3.so') or rel.startswith(module + '/')
                   for rel, _ in selected):
            raise ValueError('Dependency package absent: ' + module)
        wheel = self.members.get(SITE + dist + '/WHEEL')
        if wheel:
            tags = BytesParser().parsebytes(self.read(wheel, 65536)).get_all('Tag', [])
            if not tags or not all('-none-any' in t or '-abi3-' in t for t in tags):
                raise ValueError('Dependency wheel is neither pure Python nor abi3: ' + module)
        # Validate every selected member before publishing any of this package.
        for rel, member in selected:
            if member.size > 64 << 20: raise ValueError('Oversized dependency member')
            with self.tar.extractfile(member) as stream:
                magic = stream.read(4)
            if magic == b'\x7fELF' and not rel.endswith('.abi3.so'):
                raise ValueError('Unlabelled native dependency')
        for rel, member in selected:
            target = destination / rel
            target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            with target.open('xb') as output, self.tar.extractfile(member) as stream:
                for block in iter(lambda: stream.read(1 << 20), b''): output.write(block)
            target.chmod(0o400)
        self.unchanged()
        return dict(module=module, version=distribution['version'], files=len(selected))

    def unchanged(self):
        after = os.fstat(self.source.fileno())
        if any(getattr(after, k) != getattr(self.before, k) for k in
               ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_ctime_ns')):
            raise ValueError('Venv changed during extraction')

    def close(self):
        if hasattr(self, 'tar'): self.tar.close()
        self.source.close()


def prepare(tree, destination, authority, report):
    destination.mkdir(mode=0o700)
    imports = authority['imports']
    if closure(tree) != imports: raise ValueError('Selection import closure differs')
    report.update(imports=imports, imported_versions={}, missing_modules=[], import_errors=[], recovered=[],
                  recovery_errors={}, production_versions={})
    archive = Archive(authority['venv'])
    try:
        report['production_versions'] = {n: archive.metadata.get(n, {}).get('version')
                                         for n in ('torch', 'numpy', 'tokenizers', 'scipy')}
        # Never import the host's tokenizers: production bytes must take precedence.
        report['recovered'].append(archive.extract('tokenizers', destination))
        sys.path.insert(0, str(destination))  # Explicit: -I ignores PYTHONPATH.
        attempted = {'tokenizers'}
        while True:
            importlib.invalidate_caches()
            failures, versions = probe(imports['external'])
            report['imported_versions'].update(versions)
            # Probe each module independently so one failure never hides another.
            native_errors, _ = probe(imports['local'])
            failures += native_errors
            missing = {f['missing'].split('.')[0] for f in failures if f['missing']}
            pending = missing - attempted - set(sys.stdlib_module_names)
            if not pending: break
            for name in sorted(pending):
                attempted.add(name)
                try: report['recovered'].append(archive.extract(name, destination))
                except ValueError as exc: report['recovery_errors'][name] = str(exc)
        report['missing_modules'] = sorted({f['missing'] for f in failures if f['missing']})
        report['import_errors'] = failures
        if 'tokenizers' in report['imported_versions']:
            tokenizers = sys.modules['tokenizers']
            if (not Path(tokenizers.__file__).resolve().is_relative_to(destination.resolve())
                    or report['imported_versions']['tokenizers'] != report['production_versions']['tokenizers']):
                raise ValueError('Imported tokenizers differs from production overlay')
        report['version_differences'] = {n: dict(imported=report['imported_versions'].get(n), production=v)
            for n, v in report['production_versions'].items() if v != report['imported_versions'].get(n)}
        report['selection_content_risk'] = (
            'Tokenizers controls token IDs and room normalization and must match production. '
            'Numpy supplies finite-value checks; torch and scipy are import dependencies, '
            'without tensor or geometry kernels on the selection path. Compatible version differences '
            'are not expected to change selection content, but selection_check must establish equality '
            'over every content field.')
        archive.unchanged()
        if failures: raise ValueError('Selection import preflight failed; see missing_modules and import_errors')
    finally:
        archive.close()
