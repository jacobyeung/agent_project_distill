from pathlib import Path
import hashlib,json,os,subprocess,sys,time
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
names=sys.argv[1:];records=[]
for name in names:
    p=B/(name+'.py');assert p.is_file()
    source=p.read_text()
    assert not any(s in source for s in ('L.parent','/tree_rebuild_w/wn2','/tree_rebuild_w/w9f','/tree_rebuild/')),name
    if name=='make_delivery':
        check=subprocess.run(['df','-BG','--output=avail','/scratch'],check=True,capture_output=True,text=True)
        assert int(check.stdout.splitlines()[-1].rstrip('G'))>=85
    (B/'STATUS.md').write_text('CPU/source qualification is running: '+name+'. GO=false. Completed phase records: QUALIFICATION_LOCAL.json.\n')
    command=[sys.executable,'-I','-s','-B',str(p)]
    if name=='packet_final':command+=['integrated','packet','contract']
    if name=='package':command+=[str(L/json.loads((B/'DELIVERY.json').read_text())['path'])]
    with (B/(name+'.log')).open('w') as stream:
        start=time.time();code=subprocess.run(command,cwd=L,env=os.environ,stdout=stream,stderr=subprocess.STDOUT).returncode
    row=dict(name=name,returncode=code,seconds=time.time()-start,script_sha256=hashlib.sha256(p.read_bytes()).hexdigest())
    records.append(row);(B/'QUALIFICATION_LOCAL.json').write_text(json.dumps(records,indent=2))
    print(json.dumps(row),flush=True)
    if code<0:raise SystemExit('Process was killed; stop without retry.')
    if code:raise SystemExit('Phase failed: '+name)
(B/'STATUS.md').write_text('Requested qualification phases completed. GO=false. Evidence: QUALIFICATION_LOCAL.json.\n')
