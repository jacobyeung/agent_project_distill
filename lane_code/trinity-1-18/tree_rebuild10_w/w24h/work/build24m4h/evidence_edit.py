import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from common import *
k=kit('n');s=(k/'b/ep.py').read_text();a=s.index('def publish_artifacts(');b=s.index("\n\nif __name__",a)
s=s[:a]+'''def artifact_entries(root):
    root=Path(root)
    result=[]
    for prefix,label in (('p','a'),('dr/p','b')):
        for part,code in (('selection','0'),('base','1'),('pr','2')):
            for filename,suffix in (('materialization.json','m'),('receipt.json','r')):
                result.append((label+code+suffix+'.json',root/prefix/'q'/part/filename))
        result.append((label+'3r.json',root/prefix/'i/pool/r.json'))
        for part,code in (('base_refresh','4'),('pr_refresh','5')):
            result.append((label+code+'r.json',root/prefix/'q'/part/'r.json'))
    return result


def publish_artifacts(target, root):
    total=0;records={}
    for name,p in artifact_entries(root):
        if not p.exists():continue
        if p.is_symlink() or not stat.S_ISREG(p.stat().st_mode):
            raise ValueError('R1_ROUTING_ARTIFACT_UNUSABLE')
        size=p.stat().st_size
        if size>2_000_000 or total+size>10_000_000:
            raise ValueError('R1_ROUTING_ARTIFACTS_TOO_LARGE')
        raw=p.read_bytes();json.loads(raw);total+=len(raw)
        fd=os.open(target/(name+'.part'),os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
        with os.fdopen(fd,'wb') as f:f.write(raw)
        os.replace(target/(name+'.part'),target/name)
        records[name]=dict(source=str(p.relative_to(root)),sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw))
    raw=(json.dumps(records,sort_keys=True)+'\\n').encode()
    fd=os.open(target/'a6.json.part',os.O_WRONLY|os.O_CREAT|os.O_TRUNC|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'wb') as f:f.write(raw)
    os.replace(target/'a6.json.part',target/'a6.json')
    return records
'''+s[b:]
r=(k/'b/rd.py').read_text().replace('    return records','    from ep import publish_artifacts\n    publish_artifacts(target, root)\n    return records')
i=(k/'b/i.py').read_text().replace('def refresh(request,root):','def _refresh(request,root):')
i+='''

def refresh(request,root):
    from z import write
    root=Path(root)
    try:
        result=_refresh(request,root)
    except BaseException as error:
        if not (root/'r.json').exists():
            write(root/'r.json',dict(status='REFUSE',refusal=str(error)))
        raise
    if not (root/'r.json').exists():
        write(root/'r.json',dict(status='PASS',prepared=False,config=result['config']))
    return result
'''
for n in NAMES:
 for name,raw in (('ep.py',s),('rd.py',r),('i.py',i)):replace(kit(n)/'b'/name,raw)
changed=J.load(D/'CHANGED_B.json');J.write(D/'CHANGED_B.json',sorted(set(changed)|{'ep.py','rd.py'}))
# Record the shell parse failure without claiming it was a cluster kill.
J.write(D/'FAILURES.json',[dict(stage='edit script creation',output="bash: syntax error near unexpected token `('; here-document terminated at shell quote",cause='Shell quoting in a generated editor; corrected editor uses a quoted heredoc',cluster_kill=False)])
print('Evidence publication updated')
