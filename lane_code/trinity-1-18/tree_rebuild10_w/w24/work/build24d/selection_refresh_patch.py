from pathlib import Path
import sys
L=Path(__file__).resolve().parents[2];D=L/'work/build24d'
sys.path.insert(0,str(D));from patch import reseal
for k in (L/'work/build24/kits/q',L/'work/build24/kits/n',L/'out/kit_n_go'):
 (k/'b/i.py').write_bytes((D/'i.py').read_bytes())
 p=k/'b/a.py';s=p.read_text()
 marker=" with scope(request.pop('_paths',{})):\n  r=run(request,root/'q')"
 assert marker in s
 s=s.replace(marker," sys.path.insert(0,str(kit/'b'))\n from i import refresh\n with scope(request.pop('_paths',{})):\n  request=refresh(request,root/'i')\n  r=run(request,root/'q')")
 p.write_text(s);reseal(k,k.name=='kit_n_go')
p=D/'kit24d.py';s=p.read_text();marker="    if not (k/'b/t.py').exists():return"
add="""    if (k/'b/a.py').exists():
        (k/'b/i.py').write_bytes((L/'work/build24d/i.py').read_bytes())
        p=k/'b/a.py';s=p.read_text()
        marker=" with scope(request.pop('_paths',{})):\\n  r=run(request,root/'q')"
        if marker in s:s=s.replace(marker," sys.path.insert(0,str(kit/'b'))\\n from i import refresh\\n with scope(request.pop('_paths',{})):\\n  request=refresh(request,root/'i')\\n  r=run(request,root/'q')")
        p.write_text(s)
"""
assert marker in s;s=s.replace(marker,add+marker);p.write_text(s)
