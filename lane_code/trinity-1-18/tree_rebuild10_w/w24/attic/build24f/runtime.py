"""Prevent runtime writes to sealed kits; leave all authenticated inputs intact."""
from pathlib import Path
import base64,hashlib,json,re

def shell(source):
    # -I ignores PYTHON* environment variables, so every invocation needs -B.
    source=re.sub(r'(/usr/bin/python3|(?<![\w/])python3)(?![\w.])(?=\s)(?! -B)',r'\1 -B',source)
    source=source.replace('"$PILOT_VENV/bin/python" -s -B','"$PILOT_VENV/bin/python" -B -s')
    # Scheduler directives must precede the first executable shell statement.
    source=source.replace('export PYTHONDONTWRITEBYTECODE=1\n','')
    lines=source.splitlines(True);i=0
    while i<len(lines) and (lines[i].startswith('#') or not lines[i].strip()):i+=1
    lines.insert(i,'export PYTHONDONTWRITEBYTECODE=1\n');source=''.join(lines)
    return source

def local_env(root):
    return ('export TMPDIR="'+root+'/tmp" XDG_CACHE_HOME="'+root+'/cache"\n'
            'export HF_HOME="'+root+'/cache/hf" TORCH_HOME="'+root+'/cache/torch" TRITON_CACHE_DIR="'+root+'/cache/triton"\n'
            'export CUDA_CACHE_PATH="'+root+'/cache/cu" MPLCONFIGDIR="'+root+'/cache/plot"\n'
            'mkdir -p "$TMPDIR" "$XDG_CACHE_HOME"\ncd "'+root+'"\n')

def harden_kit(k):
    k=Path(k)
    for p in sorted(k.rglob('*.sh')):
        s=shell(p.read_text())
        if p.name=='job.sh' and 'cd "$N"' not in s:
            marker='export OMP_NUM_THREADS='
            i=s.index(marker)
            s=s[:i]+local_env('$N')+s[i:]
        if p.name=='job.sh' and '#SBATCH --output=' not in s:
            s=s.replace('#SBATCH --no-requeue\n','#SBATCH --no-requeue\n#SBATCH --output=/tmp/q_%j.log\n#SBATCH --error=/tmp/q_%j.err\n')
        if p.name=='f.sh':
            s='''#!/bin/bash
set -eu
umask 077
export CUDA_VISIBLE_DEVICES="" PYTHONDONTWRITEBYTECODE=1
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
N="${1:?}.h"
'''+local_env('$N')+'''exec python3 -B -I -s "$ROOT/b/a.py" p "$1"
'''
        p.write_text(s)
    p=k/'k/j.json'
    if p.exists():
        doc=json.loads(p.read_text());s=shell(base64.b64decode(doc['payload']).decode())
        if 'cd "$Q_ROOT"' not in s:
            marker='export PATH='
            i=s.index(marker);s=s[:i]+local_env('$Q_ROOT')+s[i:]
        raw=s.encode();doc.update(payload=base64.b64encode(raw).decode(),sha256=hashlib.sha256(raw).hexdigest())
        p.write_text(json.dumps(doc))
    p=k/'b/z.py'
    if p.exists():
        s=p.read_text()
        if "'PYTHONDONTWRITEBYTECODE':'1'" not in s:
            s=s.replace("'Q_ROOT':env_node", "'PYTHONDONTWRITEBYTECODE':'1','Q_ROOT':env_node")
        p.write_text(s)
    # Keep the result archive in node-local storage, then publish that closed
    # artifact to the existing output path. No intermediate writes enter a kit.
    p=k/'b/o.py'
    if p.exists() and "local=r/'o'" not in p.read_text():
        s=p.read_text().replace('import json,sys,tarfile,os','import json,sys,tarfile,os,shutil')
        s=s.replace("with tarfile.open(out/'o.tar','w:gz') as t:","local=r/'o';local.mkdir(parents=True,exist_ok=True)\nwith tarfile.open(local/'o.tar','w:gz') as t:")
        s=s.replace("write(out/'RESULT.json',", "shutil.copyfile(local/'o.tar',out/'o.tar')\nwrite(local/'RESULT.json',")
        if "shutil.copyfile(local/'RESULT.json'" not in s:
            s+="shutil.copyfile(local/'RESULT.json',out/'RESULT.json')\n"
        p.write_text(s)
    p=k/'b/t.py'
    if p.exists():
        s=p.read_text().replace('import sys,subprocess\n','import sys,subprocess,os\n')
        s=s.replace("str(k/'b/u.py'),*sys.argv[1:]],check=False)","'--no-python','/bin/bash',str(k/'b/e.sh'),sys.executable,*sys.argv[1:]],check=False,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})")
        p.write_text(s)
        (k/'b/e.sh').write_text('''#!/bin/bash
set -eu
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(dirname "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")")"
PY="$1"
shift
exec "$PY" -B -s "$ROOT/b/u.py" "$@"
''')

    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"work/build24d"))
    from kit24d import upgrade
    upgrade(k)

    sys.path.insert(0,str(Path(__file__).resolve().parents[2]/"work/build24e"))
    from patch24e import upgrade as upgrade24e
    upgrade24e(k)
