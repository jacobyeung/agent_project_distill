from common import *
s=(D/'cs.py').read_text()
s=s.replace("def verify(kit,root,cfg):","def _verify(kit,root,cfg):")
s += '''
def verify(kit,root,cfg):
    from student_pilot.r1_persisted import scope
    # Receipt bodies retain their authenticated original pins. Resolve those
    # pins only through the native job's content-addressed staged bytes.
    folder=Path(root)/'p/q/u'
    paths={}
    if folder.is_dir():
        for p in folder.iterdir():
            h=p.name
            if len(h)==64 and all(c in '0123456789abcdef' for c in h):
                if p.is_symlink() or not p.is_file():raise ValueError('R1_CENSUS_STAGED_PIN_INVALID')
                paths[h]=str(p)
    with scope(paths):
        return _verify(kit,root,cfg)
'''
replace(D/'cs.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/cs.py',s)
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 print(name,reseal(k))
