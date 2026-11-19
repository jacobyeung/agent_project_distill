from pathlib import Path
L=Path(__file__).resolve().parents[2];D=L/"work/build24e"
s=(L/"work/build24d/sequence.py").read_text().replace("work/build24d","work/build24e").replace("work/build24c\x27/(\x27UPLOADS_","work/build24e\x27/(\x27UPLOADS_")
a=s.index(" old=str(L.parent/\x27w21\x27)");b=s.index(" guard=root/\x27guard.py\x27",a)
s=s[:a]+""" node=root/\x27q_22c714e1_20\x27;ns=\x27/tmp/q_22c714e1\x27;k=root/\x27kit\x27
 args=[\x27/usr/bin/bwrap\x27,\x27--ro-bind\x27,\x27/usr\x27,\x27/usr\x27,\x27--symlink\x27,\x27usr/bin\x27,\x27/bin\x27,\x27--symlink\x27,\x27usr/lib\x27,\x27/lib\x27,\x27--symlink\x27,\x27usr/lib64\x27,\x27/lib64\x27,\x27--ro-bind\x27,\x27/etc\x27,\x27/etc\x27,\x27--proc\x27,\x27/proc\x27,\x27--dev\x27,\x27/dev\x27,\x27--tmpfs\x27,\x27/tmp\x27,\x27--ro-bind\x27,\x27/scratch/jjyeung/uv-python/cpython-3.12.13-linux-x86_64-gnu\x27,\x27/opt/py\x27,\x27--ro-bind\x27,\x27/scratch/jjyeung/envs/p1cpu/lib/python3.12/site-packages\x27,\x27/opt/site\x27,\x27--setenv\x27,\x27PYTHONPATH\x27,\x27/opt/site\x27,\x27--bind\x27,str(node),ns,\x27--ro-bind\x27,str(k),\x27/tmp/kit\x27,\x27--ro-bind\x27,str(root),\x27/tmp/fixture\x27,\x27--chdir\x27,ns]
 for item in J.load(D/(\x27UPLOADS_\x27+name+\x27.json\x27))[\x27files\x27]:
  if item[\x27opaque_name\x27].startswith(\x27u/\x27):args += [\x27--ro-bind\x27,item[\x27local_path\x27],\x27/tmp/up/\x27+item[\x27sha256\x27]]
 J.write(root/\x27view.json\x27,args)
"""+s[b:]
s=s.replace("paths={x[\x27sha256\x27]:x[\x27local_path\x27]", "paths={x[\x27sha256\x27]:\x27/tmp/up/\x27+x[\x27sha256\x27]")
s=s.replace("request.update(config=cfgpin,", "cfgpin[\x27path\x27]=\x27/tmp/fixture/own.json\x27\n request.update(config=cfgpin,")
s=s.replace("shlex.quote(str(Path(sys.executable).parent.parent))", "shlex.quote(\x27/opt/py\x27)")
s=s.replace("shlex.quote(str(guard))+\x27 \"$Q_KIT/b/g.py\"\x27", "\x27/tmp/fixture/guard.py /tmp/kit/b/g.py\x27")
s=s.replace("replacement+=\"        shell=shell.replace", "replacement+=\"        shell=shell.replace",1)
marker=" assert marker in source;source=source.replace(marker,replacement)"
s=s.replace(marker," replacement=replacement.replace(marker,\"        shell=shell.replace(\x27\\\"$Q_KIT/b/a.py\\\"\x27,\x27/tmp/kit/b/a.py\x27).replace(\x27\\\"$Q_KIT/b/d.py\\\"\x27,\x27/tmp/kit/b/d.py\x27)\\n\"+marker)\n"+marker)
s=s.replace("cls.spec.pop(\x27m4\x27,None);cls.spec[\x27uploads\x27]=[];", "cls.spec.pop(\x27m4\x27,None);cls.spec[\x27host_paths\x27]={};cls.spec[\x27uploads\x27]=[];")
s=s.replace("production_kit_seal=", "hidden_host_roots=[\x27/scratch/jjyeung\x27,\x27/home\x27,\x27/data\x27,\x27/data2\x27,\x27/data3\x27],production_kit_seal=")
(D/"sequence.py").write_text(s)
