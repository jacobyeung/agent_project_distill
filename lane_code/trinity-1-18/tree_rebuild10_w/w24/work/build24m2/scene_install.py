import sys;from pathlib import Path;sys.path.insert(0,str(Path(__file__).resolve().parent))
from buildlib import *
s=(D/'sc.py').read_text().replace("    binary = __import__('z').load(kit/'k/h.json')['binaries']['bwrap']\n    if isinstance(binary, dict):\n        binary = checked(binary['path'], binary['sha256'])", "    import shutil\n    binary = shutil.which('bwrap')\n    if not binary:raise ValueError('R1_BINARY_MISSING:bwrap')")
s=s.replace("str(physical), str(destination/'sc')", "str(physical), str(destination)")
s=s.replace("    result = load(physical/'2.json')", "    physical = physical/'sc'\n    result = load(physical/'2.json')")
(D/'sc.py').write_text(s)
for name in ('q','n','n_go'):
 k=kit(name)
 for f in ('sc.py','sv.py'):replace(k/'b'/f,(D/f).read_bytes())
 if name=='q':
  for f in ('h.py','rv.py'):replace(k/'b'/f,(kit('n')/'b'/f).read_bytes())
  c=J.load(k/'k/a.json');c['review_wait_seconds']=7200;cap(k,'k/a.json',c)
 p=k/'b/pl.py';s=p.read_text()
 needle="    cfgraw=raw_json(cfg); cfgpath=metadata/'n.json'"
 assert needle in s
 s=s.replace(needle,"    scene=None\n    if not regeneration:\n        from sc import bind\n        scene=bind(cfg,sources,scratch,q,kit)\n        for p in scene.rglob('*'):\n            if p.is_file():remember(p)\n"+needle)
 needle="    copy_entry('source_code.json',codepath,spec['code_sha256']);copy_entry('n.json',cfgpath,cfgh)"
 s=s.replace(needle,needle+"\n    if scene is not None:\n        for p in scene.rglob('*'):\n            if p.is_file():copy_entry('sc/'+str(p.relative_to(scene)),p)")
 replace(p,s)
 p=k/'b/a.py';s=p.read_text().replace("if sys.argv[1]=='r':\n import os", "if sys.argv[1] in ('q','r'):\n import os")
 needle="    r=run(request,root/'q',stage=stage)"
 s=s.replace(needle,needle+"\n    if r['status']=='ADMIT':\n     from sv import publish\n     from student_pilot.p3_provenance import pinned\n     publish(kit,root.parent,load(pinned(r['config'])),os.environ['SLURM_JOB_ID'])")
 replace(p,s)
 s=base64.b64decode(json.loads((k/'k/j.json').read_text())['payload']).decode()
 if name=='q':
  needle='BW+=(--bind "$Q_ROOT" "$Q_NS")'
  s=s.replace(needle,needle+'\nQ_LIVE=$(/usr/bin/python3 -B -I -s "$Q_KIT/b/rv.py" --live "$Q_ROOT" "${SLURM_JOB_ID:?}")\nBW+=(--bind "$Q_LIVE" "$Q_LIVE")')
 cap(k,'k/j.json',s.encode());print(name,reseal(k))
