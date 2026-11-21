# Kit-only change for mode q (b/pl.py, b/a.py, new b/mg.py and b/pf.py):
#  1. the model manifest's non-weight files also get one folder, q/y, under their manifest names, and their pins
#     resolve there after staging, so the opener witness finds a processor folder;
#  2. b/pf.py opens the witness's and the forward's processor folders at the end of planning and after staging;
#  3. b/mg.py answers device queries without the driver while admit() holds the empty mask.
import sys,hashlib,os
from pathlib import Path
K=Path(sys.argv[1]);src=Path(sys.argv[2])
def swap(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)
p=K/'b/pl.py';s=p.read_text()
s=swap(s,"from z import load, checked, sha, write, seal, name_guard, selected400\n",
"from z import load, checked, sha, write, seal, name_guard, selected400, inside\n")
s=swap(s,'''def plan_payload(kit, resolved, root, *, regeneration=False):
''','''def named_folder(folder, pool, named, link=True):
    """Place each named file's pool bytes under its own name in one folder; return {sha256: path}."""
    folder = Path(folder); folder.mkdir(mode=0o700, exist_ok=True)
    placed = {}
    for name, h in named.items():
        source = checked(pool(h), h); target = inside(folder, name)
        if target.exists():checked(target, h)
        elif link:os.link(source, target)
        else:
            shutil.copyfile(source, target); checked(target, h)
        placed[h] = str(target)
    return placed


def plan_payload(kit, resolved, root, *, regeneration=False):
''')
s=swap(s,'''    need=resolver(kit,root,sources)
''','''    need=resolver(kit,root,sources)
    # The opener witness takes the processor folder from where the model manifest's config.json pin
    # resolves. In mode q that manifest's non-weight files therefore also get one folder, q/y, under
    # their manifest names (hard links to q/u), and their pins resolve there once staging is done.
    named={}
    if not regeneration:
        for name,h in resolved['model_files'].items():
            if name.endswith(('.json','.txt','.jinja','.model')):
                name_guard(kit)(name)
                if Path(name).name!=name or name in ('.','..'):raise ValueError('E43')
                if h not in sources:need(h,'model_manifest.files.'+name)
                named[name]=h
        if 'config.json' not in named:raise ValueError('E31')
''')
s=swap(s,'''        shutil.copyfile(manifest_path,q/'u'/manifest_pin['sha256'])
        for p in [q,*[p for p in q.rglob('*') if p.is_dir()]]:p.chmod(0o700)
''','''        shutil.copyfile(manifest_path,q/'u'/manifest_pin['sha256'])
        linked=named_folder(q/'y',lambda h:q/'u'/h,named) if named else {}
        for p in [q,*[p for p in q.rglob('*') if p.is_dir()]]:p.chmod(0o700)
''')
s=swap(s,'''        final_paths.update(paths)
        final_paths[cfgh]=str(q/'n.json')
''','''        final_paths.update(paths)
        final_paths.update(linked)
        final_paths[cfgh]=str(q/'n.json')
''')
s=swap(s,'''        stage.context=scope(final_paths)
        stage.context.__enter__()
''','''        stage.context=scope(final_paths)
        stage.context.__enter__()
        if named:
            from pf import check
            check(cfg,resolved['model_manifest'])
''')
s=swap(s,'''    stage.context=None
    stage.close=close
''','''    stage.context=None
    stage.close=close
    if named:
        # Fail before the long steps: rehearse both processor folders on the planned bytes.
        from pf import check
        with scope({**sources,**named_folder(scratch/'y',lambda h:sources[h],named,link=False)}):
            check(cfg,resolved['model_manifest'])
''')
p.write_text(s)
a=K/'b/a.py';s=a.read_text()
s=swap(s,'''    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:return native_admit(*args,**kwargs)
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
''','''    # A driver query made while admit() hides the devices would leave this process unable to open
    # one later; b/mg.py answers the device queries without the driver for as long as the mask is empty.
    from mg import guard
    def restoring_admit(*args,**kwargs):
     limit=resource.getrlimit(resource.RLIMIT_AS)
     try:
      with guard():return native_admit(*args,**kwargs)
     finally:resource.setrlimit(resource.RLIMIT_AS,limit)
''')
a.write_text(s)
mode=os.stat(K/'b/z.py').st_mode&0o7777
for name in ('mg.py','pf.py'):
    f=K/'b'/name;assert not f.exists()
    f.write_bytes((src/name).read_bytes());os.chmod(f,mode)
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
L=(K/'SHA256SUMS.txt').read_text().splitlines()
name=lambda l:l.split('  ',1)[1]
assert [name(l) for l in L]==sorted(name(l) for l in L)
new={'b/a.py':a,'b/pl.py':p}
L=[(sha(new[name(l)])+'  '+name(l)) if name(l) in new else l for l in L]+[sha(K/'b'/n)+'  b/'+n for n in ('mg.py','pf.py')]
L.sort(key=name)
(K/'SHA256SUMS.txt').write_text('\n'.join(L)+'\n')
print({n:sha(K/n)[:16] for n in ('b/a.py','b/pl.py','b/mg.py','b/pf.py')},'seal',sha(K/'SHA256SUMS.txt'))
