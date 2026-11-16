"""Write a deterministic source archive; exclude results, inputs and bytecode."""
import gzip
import hashlib
import io
import tarfile
from .paths import ROOT, OUT
from .io import write_json

def package_source():
    files = sorted([p for directory, pattern in [('navrun','*.py'),('navrun/vendor','*.py'),
                    ('navrun/vendor','*.json'),('tests','*.py'),('tests/fixtures','*.json'),('configs','*.json')]
                    for p in (ROOT/directory).glob(pattern)] + [ROOT/'README.md',ROOT/'run.sh',ROOT/'pyproject.toml'])
    target=OUT/'navrun_src.tgz'
    with target.open('wb') as raw, gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode='w') as tar:
            for path in files:
                content=path.read_bytes()
                info=tarfile.TarInfo(str(path.relative_to(ROOT)))
                info.size=len(content);info.mode=0o755 if path.name=='run.sh' else 0o644
                info.mtime=0;info.uid=info.gid=0
                tar.addfile(info,io.BytesIO(content))
    sha=hashlib.sha256(target.read_bytes()).hexdigest()
    with tarfile.open(target,'r:gz') as tar:
        names=tar.getnames()
        assert all(not n.startswith('out/') and '__pycache__' not in n for n in names)
        assert 'navrun/runner.py' in names and 'tests/test_runner.py' in names and 'configs/NU.json' in names
    write_json(OUT/'tables/source_archive.json',dict(path=str(target),sha256=sha,bytes=target.stat().st_size,members=names))
    return sha
if __name__=='__main__':print(package_source())
