"""Keep test scratch files under b4 and retain them without deletion."""
import os
from pathlib import Path
import tempfile

ROOT=Path(__file__).resolve().parents[1]/'tmp/b4'
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
    os.environ['H1_TINY_FIXTURE']=str(ROOT/'artifact')
