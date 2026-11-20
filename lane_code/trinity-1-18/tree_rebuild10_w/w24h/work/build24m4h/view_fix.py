import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
for n in NAMES:
 p=kit(n)/'b/rb.py';s=p.read_text();s=s.replace('''    cmd = [binary, "--ro-bind", "/", "/", "--dev-bind", "/dev", "/dev", "--proc", "/proc"]
    for p in roots: cmd += ["--tmpfs", p]
    for p in (Path(sys.base_prefix), Path(sys.prefix), Path(__file__).resolve().parent, Path(root)):
        if any(str(p).startswith(r+"/") for r in roots): cmd += ["--ro-bind", str(p), str(p)]''','''    cmd = [binary, "--ro-bind", "/usr", "/usr", "--symlink", "usr/bin", "/bin",
           "--symlink", "usr/lib", "/lib", "--symlink", "usr/lib64", "/lib64",
           "--ro-bind", "/etc", "/etc", "--dev-bind", "/dev", "/dev", "--proc", "/proc", "--tmpfs", "/tmp"]
    for p in (Path(sys.base_prefix), Path(sys.prefix), Path(__file__).resolve().parent, Path(root)):
        cmd += ["--ro-bind", str(p), str(p)]''');replace(p,s)
J.write(D/'SEALS.json',{n:reseal(kit(n)) for n in NAMES})
