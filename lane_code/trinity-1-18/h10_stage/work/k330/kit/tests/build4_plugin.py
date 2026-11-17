"""Keep test scratch files under b4 and retain them without deletion."""
import os
from pathlib import Path
import tempfile

K=Path(__file__).resolve().parents[1]
ROOT=Path(os.environ.get('LANE_TEST_OUTPUT', K/'tmp/b4')).resolve()
if not ROOT.is_relative_to(K/'tmp'):
    raise ValueError('Test output must be under K/tmp')
_mkdtemp=tempfile.mkdtemp

def retained_dir(suffix=None,prefix=None,dir=None):
    if dir is None or not Path(dir).resolve().is_relative_to(ROOT):dir=ROOT
    return _mkdtemp(suffix=suffix,prefix=prefix,dir=dir)

class RetainedTemporaryDirectory:
    def __init__(self,suffix=None,prefix=None,dir=None,**kwargs):
        self.name=retained_dir(suffix,prefix,dir)
    def __enter__(self):return self.name
    def __exit__(self,*args):pass
    def cleanup(self):pass

def pytest_configure(config):
    tempfile.mkdtemp=retained_dir
    tempfile.TemporaryDirectory=RetainedTemporaryDirectory
    os.environ['H1_TINY_FIXTURE']=str(K/'tmp/b4/artifact')

def pytest_collection_modifyitems(items):
    for item in items:
        module=item.module
        if hasattr(module, 'OUT'):
            module.OUT=ROOT/'reader_proofs'
        if hasattr(module, 'reader') and hasattr(module.reader, 'OUT'):
            module.reader.OUT=ROOT/'h1_reader_proofs'

# Optional lossless retention for disk-constrained CPU suites. A function-scoped
# tmp_path is no longer needed after its finalizer; shared fixtures stay intact.
import gzip
import hashlib
import json
import pytest

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_teardown(item, nextitem):
    root=item.funcargs.get('tmp_path')
    yield
    if os.environ.get('LANE_COMPRESS_TEST_OUTPUT')!='1' or root is None:return
    records=[]
    for path in sorted(Path(root).rglob('*')):
        if path.is_symlink() or not path.is_file() or path.stat().st_size<8192 or path.suffix not in ('.json','.jsonl','.bin','.pt','.log'):continue
        raw=path.read_bytes();data=gzip.compress(raw,compresslevel=6,mtime=0)
        if len(data)>=len(raw):continue
        target=path.with_name(path.name+'.gz')
        if target.exists():raise ValueError('Retention destination exists')
        path.write_bytes(data);path.rename(target)
        assert gzip.decompress(target.read_bytes())==raw
        records.append(dict(path=str(target.relative_to(K)),original_bytes=len(raw),bytes=len(data),
                            original_sha256=hashlib.sha256(raw).hexdigest()))
    if records:
        with (K/'logs/b9/test_compression.jsonl').open('a') as stream:
            for record in records:stream.write(json.dumps(record,sort_keys=True)+'\n')
