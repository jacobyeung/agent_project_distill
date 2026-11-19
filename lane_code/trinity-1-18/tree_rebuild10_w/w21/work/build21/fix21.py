from pathlib import Path
import re,json
L=Path(__file__).resolve().parents[2];B=L/'work/build21';T=L/'work/tree_r1'
names={'STUDENT_ORCHARD':'Q_E1','STUDENT_SLURM_SITE':'Q_E2','STUDENT_MODEL_ROOT':'Q_E3','STUDENT_FRAME_ROOT_MAP':'Q_E4','R1_STUDENT_HEX':'Q_E5'}
changed=[]
for p in (T/'student_pilot').glob('*.py'):
    text=p.read_text();old=text
    for name,alias in names.items():
        for q in ("'",'"'):
            text=text.replace('os.environ.get('+q+name+q, 'os.environ.get(('+q+alias+q+' if '+q+alias+q+' in os.environ else '+q+name+q+')')
            text=text.replace('os.environ['+q+name+q+']','os.environ['+q+alias+q+' if '+q+alias+q+' in os.environ else '+q+name+q+']')
    if text!=old:
        (B/'base'/p.name).write_text(old);p.write_text(text);changed.append(str(p.relative_to(T)))
(B/'ENV_CHANGES.json').write_text(json.dumps(changed,indent=2))
p=B/'kit.py';s=p.read_text()
s=s.replace("pfiles['SHA256SUMS.txt']=", "pfiles['ANON_OK.json']=sha256(E/'ANON_OK.json')\npfiles['SHA256SUMS.txt']=")
s=s.replace("cap('k/p.json',spec);", "from naming21 import neutral_map\nneutral,links=neutral_map(load(E/'k/0.json'))\ncap('k/l.json',neutral)\nspec.update(local_map='k/l.json',link_checks=links)\ncap('k/p.json',spec);")
s=s.replace("shell=shell[:shell.index('tk_persist_small()')]", "shell=shell[:shell.index('tk_persist_small()')]\nfrom naming21 import neutral_shell\nshell=neutral_shell(shell)")
s=s.replace("(K/'b/w.py').write_text", "(K/'b/m.py').write_text('import sys\\nfrom z import snapshot\\nsnapshot(*sys.argv[1:])\\n')\n(K/'b/w.py').write_text")
p.write_text(s)
