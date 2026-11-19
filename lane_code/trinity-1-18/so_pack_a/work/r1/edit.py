from pathlib import Path
r=Path(__file__).parent/'src'
p=r/'pack.py';s=p.read_text()
s=s.replace("if m:until=m.group(1)","if m:\n            need(re.search(r'(?:^|[ ;])(?:/usr/bin/)?python3(?:\\s+-[IsB])*\\s+-(?:\\s|$)',line), 'Only Python stdin heredocs are allowed')\n            until=m.group(1)",1)
s=s.replace("        for word in words:opaque(word,extra)","""        # Parse shell punctuation so utility exemptions apply only at command position.
        lex=shlex.shlex(line,posix=True,punctuation_chars=';&|()');lex.whitespace_split=True;lex.commenters='#'
        try:tokens=list(lex)
        except ValueError:tokens=words
        start=True
        utilities=set('head tail sed awk cat wc df hostname nvidia-smi sacct squeue sbatch python3 bash env timeout'.split())
        for word in tokens:
            if word in (';', '&&', '||', '|', '&', '(', ')'):start=True;continue
            if start and word in ('if','then','else','do','!'):continue
            assignment=bool(re.match(r'^[A-Za-z_][A-Za-z_0-9]*=',word))
            if not (start and Path(word).name in utilities):opaque(word,extra)
            if not assignment:start=False""")
s=s.replace("('pack.py','pack_checks.py')","('pack.py','pack_checks.py','pack_structural.py')")
s=s.replace("mode in ('login','fill')","mode in ('login','fill','guard')")
s=s.replace("def plan(c,b):",'''def remote_inputs(c,b):
    f,pay,_,_=structure(b['package']);base=json.loads(f['a/0.json'])
    pins={}
    def add(pin):
        path=pin['path'];opaque(path,c.get('forbidden_extra',()))
        need(type(pin.get('bytes')) is int and pin['bytes']>0,'Required input size missing: '+path)
        need(path not in pins or pins[path]==pin['bytes'],'Conflicting input size: '+path);pins[path]=pin['bytes']
    for archive in base['archives'][1:]:
        for pin in archive['parts']:add(pin)
    assets=json.loads(pay['orchard_h10/vendor/ORCHARD_ASSETS.json'])
    for group in assets['groups']:
        for path,size,sha in group:add(dict(path=path,bytes=size))
    add(assets['bwrap_pin'])
    for path in c['fill']['parts']+[c['fill'][k] for k in ('done','config','receipt','data_receipt')]:
        pin=c.get('remote_input_pins',{}).get(path)
        need(pin is not None,'Required remote input pin missing: '+path);add(dict(pin,path=path))
    return pins

def remote_preflight(c,b):
    return python_block("from pathlib import Path\\npins=%r\\nfor name,size in pins.items():\\n p=Path(name)\\n if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)\\nprint('inputs ready')"%remote_inputs(c,b))

def detached_fill(body,p):
    # Exclusive launch directory survives transport loss and prevents duplicate hashing.
    code="from pathlib import Path\\np=Path(%r)\\n(p/'a/f.lock').mkdir(mode=0o700)\\n(p/'a/f.sh').write_text(%r)"%(p,body)
    return HEADER+python_block(code)+'cd '+shlex.quote(p)+'\\nsetsid nohup bash a/f.sh </dev/null >a/f.log 2>&1 &\\n'

def plan(c,b):''')
old="scripts=dict(place=HEADER+python_block(place_code(b)),fill=HEADER+shell_join(fill_argv(c,p))+'\\ncd '+shlex.quote(p)+'\\n'+check+'\\nprintf \"0\\\\n\" > a/1.txt\\n',cpu=HEADER+adapted_script(c,'cpu',p,b['package']))"
new="""fill_body=HEADER+'cd '+shlex.quote(p)+'\\ntrap \\\'rc=$?; if [ "$rc" != 0 ]; then printf "%s\\\\n" "$rc" >a/f.exit; fi\\\' EXIT\\n'+shell_join(fill_argv(c,p))+'\\n'+check+'\\nprintf "0\\\\n" > a/1.txt\\n'
    scripts=dict(preflight=HEADER+remote_preflight(c,b),place=HEADER+python_block(place_code(b)),fill=detached_fill(fill_body,p),cpu=HEADER+adapted_script(c,'cpu',p,b['package']))
    scripts['fill_poll']=HEADER+'cd '+shlex.quote(p)+'\\nif test -f a/1.txt; then test "$(cat a/1.txt)" = 0; printf "complete\\\\n"; elif test -f a/f.exit; then tail -c 8192 a/f.log >&2; exit 1; else printf "wait\\\\n"; tail -c 8192 a/f.log >&2; fi\\n'"""
assert old in s;s=s.replace(old,new)
s=s.replace("if k!='poll':","if k not in ('poll','fill_poll','preflight','gpu'):")
s=s.replace("    for phase in phases:\n        if phase=='gpu':","""    for phase in phases:
        if phase=='place':
            r=invoke('preflight');need(r.returncode==0,'Remote input preflight failed before placement: '+r.stderr.decode(errors='replace'))
        if phase=='gpu':""")
s=s.replace("        r=invoke(phase);need(r.returncode==0,'Remote '+phase+' failed: '+r.stderr.decode(errors='replace'))","""        r=invoke(phase);need(r.returncode==0,'Remote '+phase+' failed: '+r.stderr.decode(errors='replace'))
        if phase=='fill':
            deadline=time.monotonic()+int(c['remote'].get('fill_wait',1800))
            while True:
                sleeper(60);need(time.monotonic()<deadline,'Fill wait deadline exceeded; inspect a/f.log; do not relaunch')
                r=invoke('fill_poll');need(r.returncode==0,'Fill poll failed; inspect a/f.log; do not relaunch: '+r.stderr.decode(errors='replace'))
                state=r.stdout.decode().strip();need(state in ('wait','complete'),'Unexpected fill receipt')
                if state=='complete':break""")
s=s.replace("'fill','submit','all'","'fill','gpu','submit','all'")
s=s.replace("'submit':['cpu','gpu']","'gpu':['gpu'],'submit':['cpu','gpu']")
s=s.replace("a.action in ('submit','all')","a.action in ('gpu','submit','all')")
# Refuse missing build inputs with their names before invoking a native builder.
s=s.replace("    for pin in s.get('inputs',[]):need(file_digest(pin['path'])==pin['sha256'],'Builder input differs')","    for pin in s.get('inputs',[]):\n        need(Path(pin['path']).is_file(),'Required builder input missing: '+pin['path']);need(file_digest(pin['path'])==pin['sha256'],'Builder input differs')")
p.write_text(s)

p=r/'pack_checks.py';s=p.read_text()
s=s.replace("code='import runpy,sys,torch;torch.set_num_threads(8);sys.path[:0]=sys.argv[2:];runpy.run_path(sys.argv[1],run_name=\"preflight_import\")'", "code='import runpy,sys,torch;torch.set_num_threads(8);sys.path[:0]=sys.argv[2:];'+('import h1eval.h10.launch' if n=='h1eval/h10/launch.py' else 'runpy.run_path(sys.argv[1],run_name=\"preflight_import\")')")
s=s.replace("ast.Module(body=env_nodes,type_ignores=[])","ast.Module(body=env_nodes)")
s=s.replace("return proof\n\ndef trap", "proof['python']=sys.version;return proof\n\ndef trap")
s=s.replace("raw=w/'1.tgz';raw.write_bytes(P.tar_bytes(f));b=dict(token=pub['token'],delivery=str(raw),sha256=P.file_digest(raw))", """state=Path(c['work'])/'BUILD.json'
    if state.is_file():
        b=P.built(c);P.need(P.untar(Path(b['delivery']).read_bytes())==f,'Login probe delivery differs')
    else:
        raw=w/'1.tgz';raw.write_bytes(P.tar_bytes(f));b=dict(token=pub['token'],delivery=str(raw),sha256=P.file_digest(raw))""")
s=s.replace("compiled_sources=len(sources))","compiled_sources=len(sources),delivery_sha256=b['sha256'],recorded_delivery=state.is_file())")
s=s.replace("    mapping=validate_mirrors(c);f,pay,pub,plan=P.structure(package);", """    if c.get('fill_mode','mirrors')=='structural':
        import pack_structural as S
        original=P.fingerprint(P.package_files(package));target,small=S.rebind(w/'standins',package)
        cfg=dict(c,fill_mode='mirrors',mirrors=small['mirrors'],fill=small['fill'],old_identities=[],max_read_bytes=10*1024**2)
        result=fill(target,w,cfg);result.update(mode='structural',source_tree=original,standin_bytes=sum(x['bytes'] for x in small['mirrors'].values()),production_archive_identity=False)
        P.need(P.fingerprint(P.package_files(package))==original,'Structural probe changed delivery');return result
    P.need(c.get('fill_mode','mirrors')=='mirrors','Unknown fill mode')
    mapping=validate_mirrors(c);f,pay,pub,plan=P.structure(package);""")
p.write_text(s)

# Production structural stand-ins use the same generator as the regression fixtures.
s=(r/'test_support.py').read_text();start=s.index('def jd(');s='"""Tiny structural stand-ins; never production identity evidence."""\nimport ast, io, json, re, tarfile\nfrom pathlib import Path\nimport pack as P\n'+s[start:]
s=s.replace('def fixture(w):','def rebind(w,package):').replace('P.structure(B5);f=P.normalize_wrapper(f,True);pay=dict(pay)','P.structure(package);pay=dict(pay)')
start=s.index('    c=dict(python=');s=s[:start]+"    c=dict(mirrors=mapping,fill=dict(parts=[x['path'] for x in parts],done=done['path'],object=binding['object'],lineage='SFT',step=600,**prep_paths))\n    return p,c\n"
(r/'pack_structural.py').write_text(s)
# Fixture pins now supply remote stat checks without reading production archives.
p=r/'test_support.py';s=p.read_text();s=s.replace("    (w/'ledger.jsonl').write_text('');", "    c['remote_input_pins']={k:dict(bytes=v['bytes']) for k,v in mapping.items()}\n    (w/'ledger.jsonl').write_text('');");p.write_text(s)
# Existing expectations change only where behavior intentionally changes.
p=r/'test_pack.py';s=p.read_text().replace(",'head -n 1 /tmp/0'",'').replace("{'place','fill','cpu','poll','gpu'}","{'preflight','place','fill','fill_poll','cpu','poll','gpu'}");p.write_text(s)
