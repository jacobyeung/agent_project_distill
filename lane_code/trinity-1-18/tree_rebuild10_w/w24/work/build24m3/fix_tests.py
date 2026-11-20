from common import *
p=L/'out/bind_protected.py';s=p.read_text().replace("'\n'","'\\n'");replace(p,s,0o755)
s=(D/'hidden_final.py').read_text()
s=s.replace("if not (u/h).exists():os.link(p,u/h)","if not (u/h).exists():\n   try:os.link(p,u/h)\n   except OSError as e:\n    if e.errno!=18:raise\n    shutil.copyfile(p,u/h)")
(D/'hidden_final2.py').write_text(s)
s=(D/'wrapper_tests.py').read_text()
s=s.replace("F=D/'db_loop_fixture';F.mkdir();node=F/'node';out=F/'out';out.mkdir()","F=D/'db_loop_fixture';node=F/'node';out=F/'out'")
start=s.index("with sqlite3.connect(db)")
end=s.index("# Exercise the real shell loop")
s=s[:start]+"""value=J.load(out/'db_bytes.json');entry=value['files'][0]
loop=(D/'db_loop.sh').read_text()
"""+s[end:]
s=s.replace("db.parent.mkdir(parents=True)","assert db.is_file()")
s=s.replace("printf call\\\\n", "echo call")
(D/'wrapper_continue.py').write_text(s)
