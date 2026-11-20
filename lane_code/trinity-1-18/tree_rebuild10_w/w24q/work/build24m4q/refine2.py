import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent));from common import *
p=D/'run_one.py';s=p.read_text().replace("(D/'tmp').mkdir(exist_ok=True)","(D/'tmp').mkdir(exist_ok=True)\nimport tempfile\ntempfile.tempdir=str(D/'tmp')");replace(p,s)
p=L/'out/rcj/ch.py';s=p.read_text().replace('def call(*args, **kwargs):','def call(*args):').replace('function(*args, **kwargs)','function(*args)');replace(p,s)
