"""Extract the complete pinned local Python through the production loader."""
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result
C = module('a_storage', ROOT/'src/storage.py')
B = module('builder', ROOT/'build.py')
ctl = module('control', ROOT/'src/control.py')
root = ROOT/'out'/('i'+uuid.uuid4().hex)
root.mkdir()
package = root/'p'
package.mkdir()
with tarfile.open(ROOT/'out/delivery.tgz') as archive:
    for item in archive:
        (package/item.name).write_bytes(archive.extractfile(item).read())
cfg = C.loads((package/'2.json').read_bytes())
sources = C.loads((package/'8.bin').read_bytes())
S, J = ctl.materialize(package, root)
native = Path(sys.base_prefix)
relative = Path('sj/uv-python')/native.name
staged = root/relative
inventory = {}
archive_path = root/'0.tar'
with tarfile.open(archive_path, 'w') as archive:
    # Preserve every pinned interpreter member, including dynamic libraries.
    for path in sorted(native.rglob('*')):
        rel = path.relative_to(native)
        if path.is_file():
            inventory[str(rel)] = hashlib.sha256(path.read_bytes()).hexdigest()
        archive.add(path, arcname=str(relative/rel), recursive=False)
S.unpack(archive_path, root, links=True)
for name, digest in inventory.items():
    assert hashlib.sha256((staged/name).read_bytes()).hexdigest() == digest, name

# The old translator renamed every one of these files during extraction.
damaged = sorted(name for name in inventory if C.mapped(str(relative/name)) != str(relative/name))
assert 'lib/python3.12/keyword.py' in damaged
assert all(str(S.Path(staged/name)) == str(staged/name) for name in inventory)
site = Path(sys.prefix)/'lib/python3.12/site-packages'
package_paths = [p.relative_to(site) for p in site.rglob('*')]
# Check the complete local package inventory through the same archive Path
# constructor, without duplicating GB of immutable native library binaries.
site_target = root/'sj/a/d/v/site'
assert all(str(S.Path(site_target/rel)) == str(site_target/rel) for rel in package_paths)

# Reproduce the observed rename using the old implementation of translate.
old_source = (ROOT/'src/storage.py').read_text()
start = old_source.index('        try: rel = p.relative_to(root)')
end = old_source.index('\n    def writable_json', start)
old_source = old_source[:start]+'''        try: return root/mapped(str(p.relative_to(root)))
        except ValueError: return p
''' + old_source[end:]
old = root/'1.py'
old.write_text(old_source)
legacy = module('legacy_storage', old)
old_root = root/'z'
old_root.mkdir()
old_finder = legacy.materialize(old_root, {k:v for k,v in sources.items() if k.startswith('v/')})
sys.modules.pop('orchard_stage', None)
import orchard_stage as old_stage
raw = B.archive({'sj/lib/keyword.py': (native/'lib/python3.12/keyword.py').read_bytes()})
old_stage.extract_stream(io.BytesIO(raw), old_root, None, 100000)
assert not (old_root/'sj/lib/keyword.py').exists()
renamed = old_root/C.mapped('sj/lib/keyword.py')
assert renamed.is_file()
negative = subprocess.run([sys.executable, '-I', '-S', '-B', '-c',
    'import sys; sys.path[:]=[sys.argv[1]]; import keyword', str(old_root/'sj/lib')],
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
assert negative.returncode and b"No module named 'keyword'" in negative.stderr
sys.meta_path.remove(old_finder)

C.materialize(package, sources)
(package/'a').mkdir()
cfg['logical'] = str(package)
cfg['inputs']['env_roots'] = [str(site)]
C.store(package/'2.json', cfg)
audit = root/'2.py'
audit.write_bytes((ROOT/'tests/import_worker.py').read_bytes())
output = root/'2.json'
stdlib = staged/'lib/python3.12'
# Exercise runpy with the staged local interpreter; test_pinned.py separately
# uses the exact Orchard archives and entry wrapper.
boot = root/'3.py'
boot.write_text("import sys, runpy\nargs=sys.argv[1:]\nsys.argv=args\nrunpy.run_path(args[0], run_name='__main__')\n")
native_site = module('native_fixture', ROOT/'tests/native_fixture.py').prepare(ROOT)
command = [str(staged/'bin/python3.12'), '-I', '-S', '-B', '-X', 'importtime',
           str(boot), str(audit), str(stdlib), str(site), str(package), str(output), str(native_site)]
env = C.job_environment(root, dict(PATH='/usr/bin:/bin', USER='a', CUDA_VISIBLE_DEVICES=''))
env.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='2')
# Use the production namespace construction when user namespaces are available.
for directory in ('sj', 'fsw', 'm/ap'): (root/directory).mkdir(parents=True, exist_ok=True)
namespace = J.namespace(root)
namespace[0] = '/usr/bin/bwrap'
for i in range(len(namespace)-2):
    if namespace[i:i+3] == ['--bind', '/tmp', '/tmp']:
        namespace[i:i+3] = ['--dir', '/tmp', '--bind', str(root), str(root)]
        break
namespace += ['--bind', str(root), str(root), '--ro-bind', str(site), str(site),
              '--ro-bind', str(native_site), str(native_site)]
probe = subprocess.run(namespace+['/usr/bin/true'], env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=20)
mode = 'production namespace' if probe.returncode == 0 else 'relocated isolated interpreter; namespace unavailable'
if probe.returncode:
    assert any(x in probe.stderr.lower() for x in (b'operation not permitted', b'permission denied', b'creating new namespace')), probe.stderr
result = subprocess.run((namespace if probe.returncode == 0 else [])+command,
    cwd=root, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=120)
(root/'2.log').write_bytes(result.stderr)
assert result.returncode == 0, result.stderr.decode()[-8000:]
evidence = json.loads(output.read_text())
evidence.update(tests=1, delivery=B.pin((ROOT/'out/delivery.tgz').read_bytes()),
    native_fixture='Local torchvision 0.25.0+cu128 Python modules; unused NMS schema double for CPU torch. No native CUDA operators executed.',
    mode=mode, namespace_probe=probe.stderr.decode(), runtime_files=len(inventory),
    runtime_inventory_sha256=B.digest(B.jd(inventory)), affected_runtime_files=damaged,
    package_paths_checked=len(package_paths), old_keyword_reproduced=True,
    importtime=str((root/'2.log').relative_to(ROOT)),
    limits='Local pinned CPython 3.12.13 and p1cpu packages; the exact Orchard environment is tested separately by tests/test_pinned.py. Native package bytes are read from the local site tree; all package paths pass the extractor path-identity audit. No checkpoint or GPU loaded.')
(ROOT/'out/IMPORT_CHECKS.json').write_text(json.dumps(evidence, indent=2)+'\n')
print(json.dumps({k:v for k,v in evidence.items() if k not in ('imports','modules','affected_runtime_files')}, indent=2))
