"""Opt-in read-package preflight and bounded Orchard planner. Python 3.6."""
import argparse, ast, base64, gzip, hashlib, io, json, os, re, resource, shlex, subprocess, sys, tarfile, time
from pathlib import Path, PurePosixPath
PREFIX='a15_cot_ap'
ROOT='/project/community/jjyeung/okh7'
PYTHON='/scratch/jjyeung/envs/p1cpu/bin/python'
TERMS=tuple('split revsi vsibench scannet arkit distill qgen sam qwen h1 h10 head routing faithful devs1 g3t camera displacement rotation movement distance r0 scannetpp direction own room selector parity benchmark dataset model student_pilot e2e_reader evalpath carrier leg-s1 dev-s1 tower candidates_argmax perception_memo'.split())
class Rejected(ValueError):pass
def need(ok,msg):
    if not ok:raise Rejected(msg)
def digest(b):return hashlib.sha256(b).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':')).encode()
def read(p):return json.loads(Path(p).read_text())
def write(p,v):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_text(json.dumps(v,sort_keys=True,indent=2)+'\n');p.chmod(0o600)
def file_digest(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024**2),b''):h.update(b)
    return h.hexdigest()
def token(v):
    need(isinstance(v,str) and re.fullmatch('[a-f][0-9a-f]{10,15}',v),'Invalid explicit token');return v
def opaque(v,extra=()):
    hits=[w for w in TERMS+tuple(extra) if w.lower() in str(v).lower()]
    need(not hits,'Non-opaque surface %r: %s'%(v,','.join(hits)))
def safe_name(n):
    p=PurePosixPath(n);need(n and not p.is_absolute() and '..' not in p.parts and str(p)==n,'Unsafe member '+n)
def untar(raw):
    out={};total=0
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as t:
        for m in t:
            safe_name(m.name);need(m.isfile() and m.name not in out,'Unsafe/duplicate member '+m.name)
            total+=m.size;need(total<=128*1024**2,'Metadata archive too large');out[m.name]=t.extractfile(m).read()
    return out
def tar_bytes(files):
    buf=io.BytesIO()
    with gzip.GzipFile(fileobj=buf,mode='wb',mtime=0) as gz:
        with tarfile.open(fileobj=gz,mode='w') as t:
            for n,b in sorted(files.items()):
                safe_name(n);m=tarfile.TarInfo(n);m.size=len(b);m.mode=0o600;t.addfile(m,io.BytesIO(b))
    return buf.getvalue()
def extract(files,root):
    root=Path(root);root.mkdir(parents=True,exist_ok=False,mode=0o700)
    for n,b in files.items():
        safe_name(n);p=root/n;p.parent.mkdir(parents=True,exist_ok=True,mode=0o700);p.write_bytes(b);p.chmod(0o600)
    return root
def package_files(p):
    p=Path(p)
    if p.is_file():return untar(p.read_bytes())
    out={}
    for f in sorted(p.rglob('*')):
        need(not f.is_symlink(),'Package symlink')
        if f.is_file():out[str(f.relative_to(p))]=f.read_bytes()
    return out
def bundle(batch):
    lines=[s for s in batch.decode().splitlines() if s.startswith('b=bytes.fromhex(')]
    need(len(lines)==1,'Expected one batch bundle');v=ast.parse(lines[0]).body[0].value
    need(isinstance(v,ast.Call) and isinstance(v.func,ast.Attribute) and isinstance(v.func.value,ast.Name) and v.func.value.id=='bytes' and v.func.attr=='fromhex' and len(v.args)==1 and not v.keywords,'Invalid bundle encoding')
    return untar(bytes.fromhex(ast.literal_eval(v.args[0])))
def structure(package,c=None):
    c=c or {};f=package_files(package);v=json.loads(f['0.json']);token(v['token']);m=json.loads(f['PACKAGE.json'])
    need(f['CONFIG.json']==f['0.json'] and m['token']==v['token'],'Descriptor/token differs')
    for n,h in m['files'].items():need(n in f and digest(f[n])==h,'Package pin differs: '+n)
    need(digest(f['0.tgz'])==v['payload_sha256'] and len(f['0.tgz'])==v['payload_bytes'],'Payload pin differs')
    pay=untar(f['0.tgz']);plan=json.loads(pay['9.json'])
    need(plan['token']==v['token'] and digest(canonical(plan))==v['plan_sha256'],'Plan differs')
    for n,pin in plan['payload_pins'].items():need(n in pay and digest(pay[n])==pin['sha256'] and len(pay[n])==pin['bytes'],'Payload member differs: '+n)
    b=bundle(f['BATCH.sh']);need(set(b)=={'0.py','0.json','7.py'},'Bundle inventory differs');need(json.loads(b['0.json'])==v,'Bundle descriptor differs');need(b['7.py']==f['a/6.py'],'Bundle operator differs')
    need(("'a'+j+%r"%v['token']).encode() in f['BATCH.sh'],'Temporary token differs')
    for old in c.get('old_identities',[]):
        need(old,'Empty identity')
        for n,data in list(f.items())+list(pay.items())+list(b.items()):
            need(old not in n and old.encode() not in data and old.encode().hex().encode() not in data,'Old identity in '+n)
    for n in f:opaque(n,c.get('forbidden_extra',()))
    return f,pay,v,plan
def shell_lines(text):
    until=None
    for line in text.splitlines():
        if until:
            if line.strip()==until:until=None
            continue
        if line.lstrip().startswith('#') and not line.lstrip().startswith('#SBATCH'):continue
        yield line
        m=re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z_0-9]*)['\"]?",line)
        if m:
            need(re.match(r'^\s*(?:exec\s+)?(?:/usr/bin/)?python3(?:\s+-[IsB])*\s+-(?:\s|$)',line), 'Only Python stdin heredocs are allowed')
            until=m.group(1)
    need(until is None,'Unterminated heredoc')
def shell_privacy(text,extra=()):
    for line in shell_lines(text):
        line=line.replace('#SBATCH','')
        try:words=shlex.split(line,comments=True)
        except ValueError:words=[line]
        # Parse shell punctuation so utility exemptions apply only at command position.
        lex=shlex.shlex(line,posix=True,punctuation_chars=';&|()');lex.whitespace_split=True;lex.commenters='#'
        try:tokens=list(lex)
        except ValueError:tokens=words
        start=True
        utilities=set('head tail sed awk cat wc df hostname nvidia-smi sacct squeue sbatch python3 bash env timeout'.split())
        for word in tokens:
            if word in (';', '&&', '||', '|', '&', '(', ')'):start=True;continue
            if start and word in ('if','then','else','do','!','{','}'):continue
            assignment=bool(re.match(r'^[A-Za-z_][A-Za-z_0-9]*=',word))
            system=word in utilities or (str(Path(word).parent) in ('/bin','/usr/bin') and Path(word).name in utilities)
            if not (start and system):opaque(word,extra)
            if not assignment:start=False
        for name in re.findall(r'a15_cot_ap[0-9a-z]+',line):need(re.fullmatch(PREFIX+'[a-f][0-9a-f]{10,15}',name),'Invalid job name '+name)
def privacy(p,c):
    f,pay,v,plan=structure(p,c);extra=c.get('forbidden_extra',());shell_privacy(f['BATCH.sh'].decode(),extra)
    opaque(ROOT+'/'+PREFIX+v['token'],extra);opaque(plan['pool'],extra)
    need(b'umask 077\n' in f['BATCH.sh'],'Batch must set umask 077');need(b'mode=0o700' in f['BATCH.sh'],'Private job temporary directory missing')
    if '2.json' in f:
        receipt=json.loads(f['2.json'])
        for arg in receipt.get('argv',[]):opaque(arg,extra)
        names=[x.split('=',1)[1] for x in receipt.get('argv',[]) if x.startswith('--job-name=')]
        need(names==[PREFIX+v['token']],'Checked job name differs')
    return dict(names=len(f),scope='visible surfaces; sealed archive bytes excluded')
def normalize_wrapper(f,enabled=False):
    out=dict(f)
    if not enabled:return out
    t=out['BATCH.sh'].decode();need(t.count('head -n 1 "$L"')==1,'Unrecognized EXIT capture')
    t=t.replace('head -n 1 "$L"',"sed -n '1p' \"$L\"")
    if 'umask 077\n' not in t:t=t.replace('set -uo pipefail\n','set -uo pipefail\numask 077\n',1)
    out['BATCH.sh']=t.encode();m=json.loads(out['PACKAGE.json']);m['files']['BATCH.sh']=digest(out['BATCH.sh']);out['PACKAGE.json']=(json.dumps(m,sort_keys=True,indent=2)+'\n').encode();return out
def environment(root):
    return dict(PATH='/usr/local/bin:/usr/bin:/bin',HOME=str(root),USER='jjyeung',CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',OPENBLAS_NUM_THREADS='8',TOKENIZERS_PARALLELISM='false',TMPDIR=str(root),XDG_CACHE_HOME=str(root/'0'))
def run(argv,cwd,log,env=None,seconds=180):
    with Path(log).open('wb') as out:r=subprocess.run(['nice','-n','10']+list(argv),cwd=str(cwd),env=env or environment(Path(cwd)),stdout=out,stderr=subprocess.STDOUT,timeout=seconds)
    need(r.returncode==0,'Command failed (%s); see %s'%(r.returncode,log))
def fingerprint(f):return digest(canonical({n:digest(b) for n,b in f.items()}))
def source_fingerprint():return {n:file_digest(Path(__file__).parent/n) for n in ('pack.py','pack_checks.py','pack_structural.py')}
def limits():
    resource.setrlimit(resource.RLIMIT_AS,(28*1024**3,28*1024**3))
    if hasattr(os,'sched_getaffinity'):os.sched_setaffinity(0,set(sorted(os.sched_getaffinity(0))[:8]))
def probe(mode,p,w,c):
    w=Path(w);w.mkdir(parents=True,exist_ok=False,mode=0o700);write(w/'0.json',c)
    py='/usr/bin/python3' if mode in ('login','fill','guard') else c.get('python',PYTHON)
    run([py,'-I','-s','-B',str(Path(__file__).with_name('pack_checks.py')),mode,str(p),str(w),str(w/'0.json')],w,w/'0.log',seconds=c.get('check_timeout',240));return read(w/'1.json')
def source_preflight(c):
    """Apply the native D embedded-asset equality before any release operation."""
    required_inputs(c)
    spec=c.get('builder')
    if not spec:return {'fixture_only':True}
    argv=spec['argv'];source=Path(argv[argv.index('--source')+1]) if '--source' in argv else Path(spec['path'])
    pins={str(source):file_digest(source)}
    for pin in spec.get('inputs',[]):
        need(file_digest(pin['path'])==pin['sha256'],'Builder input differs');pins[pin['path']]=pin['sha256']
    need(file_digest(spec['path'])==spec['sha256'],'Builder hash differs')
    if source.name=='build_d.py':
        here=source.parent;script=here/'o_build_D.sh';checker=here/'check_release_d.py'
        pins[str(script)]=file_digest(script);pins[str(checker)]=file_digest(checker)
        assets=ast.literal_eval(next(l for l in script.read_text().splitlines() if l.startswith('assets = ')).split('=',1)[1])
        native=argv[argv.index('--')+1:] if '--' in argv else argv
        need(len(native)>=5,'Native D inputs absent');items=Path(native[3])
        for name,asset in assets.items():
            raw=gzip.decompress(base64.b64decode(asset['data']));need(digest(raw)==asset['sha256'],'Native embedded hash differs: '+name)
            path=items if name=='items/dist580.json' else here/('build_d.py' if name=='b.py' else name)
            need(raw==path.read_bytes(),'Native source differs from embedded asset: '+name);pins[str(path)]=file_digest(path)
        return dict(kind='d',assets=len(assets),pins=pins)
    return dict(kind=source.name,pins=pins)
def local_check(c,p,w):
    w=Path(w);w.mkdir(parents=True,exist_ok=False,mode=0o700);f,_,v,_=structure(p,c);r={'source':source_preflight(c),'privacy':privacy(p,c)}
    for mode in ('logic','guard','trap','stop','login','fill','receipt'):r[mode]=probe(mode,p,w/mode,c)
    result=dict(passed=True,token=v['token'],tree=fingerprint(f),checker=source_fingerprint(),config=digest(canonical(c)),checks=r);write(w/'CHECK.json',result);return result
def ledger_check(c,tok):
    token(tok);p=Path(c['ledger']);need(p.is_file(),'Trinity token ledger missing');need(tok not in p.read_text(),'Token already appears in Trinity ledger');return file_digest(p)
def required_inputs(c):
    for pin in c.get('required_inputs',[]):
        name=pin.get('name',pin.get('path','unnamed'));path=Path(pin['path'])
        need(path.is_file(),'Required input missing: '+name+' ('+str(path)+')')
        need(path.stat().st_size<=c.get('max_required_input_bytes',128*1024**2),'Required input exceeds local metadata budget: '+name)
        if 'sha256' in pin:need(file_digest(path)==pin['sha256'],'Required input hash differs: '+name)
    return {'passed':True,'inputs':len(c.get('required_inputs',[]))}
def state_root(c):
    p=Path(c['work']).resolve();p.mkdir(parents=True,exist_ok=True,mode=0o700);return p
def build(c,explicit):
    required_inputs(c)
    tok=token(explicit);ledger=ledger_check(c,tok);w=state_root(c);need(not (w/'BUILD.json').exists(),'Build state exists');s=c['builder'];path=Path(s['path']);need(file_digest(path)==s['sha256'],'Builder hash differs')
    for pin in s.get('inputs',[]):
        need(Path(pin['path']).is_file(),'Required builder input missing: '+pin['path']);need(file_digest(pin['path'])==pin['sha256'],'Builder input differs')
    cwd=w/'b';cwd.mkdir(mode=0o700);env=environment(cwd);env.update({k:str(v).replace('{work}',str(cwd)) for k,v in s.get('env',{}).items()});env.pop('SO_PACK_EXPLICIT_TOKEN',None);env.pop('SO_PACK_TOKEN',None)
    args=[str(x).replace('{work}',str(cwd)).replace('{token}',tok) for x in s['argv']]
    run([c.get('python',PYTHON),'-I','-s','-B',str(path)]+args,cwd,w/'build.log',env,c.get('build_timeout',300))
    r=read(s['report'].replace('{work}',str(cwd)))[s.get('key','D')];need(r['token']==tok,'Builder token differs');d=Path(r['delivery_dir'])/'1.tgz';need(file_digest(d)==r['delivery_sha256'],'Builder delivery differs')
    original=d.read_bytes();f=normalize_wrapper(untar(original),c.get('normalize_wrapper',False));p=extract(f,w/'p');structure(p,c);d=w/'1.tgz';d.write_bytes(tar_bytes(f) if c.get('normalize_wrapper',False) else original);d.chmod(0o600)
    b=dict(token=tok,package=str(p),delivery=str(d),sha256=file_digest(d),tree=fingerprint(f),ledger_sha256=ledger,native_report=str(Path(s['report'].replace('{work}',str(cwd)))),native_budget_fits=r.get('budget_fits'),native_budget_gpu_seconds=r.get('budget_gpu_seconds'));write(w/'BUILD.json',b);return b
def built(c):
    b=read(state_root(c)/'BUILD.json');token(b['token']);need(file_digest(b['delivery'])==b['sha256'] and fingerprint(package_files(b['package']))==b['tree'],'Built bytes changed');need(untar(Path(b['delivery']).read_bytes())==package_files(b['package']),'Delivery differs from tested tree');return b
def checked(c):
    b=built(c);v=read(state_root(c)/'CHECK.json');need(v['checks']['source']==source_preflight(c),'Native source context changed');need(v['passed'] and v['tree']==b['tree'] and v['checker']==source_fingerprint() and v['config']==digest(canonical(c)),'Stale or missing local checks');return b
HEADER='''#!/bin/bash
set -euo pipefail
umask 077
export PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung CUDA_VISIBLE_DEVICES=
trap 'rc=$?; if [ "$rc" != 0 ]; then printf "phase exit %s line %s\\n" "$rc" "$LINENO" >&2; fi' EXIT
'''
def python_block(code):return "/usr/bin/python3 -I -s -B - <<'PYCODE'\n"+code+"\nPYCODE\n"
def remote_path(b):return ROOT+'/'+PREFIX+token(b['token'])
def place_code(b):
    return '''import hashlib,io,os,tarfile
from pathlib import Path
os.umask(0o077)
p=Path(%r);raw=bytes.fromhex(%r)
assert hashlib.sha256(raw).hexdigest()==%r
p.mkdir(mode=0o700)
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
    seen=set()
    for m in t:
        q=Path(m.name)
        assert m.isfile() and not q.is_absolute() and '..' not in q.parts and m.name not in seen
        seen.add(m.name);f=p/q;f.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
        with f.open('xb') as out:out.write(t.extractfile(m).read())
        f.chmod(0o600)
(p/'a').chmod(0o700)
print('placed')
'''%(remote_path(b),Path(b['delivery']).read_bytes().hex(),b['sha256'])
def fill_argv(c,p):
    f=c['fill'];argv=['/usr/bin/python3','-I','-s','-B',p+'/a/4.py','--parts']+f['parts']
    for k in ('done','object','config','receipt','data_receipt','lineage','step'):argv+=['--'+k.replace('_','-'),str(f[k])]
    for k,n in (('out','a/export.json'),('prep-tar','a/6'),('base-inputs','a/0.json'),('inputs-out','a/1.json')):argv+=['--'+k,p+'/'+n]
    for arg in argv:opaque(arg,c.get('forbidden_extra',()))
    return argv
def shell_join(a):return ' '.join(shlex.quote(str(x)) for x in a)
def adapted_script(c,key,p,package=None):
    s=c['remote'][key];path=Path(s['path']);need(file_digest(path)==s['sha256'],'Sealed script hash differs: '+key);text=path.read_text();old=s.get('old_token')
    if old:
        token(old);need(s.get('adapt_token') is True,'Explicit adaptation required');text=text.replace(PREFIX+old,Path(p).name);need(old not in text,'Old script token survived')
    need(all(x.strip('"\'')==p for x in re.findall(r'^(?:export )?P=([^;\n]+)',text,re.M)),'Fixed package path differs')
    for literal in re.findall(PREFIX+r'([a-f0-9]{11,16})(?![a-f0-9])',text):need(literal==Path(p).name[len(PREFIX):],'Foreign job/package token in script')
    text='P='+shlex.quote(p)+'\nT='+shlex.quote(c['remote']['walltime'])+'\n'+text;shell_privacy(text,c.get('forbidden_extra',()))
    need('3.py check' in text,'Native entry check absent')
    for line in shell_lines(text):
        if '3.py check' in line or '3.py submit' in line:
            need('--gpus 1' in line,'Native GPU count differs')
            times=re.findall(r'--time\s+["\']?([0-9]{2}:[0-9]{2}:[0-9]{2}|\$T)',line)
            need(times and all(t in ('$T',c['remote']['walltime']) for t in times),'Native walltime differs')
    if key=='cpu':need(text.count('sbatch --parsable')==1 and 'a/5.py' in text and 'a/4.txt' in text,'CPU script differs')
    else:
        for m in ('bundle_guard_passed','entry_sequence_passed','MEMORY.json','3.py submit','a/8.txt'):need(m in text,'Native GPU gate absent: '+m)
        if package and b'def validate_full_reader' in (Path(package)/'a/5.py').read_bytes():need('full_reader_passed' in text,'Native full reader gate absent')
        need(text.count('JOB_REPLY=$(')==1,'Native submission boundary absent')
        text=text.replace('JOB_REPLY=$(', 'mkdir "$P/a/g.lock"\nJOB_REPLY=$(',1)
    return text
def heredocs(text):
    out=[];end=None;lines=[];python=False
    for line in text.splitlines():
        if end:
            if line.strip()==end:
                if python:out.append('\n'.join(lines)+'\n')
                end=None;lines=[]
            else:lines.append(line)
        else:
            m=re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z_0-9]*)['\"]?",line)
            if m:end=m.group(1);python='python' in line
    return out
def remote_inputs(c,b):
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
    return python_block("from pathlib import Path\npins=%r\nfor name,size in pins.items():\n p=Path(name)\n if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)\nprint('inputs ready')"%remote_inputs(c,b))

def detached_fill(body,p):
    # Exclusive launch directory survives transport loss and prevents duplicate hashing.
    code="from pathlib import Path\np=Path(%r)\n(p/'a/f.lock').mkdir(mode=0o700)\n(p/'a/f.sh').write_text(%r)"%(p,body)
    return HEADER+python_block(code)+'cd '+shlex.quote(p)+'\nsetsid nohup bash a/f.sh </dev/null >a/f.log 2>&1 &\n'

def plan(c,b):
    p=remote_path(b);opaque(p,c.get('forbidden_extra',()));check=shell_join(['/usr/bin/python3','-I','-s','-B','3.py','check','--gpus','1','--time',c['remote']['walltime']])
    fill_body=HEADER+'cd '+shlex.quote(p)+'\ntrap \'rc=$?; if [ "$rc" != 0 ]; then printf "%s\\n" "$rc" >a/f.exit; fi\' EXIT\n'+shell_join(fill_argv(c,p))+'\n'+check+'\nprintf "0\\n" > a/1.txt\n'
    shell_privacy(fill_body,c.get('forbidden_extra',()))
    scripts=dict(preflight=HEADER+remote_preflight(c,b),place=HEADER+python_block(place_code(b)),fill=detached_fill(fill_body,p),cpu=HEADER+adapted_script(c,'cpu',p,b['package']))
    scripts['fill_poll']=HEADER+'cd '+shlex.quote(p)+'\nif test -f a/1.txt; then test "$(cat a/1.txt)" = 0; printf "complete\\n"; elif test -f a/f.exit; then tail -c 8192 a/f.log >&2; exit 1; else printf "wait\\n"; tail -c 8192 a/f.log >&2; fi\n'
    job='P='+p+'\nJ=$(cat "$P/a/4.txt")\n[[ "$J" =~ ^[0-9]+$ ]]\n'
    scripts['poll']=HEADER+job+'if ! sacct -n -X -j "$J" -o State --parsable2; then printf "accounting unavailable for %s\\n" "$J" >&2; exit 75; fi\n'
    scripts['gpu']=HEADER+job+'S=$(sacct -n -X -j "$J" -o State --parsable2)\n[[ "${S%%|*}" = COMPLETED ]]\ntest -s "$P/a/c/CPU.json"\n'+adapted_script(c,'gpu',p,b['package'])
    w=state_root(c)/'commands';w.mkdir(exist_ok=True,mode=0o700)
    for k,text in scripts.items():
        shell_privacy(text,c.get('forbidden_extra',()));f=w/(k+'.sh');f.write_text(text);f.chmod(0o600);run(['bash','-n',str(f)],w,w/(k+'.log'))
        for i,body in enumerate(heredocs(text)):
            src=w/(k+str(i)+'.py');src.write_text(body);run(['/usr/bin/python3','-I','-s','-B','-c','import sys;compile(open(sys.argv[1],"rb").read(),sys.argv[1],"exec")',str(src)],w,w/(k+str(i)+'.log'))
    return {k:str(w/(k+'.sh')) for k in scripts}
def command(c,script):
    secs=int(c['remote'].get('timeout',300));need(1<=secs<=300,'Remote timeout must be 1..300');ossh=c['remote']['ossh'];need(Path(ossh).is_absolute(),'ossh must be absolute')
    return 'pv -q -L 8000000 '+shlex.quote(script)+' | timeout '+str(secs)+' bash '+shlex.quote(ossh)+' '+shlex.quote('env -i PATH=/usr/local/bin:/usr/bin:/bin HOME=/tmp USER=jjyeung bash -s')
def poll_state(text):
    states=[s.strip().split('|')[0].split()[0].split('+')[0] for s in text.splitlines() if s.strip()]
    if not states:return 'wait'
    need(len(states)==1,'Ambiguous accounting state')
    if states[0]=='COMPLETED':return 'complete'
    if states[0] in ('PENDING','RUNNING','CONFIGURING','COMPLETING'):return 'wait'
    raise Rejected('CPU job ended: '+states[0])
def execute(c,scripts,phases,yes=False,explicit=None,call=None,sleeper=time.sleep):
    b=checked(c)
    if 'cpu' in phases or 'gpu' in phases:need(yes and explicit==b['token'],'Submit requires --yes and exact token')
    def actual(k):
        if k not in ('poll','fill_poll','preflight','gpu'):
            marker=state_root(c)/(k+'.attempt');need(not marker.exists(),'Already attempted '+k);marker.write_text(str(time.time()))
        cmd=command(c,scripts[k]);print(cmd,flush=True)
        log=state_root(c)/('call_'+k+'_'+str(time.time_ns() if hasattr(time,'time_ns') else int(time.time()*1000000))+'.json')
        try:r=subprocess.run(['nice','-n','10','bash','-o','pipefail','-c',cmd],stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=310,env=environment(state_root(c)))
        except subprocess.TimeoutExpired as e:
            write(log,dict(phase=k,timeout=True,stdout=(e.stdout or b'').decode(errors='replace'),stderr=(e.stderr or b'').decode(errors='replace')));raise
        write(log,dict(phase=k,returncode=r.returncode,stdout=r.stdout.decode(errors='replace'),stderr=r.stderr.decode(errors='replace')));return r
    invoke=call or actual
    for phase in phases:
        if phase=='place':
            r=invoke('preflight');need(r.returncode==0,'Remote input preflight failed before placement: '+r.stderr.decode(errors='replace'))
        if phase=='gpu':
            errors=0;deadline=time.monotonic()+int(c['remote'].get('cpu_wait',14400))
            while True:
                need(time.monotonic()<deadline,'CPU wait deadline exceeded');r=invoke('poll')
                if r.returncode:
                    need(r.returncode==75,'Poll transport failed; do not retry: '+r.stderr.decode(errors='replace'))
                    errors+=1;need(errors<3,'Repeated sacct error: '+r.stderr.decode(errors='replace'))
                else:
                    errors=0
                    if poll_state(r.stdout.decode())=='complete':
                        sleeper(60);break
                sleeper(60)
        r=invoke(phase);need(r.returncode==0,'Remote '+phase+' failed: '+r.stderr.decode(errors='replace'))
        if phase=='fill':
            deadline=time.monotonic()+int(c['remote'].get('fill_wait',1800))
            while True:
                sleeper(60);need(time.monotonic()<deadline,'Fill wait deadline exceeded; inspect a/f.log; do not relaunch')
                r=invoke('fill_poll');need(r.returncode==0,'Fill poll failed; inspect a/f.log; do not relaunch: '+r.stderr.decode(errors='replace'))
                state=r.stdout.decode().strip();need(state in ('wait','complete'),'Unexpected fill receipt')
                if state=='complete':break
def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('build','check','place','fill','gpu','submit','all'));p.add_argument('--config',required=True);p.add_argument('--enable',action='store_true');p.add_argument('--token');p.add_argument('--yes',action='store_true');p.add_argument('--execute-remote',action='store_true');a=p.parse_args(argv);need(a.enable,'Default OFF: pass --enable')
    os.umask(0o077);limits();c=read(a.config);w=state_root(c)
    if a.action in ('build','all'):print(json.dumps(build(c,a.token),sort_keys=True))
    if a.action in ('check','all'):
        b=built(c);r=local_check(c,b['package'],w/('c'+os.urandom(4).hex()));write(w/'CHECK.json',r);plan(c,b)
    if a.action in ('place','fill','gpu','submit','all'):
        b=checked(c);scripts=plan(c,b);phases={'place':['place'],'fill':['fill'],'gpu':['gpu'],'submit':['cpu','gpu'],'all':['place','fill','cpu','gpu']}[a.action]
        if a.action in ('gpu','submit','all'):need(a.yes and a.token==b['token'],'Submit requires --yes and exact token')
        for phase in phases:print(command(c,scripts[phase]))
        if a.execute_remote:execute(c,scripts,phases,a.yes,a.token)
    return 0
if __name__=='__main__':
    try:sys.exit(main())
    except (Rejected,KeyError,OSError,subprocess.TimeoutExpired) as e:print('REJECTED: '+str(e),file=sys.stderr);sys.exit(1)
