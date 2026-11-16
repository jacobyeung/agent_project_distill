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
