#!/usr/bin/env python3
"""Opt-in read-package release gate. Python 3.6 standard library on login.

No builder or package source is rewritten. Local paths and remote logical paths
are connected by an explicit, hash-checked mirror table during the dry fill.
"""
from __future__ import print_function
import argparse
import ast
import base64
import datetime
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shlex
import shutil
import subprocess
import sys
import tarfile
import time

VERSION = 1
TOKEN = r'[a-f][0-9a-f]{10,15}'
PREFIX = 'a15_cot_ap'
REMOTE_ROOT = '/project/community/jjyeung/okh7'
FORBIDDEN = ('split','revsi','vsibench','scannet','arkit','distill','qgen',
             'sam','qwen','h1','h10','head','routing','faithful','devs1','g3t',
             'camera','displacement','rotation','movement','distance','r0',
             'scannetpp','direction','own','room','selector','parity',
             'benchmark','dataset','model','student_pilot','e2e_reader',
             'evalpath','carrier','leg-s1','dev-s1','tower','candidates_argmax',
             'perception_memo')
LIMIT = 32 * 1024 * 1024


class GateError(Exception):
    pass


def require(ok, message):
    if not ok:
        raise GateError(message)


def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def limit_resources():
    """Local probes use at most eight CPUs and 28 GiB of virtual memory."""
    if hasattr(os,'sched_getaffinity'):
        available=sorted(os.sched_getaffinity(0))
        os.sched_setaffinity(0,set(available[:8]))
    import resource
    soft,hard=resource.getrlimit(resource.RLIMIT_AS)
    cap=28*1024**3
    if hard!=resource.RLIM_INFINITY:cap=min(cap,hard)
    if soft!=resource.RLIM_INFINITY:cap=min(cap,soft)
    resource.setrlimit(resource.RLIMIT_AS,(cap,cap))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n')


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',',':')).encode())


def inside(path, root):
    try:
        Path(path).resolve().relative_to(Path(root).resolve())
        return True
    except ValueError:
        return False


def safe_name(name):
    p = PurePosixPath(name)
    require(name and not p.is_absolute() and '..' not in p.parts
            and str(p) == name and name != '.', 'Unsafe/noncanonical member: '+name)


def token(value):
    require(isinstance(value, str) and re.fullmatch(TOKEN, value), 'Invalid explicit token')
    return value


def opaque(value, where, more=()):
    value = str(value).lower()
    require(all(isinstance(w,str) and w for w in more),'Invalid extra forbidden term')
    hits = [w for w in FORBIDDEN+tuple(w.lower() for w in more) if w in value]
    require(not hits, 'Forbidden word at '+where+': '+','.join(hits))


def unpack(raw, max_bytes=LIMIT):
    """Bound decompression; reject links, duplicates and traversal before writing."""
    out = {}; total = 0
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:*') as archive:
        for m in archive:
            safe_name(m.name)
            require(m.isfile(), 'Nonregular archive member: '+m.name)
            require(m.name not in out, 'Duplicate archive member: '+m.name)
            total += m.size
            require(0 <= m.size <= max_bytes and total <= max_bytes,
                    'Archive expansion exceeds limit')
            data = archive.extractfile(m).read(m.size+1)
            require(len(data) == m.size, 'Truncated member: '+m.name)
            out[m.name] = data
    return out


def extract(raw, dest):
    dest = Path(dest)
    members = unpack(raw)
    dest.mkdir(mode=0o700, parents=True, exist_ok=False)
    for name, data in members.items():
        path = dest/name
        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with path.open('xb') as f:
            f.write(data)
        path.chmod(0o600)
    if (dest/'a').is_dir():
        (dest/'a').chmod(0o700)
    return members


def bundle(batch):
    lines = [l for l in batch.decode().splitlines() if l.startswith('b=bytes.fromhex(')]
    require(len(lines) == 1, 'Bundle encoding differs')
    tree = ast.parse(lines[0])
    v = tree.body[0].value
    require(isinstance(v, ast.Call) and isinstance(v.func, ast.Attribute)
            and isinstance(v.func.value, ast.Name) and v.func.value.id == 'bytes'
            and v.func.attr == 'fromhex' and len(v.args) == 1 and not v.keywords,
            'Bundle encoding differs')
    return unpack(bytes.fromhex(ast.literal_eval(v.args[0])))


def package_files(package):
    package = Path(package); files = {}
    for root, dirs, names in os.walk(str(package), followlinks=False):
        for name in dirs+names:
            require(not (Path(root)/name).is_symlink(), 'Package symlink')
        for name in names:
            p = Path(root)/name
            require(p.is_file(), 'Nonregular package file')
            require(p.stat().st_size <= LIMIT, 'Package file exceeds limit')
            files[p.relative_to(package).as_posix()] = p.read_bytes()
    require(sum(map(len, files.values())) <= 2*LIMIT, 'Package exceeds limit')
    return files


def structure(package):
    f = package_files(package)
    for n in ('0.json','CONFIG.json','PACKAGE.json','0.tgz','BATCH.sh','a/4.py','a/5.py','a/6.py'):
        require(n in f, 'Missing package member: '+n)
    public = json.loads(f['0.json']); receipt = json.loads(f['PACKAGE.json'])
    token(public['token'])
    require(f['0.json'] == f['CONFIG.json'], 'Config descriptor differs')
    require(receipt['token'] == public['token'], 'Package token differs')
    require(sha(f['0.tgz']) == public['payload_sha256']
            and len(f['0.tgz']) == public['payload_bytes'], 'Payload differs')
    for n, h in receipt['files'].items():
        safe_name(n)
        require(n in f and sha(f[n]) == h, 'Package descriptor differs: '+n)
    pay = unpack(f['0.tgz']); plan = json.loads(pay['9.json'])
    require(canonical(plan) == public['plan_sha256'], 'Plan digest differs')
    require(plan['token'] == public['token'], 'Plan token differs')
    for n, pin in plan['payload_pins'].items():
        require(n in pay and pin == dict(bytes=len(pay[n]),sha256=sha(pay[n])),
                'Payload pin differs: '+n)
    b = bundle(f['BATCH.sh'])
    require(set(b) == {'0.py','0.json','7.py'}, 'Bundle inventory differs')
    require(b['0.json'] == f['0.json'], 'Bundle descriptor differs')
    require(b['7.py'] == f['a/6.py'], 'Bundled operator differs')
    text = f['BATCH.sh'].decode()
    require(("'a'+j+%r" % public['token']) in text, 'Batch token differs')
    for n, data in list(f.items())+list(pay.items())+list(b.items()):
        # Job payloads target Python 3.12. The login interpreter validates
        # hashes too, but compiles only code that actually runs on login.
        if n.endswith('.py') and (sys.version_info >= (3,8) or n in f or n in b
                                 or n=='8.py' or n.startswith('orchard_h10/')):
            compile(data, n, 'exec')
    return f, pay, public, plan


def shell_surfaces(text, where, more=()):
    """Check shell command surfaces, excluding stdin bodies and code comments.

    Python descendants also run under the native process guard. Shell utility
    names in the sealed diagnostic trap (e.g. head) are executable syntax;
    their arguments, assignments, paths and every Slurm field are surfaces.
    """
    count = 0; heredocs = []
    for line in text.splitlines():
        if heredocs:
            if line.strip() == heredocs[0]:heredocs.pop(0)
            continue
        s=line.strip()
        if not s or (s.startswith('#') and not s.startswith('#SBATCH')):continue
        heredocs.extend(re.findall(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z_0-9]*)['\"]?",line))
        # Diagnostic strings and shell syntax are not job comments. shlex
        # retains quoted argv values, including --wrap and --export strings.
        if s.startswith('#SBATCH'):line=s[len('#SBATCH'):]
        try:
            lexer=shlex.shlex(line,posix=True,punctuation_chars=';&|()<>')
            lexer.whitespace_split=True;lexer.commenters='#';words=list(lexer)
        except ValueError:words=re.findall(r'[^\s]+',line)
        for word in words:
            if word.startswith('#SBATCH'):continue
            if word in ('head','/usr/bin/head'):continue
            # The trap's head utility is the only forbidden executable name.
            # Match paths/env/argv, not identifiers in shell control syntax.
            opaque(word,where,more);count+=1
        for m in re.finditer(r'--job-name(?:=|\s+)([^\s)]+)',line):
            name=m.group(1).strip('"\'')
            if '$' not in name:
                require(re.fullmatch(PREFIX+TOKEN,name),'Invalid job name at '+where)
    return count


def stale_identities(files, identities):
    """Identity regression scans bytes recursively; this is not a term scan."""
    total=[0]
    def scan(name,data,depth):
        require(depth<=4,'Archive nesting limit')
        total[0]+=len(data);require(total[0]<=8*LIMIT,'Identity expansion exceeds limit')
        for old in identities:
            require(old not in name and old.encode() not in data and old.encode().hex().encode() not in data,
                    'Stale identity in '+name)
        if (name.endswith(('.tgz','.tar','.tar.gz')) or data.startswith(b'\x1f\x8b')
                or data[257:262]==b'ustar'):
            for n,d in unpack(data).items():scan(name+'/'+n,d,depth+1)
        elif name.endswith('BATCH.sh'):
            for n,d in bundle(data).items():scan(name+'/bundle/'+n,d,depth+1)
    if identities:
        for n,d in files.items():scan(n,d,0)
    return total[0]


def privacy(files, payload, public, extra=(), forbidden_extra=()):
    """Names exposed on Orchard are opaque; sealed archive contents are private."""
    opaque(PREFIX+token(public['token']),'job name',forbidden_extra)
    surfaces=1
    for n,d in files.items():
        safe_name(n);opaque(n,'delivery member '+n,forbidden_extra);surfaces+=1
        if n.endswith('.sh') or n.endswith('.cmd'):
            surfaces+=shell_surfaces(d.decode(),n,forbidden_extra)
    plan=json.loads(payload['9.json']) if '9.json' in payload else {}
    for key in ('pool','logical'):
        if key in plan:opaque(plan[key],'runtime '+key,forbidden_extra);surfaces+=1
    for n in ('a/0.json','a/1.json'):
        if n not in files:continue
        inputs=json.loads(files[n])
        values=[inputs[k] for k in ('python','frames_root','sam_source') if k in inputs]
        values+=inputs.get('env_roots',[])+list(inputs.get('policy',{}).values())
        values += [p['path'] for a in inputs.get('archives',[]) for p in a['parts']]
        for value in values:opaque(value,'runtime path '+n,forbidden_extra);surfaces+=1
    if 'BATCH.sh' in files:
        text=files['BATCH.sh'].decode()
        require("r=Path('/tmp')/('a'+j+" in text and 'r.mkdir(mode=0o700)' in text,
                'Batch extraction containment differs')
        require("str(r/'0.py')" in text,'Payload path exposed in batch argv')
    return dict(surfaces_checked=surfaces,identity_bytes_checked=stale_identities(files,extra),
                policy=list(FORBIDDEN),scope='operational names; archive contents excluded')


def preserved(base, filled, prep_sha=None):
    a, b = base['archives'], filled['archives']
    require(len(b) == len(a)+1, 'Fill must append preparation archive')
    require(b[1:-1] == a[1:], 'Fill dropped or changed a base/env archive')
    require(bool(base.get('environment_receipt')) and bool(base.get('policy_receipt')),
            'Missing base environment/policy receipt')
    for key in ('environment_receipt','policy_receipt'):
        name = base[key]
        require(filled.get(key) == name and filled['files'][name] == base['files'][name],
                'Fill changed environment/policy pin')
    if prep_sha is not None:
        require(b[-1]['sha256'] == prep_sha, 'Last archive is not preparation')


def clean_env(root):
    env = {'PATH':'/usr/local/bin:/usr/bin:/bin', 'CUDA_VISIBLE_DEVICES':'',
           'OMP_NUM_THREADS':'8','MKL_NUM_THREADS':'8','OPENBLAS_NUM_THREADS':'8',
           'TOKENIZERS_PARALLELISM':'false','PYTHONDONTWRITEBYTECODE':'1',
           'HF_HUB_OFFLINE':'1','TRANSFORMERS_OFFLINE':'1', 'TZ':'UTC'}
    for n in ('XDG_CACHE_HOME','HF_HOME','TRITON_CACHE_DIR','TORCH_HOME','TMPDIR'):
        p = Path(root)/n; p.mkdir(parents=True, exist_ok=True); env[n] = str(p)
    return env


def run(argv, cwd, log, env=None, timeout=180):
    """Local computations are serial, nice, CPU-only, bounded and logged."""
    argv = ['nice','-n','10']+list(map(str,argv))
    start = time.monotonic()
    with Path(log).open('wb') as out:
        result = subprocess.run(argv, cwd=str(cwd), env=env or clean_env(cwd),
                                stdout=out, stderr=subprocess.STDOUT, timeout=timeout)
    require(result.returncode == 0, 'Command failed (%d); see %s' % (result.returncode,log))
    return dict(argv=argv,seconds_measured=time.monotonic()-start,log=str(log))


def probe(python, mode, package, workspace, spec=None):
    here = Path(__file__).resolve().parent
    workspace = Path(workspace); workspace.mkdir(parents=True, exist_ok=True)
    if mode in ('fill','login'):
        python=(spec or {}).get('login_python','/usr/bin/python3')
    args = [python,'-I','-s','-B',str(here/'pack_probes.py'),mode,
            str(package),str(workspace)]
    if spec:
        path = workspace/'spec.json'; write(path,spec); args.append(str(path))
    timeout=(spec or {}).get('fill_timeout_seconds',180) if mode=='fill' else 180
    require(type(timeout) is int and 1<=timeout<=7200,'Invalid fill timeout')
    return run(args,workspace,workspace/'probe.log',timeout=timeout)


def validate_mirrors(spec, max_read_bytes):
    total = 0
    for remote, pin in spec.items():
        require(isinstance(remote,str) and remote.startswith('/'), 'Mirror key must be absolute')
        p = Path(pin['local']).resolve()
        require(str(p).startswith('/scratch/'), 'Read mirrors must live under /scratch')
        require(p.is_file() and not p.is_symlink(), 'Missing local mirror: '+str(p))
        require(p.stat().st_size == pin['bytes'], 'Mirror size differs: '+str(p))
        total += pin['bytes']
    require(total <= max_read_bytes, 'Local mirror reads exceed configured byte budget')
    for remote, pin in spec.items():
        require(file_sha(pin['local']) == pin['sha256'], 'Mirror SHA differs: '+remote)
    return total


def local_check(config, package, workspace, audit=False):
    """Never writes a native Orchard CPU receipt or claims a staged restore."""
    workspace = Path(workspace); workspace.mkdir(parents=True,exist_ok=True)
    write(workspace/'CHECK.json',dict(passed=False,utc=utc(),state='checking'))
    attempt = workspace/('a'+os.urandom(6).hex()); attempt.mkdir()
    stages = []; errors = []
    def gate(name, fn):
        try:
            result = fn(); stages.append(dict(check=name,passed=True,result=result))
            return result
        except Exception as e:
            errors.append(dict(check=name,error=str(e)))
            if not audit:
                write(workspace/'CHECK.json',dict(passed=False,checks=stages,errors=errors,utc=utc()))
                raise
    result = gate('structure', lambda: structure(package))
    if result is None:
        write(workspace/'CHECK.json',dict(passed=False,checks=[],errors=errors,utc=utc()))
        raise GateError('Structural audit failed')
    files,pay,public,plan = result
    stages[-1]['result'] = dict(token=public['token'],payload=public['payload_sha256'])
    gate('private_containment',lambda: containment(package))
    gate('privacy', lambda: privacy(files,pay,public,config.get('old_identities',[]),
                                  config.get('forbidden_extra',[])))
    py = config.get('python',sys.executable)
    gate('native_metadata', lambda: probe(py,'metadata',package,attempt/'a0',config))
    gate('login_python36', lambda: probe(py,'login',package,attempt/'a6',config))
    gate('bundle_process_guard_dispatch', lambda: probe(py,'guard',package,attempt/'a1',config))
    gate('isolated_imports_layout_operator', lambda: probe(py,'logic',package,attempt/'a2',config))
    gate('exit_usr1', lambda: probe(py,'trap',package,attempt/'a3',config))
    gate('native_stop_slot', lambda: probe(py,'stop',package,attempt/'a5',config))
    fill = config.get('fill')
    if fill:
        mirrors = config.get('mirrors',{})
        mirrored = gate('mirror_hashes',lambda: validate_mirrors(mirrors,config.get('max_read_bytes',256*1024**2)))
        if mirrored is not None:
            gate('isolated_real_fill',lambda: probe(py,'fill',package,attempt/'a4',config))
        else:
            errors.append(dict(check='isolated_real_fill',error='Blocked by mirror_hashes; not executed'))
    else:
        gate('isolated_real_fill',lambda: require(False,'No authenticated fill inputs/mirrors configured'))
    report = dict(schema='so_pack-local-v1',passed=not errors,checks=stages,errors=errors,
                  checker_sha256=checker_fingerprint(),
                  utc=utc(),token=public['token'],package_fingerprint=fingerprint(package),
                  config_sha256=canonical(config),scope='local packaging; no allocated CPU proof')
    write(workspace/'CHECK.json', report)
    require(not errors,'Audit failed: '+', '.join(e['check'] for e in errors))
    return report


def containment(package):
    package=Path(package)
    for p in (package,package/'a'):
        require((p.stat().st_mode&0o777)==0o700,'Package directories must be 0700: '+str(p))
    for n in package_files(package):
        require(((package/n).stat().st_mode&0o777)==0o600,'Package files must be 0600: '+n)
    return dict(package_mode='0700',private_mode='0700',file_mode='0600')


def fingerprint(package):
    return canonical({n:sha(d) for n,d in package_files(package).items()})


def checker_fingerprint():
    here=Path(__file__).resolve().parent
    return {n:file_sha(here/n) for n in ('pack.py','pack_probes.py')}


def enabled(args):
    require(args.enable, 'Disabled by default; pass --enable to opt in')


def state(config):
    root = Path(config['workspace']).resolve()
    require(str(root).startswith('/scratch/'), 'Workspace must be on /scratch')
    return root


def build(config, explicit_token=None):
    root = state(config); root.mkdir(parents=True,exist_ok=True)
    require(not (root/'BUILD_STATE.json').exists(),'Build state already exists; choose a fresh workspace')
    b = config['builder']; path = Path(b['path']).resolve()
    ledger=token_ledger(config)
    if explicit_token is not None:
        unused_token(explicit_token,ledger)
    require(path.name in ('build_r8.py','build_r10.py','build_d.py'),
            'Builder must honor KROOT: use build_r8.py, build_r10.py or build_d.py')
    require(file_sha(path) == b['sha256'], 'Builder source hash differs')
    # Trusted builder args are explicit; KROOT keeps builder outputs local.
    require(set(b.get('env',{})) <= {'KROOT'},'Only KROOT may override builder environment')
    require(b.get('args') and inside(b['args'][0],root),'Builder stage must live inside workspace')
    require(inside(b['report'],root),'Builder report must live inside workspace')
    Path(b['args'][0]).mkdir(parents=True,exist_ok=True)
    env = clean_env(root); env.update(b.get('env',{}))
    require(inside(env.get('KROOT',''),root),'Set builder KROOT inside workspace')
    if explicit_token is not None:
        token(explicit_token)
        require(b.get('explicit_token_switch') is True
                and b'SO_PACK_EXPLICIT_TOKEN' in path.read_bytes(),
                'Fresh explicit-token builds require the optional builder patch and explicit_token_switch=true')
        env.update(SO_PACK_EXPLICIT_TOKEN='1',SO_PACK_TOKEN=explicit_token)
    code = ('import runpy,sys; from pathlib import Path; '
            'p=Path(sys.argv[1]); sys.path.insert(0,str(p.parent)); '
            'sys.argv=sys.argv[1:]; runpy.run_path(str(p),run_name="__main__")')
    run([config.get('python',sys.executable),'-I','-s','-B','-c',code,str(path)]+b['args'],
        root,root/'builder.log',env=env)
    report = read(b['report'])[b['key']]
    unused_token(report['token'],ledger)
    if explicit_token is not None:
        require(report['token']==explicit_token,'Builder ignored explicit token; nothing may leave Trinity')
    delivery = Path(report['delivery_dir'])/'1.tgz'
    require(inside(delivery,root),'Builder delivery escaped workspace')
    require(file_sha(delivery) == report['delivery_sha256'],'Builder delivery differs')
    p = root/(PREFIX+token(report['token']))
    extract(delivery.read_bytes(),p)
    structure(p)
    result = dict(package=str(p),delivery=str(delivery),report=report,utc=utc())
    write(root/'BUILD_STATE.json',result)
    print(json.dumps(dict(token=report['token'],package=str(p),delivery=str(delivery),
                          delivery_sha256=report['delivery_sha256']),sort_keys=True))
    return result


def token_ledger(config):
    pin=config.get('token_ledger')
    require(isinstance(pin,dict) and 'path' in pin and 'sha256' in pin,
            'Authenticated Trinity token_ledger path and sha256 required before build')
    p=Path(pin['path']).resolve()
    require(str(p).startswith('/scratch/'),'Token ledger must be a Trinity /scratch snapshot')
    require(file_sha(p)==pin['sha256'],'Token ledger SHA differs')
    raw=p.read_text()
    for line in raw.splitlines():
        if line.strip():json.loads(line)
    return raw


def unused_token(tok,ledger):
    token(tok)
    require(re.search(r'(?<![0-9a-f])'+re.escape(tok)+r'(?![0-9a-f])',ledger) is None,
            'Token already present in Trinity ledger: '+tok)


def built(config):
    return read(state(config)/'BUILD_STATE.json')


def checked(config):
    b = built(config); root = state(config)
    c = read(root/'checks/CHECK.json')
    require(c.get('schema') == 'so_pack-local-v1' and c.get('passed') is True,
            'No passing local packaging receipt')
    require(c.get('checker_sha256')==checker_fingerprint(),
            'Checker source changed; run the local check with the current tool')
    require(c['package_fingerprint'] == fingerprint(b['package']), 'Package changed after check')
    require(c['config_sha256'] == canonical(config),'Config changed after check')
    require(file_sha(b['delivery']) == b['report']['delivery_sha256'],'Delivery changed after check')
    require(unpack(Path(b['delivery']).read_bytes()) == package_files(b['package']),
            'Built package bytes differ from delivery')
    # Recheck privacy even if someone supplied a hand-written local receipt.
    f,p,pub,plan = structure(b['package']); privacy(f,p,pub,config.get('old_identities',[]),
                                                config.get('forbidden_extra',[]))
    return b


def remote_settings(config, b):
    r = config['remote']; tok = token(b['report']['token'])
    root = r.get('root',REMOTE_ROOT)
    require(root == REMOTE_ROOT,'Unregistered remote root')
    p = root+'/'+PREFIX+tok; opaque(p,'remote package path',config.get('forbidden_extra',[]))
    wall = r['walltime']
    require(re.fullmatch(r'[0-9]{2}:[0-5][0-9]:[0-5][0-9]',wall),'Invalid remote walltime')
    return r,p,tok,wall


def shell_python(code):
    return "/usr/bin/python3 -I -s -B - <<'PYCODE'\n"+code+"\nPYCODE\n"


def shell_header(config=None):
    terms=FORBIDDEN+tuple((config or {}).get('forbidden_extra',[]))
    return ('set -euo pipefail\numask 077\n'
            "trap 'r=$?; if [ \"$r\" -ne 0 ]; then printf \"phase failed: exit %s line %s\\n\" \"$r\" \"$LINENO\" >&2; fi' EXIT\n"
            +shell_python('import os\nterms='+repr(terms)+'\n'
                'for k,v in os.environ.items():\n'
                ' if any(t.lower() in (k+"="+v).lower() for t in terms):raise ValueError("Non-opaque environment: "+k)'))


def remote_place(config,b):
    r,p,tok,wall = remote_settings(config,b)
    raw = Path(b['delivery']).read_bytes()
    # Package logic stays byte-identical. Transport has its own bounded parser.
    code = '''import hashlib,io,os,tarfile
from pathlib import Path,PurePosixPath
raw=bytes.fromhex(%r)
if hashlib.sha256(raw).hexdigest()!=%r:raise ValueError('Transfer hash differs')
p=Path(%r);p.mkdir(mode=0o700)
seen=set();total=0
with tarfile.open(fileobj=io.BytesIO(raw)) as t:
 for m in t:
  q=PurePosixPath(m.name);total+=m.size
  if (q.is_absolute() or '..' in q.parts or str(q)!=m.name or not m.isfile()
      or m.name in seen or total>33554432):raise ValueError('Unsafe delivery')
  seen.add(m.name);dest=p/m.name;dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
  with dest.open('xb') as f:f.write(t.extractfile(m).read())
  dest.chmod(0o600)
(p/'a').chmod(0o700)
print('placed',p)
''' % (raw.hex(),sha(raw),p)
    return shell_header(config)+shell_python(code)


def fill_argv(config, p):
    f = config['fill']; outputs = p+'/a/'
    parts = f['parts']; require(len(parts)==4,'Require four ordered fill parts')
    argv = ['/usr/bin/python3','-I','-s','-B',outputs+'4.py','--parts']+parts
    for flag,key in (('--done','done'),('--object','object'),('--config','config'),
                     ('--receipt','receipt'),('--data-receipt','data_receipt'),
                     ('--lineage','lineage'),('--step','step')):
        argv += [flag,str(f[key])]
    for flag,name in (('--out','export.json'),('--prep-tar','6'),
                      ('--base-inputs','0.json'),('--inputs-out','1.json')):
        argv += [flag,outputs+name]
    return argv


def remote_fill(config,b):
    r,p,tok,wall = remote_settings(config,b)
    argv = fill_argv(config,p)
    for item in argv:
        opaque(item,'fill argv',config.get('forbidden_extra',[]))
    code = '''import hashlib,json
from pathlib import Path
p=Path(%r)
base=json.loads((p/'a/0.json').read_text());filled=json.loads((p/'a/1.json').read_text())
if len(filled['archives'])!=len(base['archives'])+1 or filled['archives'][1:-1]!=base['archives'][1:]:
 raise ValueError('Fill changed base archive')
if filled['archives'][-1]['sha256']!=hashlib.sha256((p/'a/6').read_bytes()).hexdigest():
 raise ValueError('Preparation archive differs')
(p/'a/1.txt').write_text('0\\n')
''' % p
    return (shell_header(config)+'P='+shlex.quote(p)+'\n'
            'test ! -e "$P/a/1.txt"\n'+ ' '.join(map(shlex.quote,argv))+'\n'
            + 'CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B '+shlex.quote(p+'/3.py')
            +' check --gpus 1 --time '+shlex.quote(wall)+'\n'+shell_python(code))


def sealed_script(config, key, package=None, walltime=None):
    pin = config['remote'][key]
    raw = Path(pin['path']).read_bytes()
    require(sha(raw) == pin['sha256'],'Remote script source hash differs: '+key)
    text=raw.decode()
    # Explicit opt-in adapter for reviewed fixed-token A/B operational scripts.
    # The default returns the exact input bytes. Native gate bodies stay intact.
    if pin.get('parameterize',False):
        require(pin['parameterize'] is True and package and walltime,
                'Invalid parameterized script request')
        matches=list(re.finditer(r'^P=('+re.escape(REMOTE_ROOT)+'/'+PREFIX+'('+TOKEN+r'))$',text,re.M))
        require(len(matches)==1,'Expected one fixed package assignment in '+key)
        old=matches[0].group(1)
        oldtok=matches[0].group(2)
        text=text.replace(old,package)
        newtok=package.rsplit(PREFIX,1)[1]
        text=text.replace(PREFIX+oldtok,PREFIX+newtok)
        text=text.replace('P='+package+'\n',
            'test "${P:?}" = '+shlex.quote(package)+'\n'
            +'test "${T:?}" = '+shlex.quote(walltime)+'\n',1)
        text,n=re.subn(r'--time [0-9]{2}:[0-5][0-9]:[0-5][0-9]',
                       '--time "$T"',text)
        require(n>=1,'No public walltime argument to parameterize in '+key)
        require(oldtok==newtok or oldtok not in text,'Old token remains in adapted '+key)
    return text


def remote_submit(config,b,phase='gpu'):
    r,p,tok,wall = remote_settings(config,b)
    cpu = sealed_script(config,'cpu_script',p,wall)
    sub = sealed_script(config,'submit_script',p,wall)
    shell_surfaces(cpu,'sealed CPU commands',config.get('forbidden_extra',[]))
    shell_surfaces(sub,'sealed submit commands',config.get('forbidden_extra',[]))
    require(not re.search(r'^P=',cpu,re.M) and not re.search(r'^P=',sub,re.M),
            'Use parameterized D-style CPU/submit scripts; fixed-token scripts are refused')
    require('CPU.json' in sub and 'squeue' in sub and '3.py submit' in sub,
            'Submit script is missing native gates')
    wait=r.get('cpu_wait_seconds',14400)
    require(type(wait) is int and 1<=wait<=14400,'Invalid CPU wait bound')
    prefix=(shell_header(config)+'export P='+shlex.quote(p)+' T='+shlex.quote(wall)+'\n'
            'test "${P##*a15_cot_ap}" = '+shlex.quote(tok)+'\n')
    if phase=='cpu':
        return prefix+"bash -s <<'CPU_CODE'\n"+cpu+"\nCPU_CODE\n"
    status=(
        'J=$(cat "$P/a/4.txt"); [[ "$J" =~ ^[0-9]+$ ]]\n'
        'if ! V=$(sacct -n -X -j "$J" --format=State 2>"$P/a/0.err"); then\n'
        '  cat "$P/a/0.err" >&2; echo PACK_CPU_RETRY; exit 0\nfi\n'
        "S=$(printf '%s\\n' \"$V\" | awk 'NF{print $1;exit}'); S=${S%%+*}\n"
        'case "$S" in\n'
        ' COMPLETED) test -s "$P/a/c/CPU.json"; echo PACK_CPU_READY;;\n'
        ' PENDING|RUNNING|CONFIGURING|COMPLETING) echo "PACK_CPU_WAIT $J $S"; exit 0;;\n'
        ' "") echo "CPU accounting has no state for $J" >&2; echo PACK_CPU_RETRY; exit 0;;\n'
        ' *) echo "CPU job $J state $S" >&2; tail -n 60 "$P/a/4.err" >&2 || true; exit 1;;\nesac\n')
    if phase=='poll':return prefix+status
    require(phase=='gpu','Unknown submit phase')
    # Recheck readiness in the same bounded call that submits the GPU job.
    status=status.replace('echo PACK_CPU_RETRY; exit 0','exit 1')
    status=status.replace('echo "PACK_CPU_WAIT $J $S"; exit 0','echo "CPU not ready: $S" >&2; exit 1')
    return prefix+status+"bash -s <<'SUB_CODE'\n"+sub+"\nSUB_CODE\n"


def transport_command(config):
    r=config['remote'];seconds=r.get('timeout_seconds',300)
    require(type(seconds) is int and 1<=seconds<=300,'Remote timeout must be 1..300 seconds')
    return ['timeout',str(seconds),'bash',r['ossh'],
            'env -i PATH=/usr/local/bin:/usr/bin:/bin HOME="$HOME" USER="$USER" bash -s']


def remote_call(action,config,script,expected_sha):
    """One throttled, bounded call. A failed transport is never retried."""
    require(file_sha(script)==expected_sha,'Planned remote script changed')
    command=transport_command(config);root=state(config)
    with (root/(action+'_remote.log')).open('wb') as out:
        pump=subprocess.Popen(['pv','-q','-L','8000000',str(script)],stdout=subprocess.PIPE,stderr=out)
        try:
            remote=subprocess.Popen(command,stdin=pump.stdout,stdout=out,stderr=subprocess.STDOUT)
        except BaseException:
            pump.stdout.close();pump.wait();raise
        pump.stdout.close()
        rc=remote.wait();transfer_rc=pump.wait()
    require(rc==0 and transfer_rc==0,
            'Remote '+action+' failed (transport %d, stream %d); stop, inspect log, do not retry'%(rc,transfer_rc))
    return (root/(action+'_remote.log')).read_text()


def run_remote(action,config,args,script,expected_sha):
    """Use only planned bytes; submit polls locally between short calls."""
    b=checked(config);r,p,tok,wall=remote_settings(config,b)
    require(args.yes and args.token==tok,
            'Remote execution requires --yes and the exact explicit --token')
    require(file_sha(script)==expected_sha,'Planned remote script changed')
    require(shutil.which('pv') is not None,'pv is required for the 8 MB/s transport limit')
    manifest=None
    if action=='submit':
        manifest=read(script)
        for phase in ('cpu','poll','gpu'):
            pin=manifest[phase]
            require(file_sha(pin['path'])==pin['sha256'],'Planned submit script changed')
    root=state(config);marker=root/(action+'_ATTEMPT.json')
    require(not marker.exists(),'Remote action already attempted; inspect its log; no retry')
    write(marker,dict(utc=utc(),token=tok,script_sha256=expected_sha))
    if action!='submit':return remote_call(action,config,script,expected_sha)
    pin=manifest['cpu'];remote_call('submit_cpu',config,pin['path'],pin['sha256'])
    start=time.monotonic();errors=0;index=0
    while time.monotonic()-start<r.get('cpu_wait_seconds',14400):
        time.sleep(60);index+=1
        pin=manifest['poll']
        output=remote_call('submit_poll_%04d'%index,config,pin['path'],pin['sha256'])
        lines=output.splitlines()
        if 'PACK_CPU_READY' in lines:break
        retry='PACK_CPU_RETRY' in lines
        require(retry or any(l.startswith('PACK_CPU_WAIT ') for l in lines),'Unrecognized CPU poll reply')
        errors=errors+1 if retry else 0
        require(errors<3,'Three consecutive sacct errors; stop and inspect poll logs')
    else:raise GateError('CPU wait expired; inspect submit_poll logs')
    # The final submit call rechecks sacct. Keep it a minute after the poll too.
    time.sleep(60)
    pin=manifest['gpu'];return remote_call('submit_gpu',config,pin['path'],pin['sha256'])


def python_stdin_sources(text):
    sources=[];active=None;body=[]
    for line in text.splitlines():
        if active:
            if line.strip()==active:
                sources.append('\n'.join(body)+'\n');active=None;body=[]
            else:body.append(line)
        elif '/usr/bin/python3' in line and '<<' in line:
            match=re.search(r"<<['\"]?([A-Za-z_][A-Za-z_0-9]*)",line)
            require(match is not None,'Unrecognized Python heredoc');active=match.group(1)
    require(active is None,'Unterminated Python stdin body')
    return sources


def validate_login_sources(text,config,root,label):
    """Real Python 3.6 compiles every Python stdin body before transport."""
    sources=python_stdin_sources(text)
    path=Path(root)/(label+'_python.json');write(path,sources)
    code='import json,sys;[compile(s,"stdin","exec") for s in json.load(open(sys.argv[1]))];print("LOGIN_COMPILE_PASS",sys.version)'
    run([config.get('login_python','/usr/bin/python3'),'-I','-s','-B','-c',code,str(path)],
        root,Path(root)/(label+'_python.log'))


def stage_remote(action,config,args,plan_only=False):
    b = checked(config); r,p,tok,wall = remote_settings(config,b)
    if action == 'submit' or args.execute_remote:
        require(args.yes and args.token == tok,
                'submit/remote execution requires --yes and the exact explicit --token')
    if args.execute_remote:
        require(shutil.which('pv') is not None,'pv is required for the 8 MB/s transport limit')
    root=state(config);command=transport_command(config)
    phases=('cpu','poll','gpu') if action=='submit' else (action,)
    plans={}
    for phase in phases:
        if action=='submit':text=remote_submit(config,b,phase)
        else:text={'place':remote_place,'fill':remote_fill}[action](config,b)
        shell_surfaces(text,'outbound '+phase,config.get('forbidden_extra',[]))
        script=root/(tok+'_'+phase+'.sh');script.write_text(text);script.chmod(0o600)
        run(['bash','-n',str(script)],root,root/(phase+'_syntax.log'))
        validate_login_sources(text,config,root,phase)
        plans[phase]=dict(path=str(script),sha256=file_sha(script))
        stream=['pv','-q','-L','8000000',str(script)]
        print('set -o pipefail; '+' '.join(map(shlex.quote,stream))+' | '+' '.join(map(shlex.quote,command)))
    if action=='submit':
        script=root/(tok+'_submit.json');write(script,plans)
    if args.execute_remote and not plan_only:
        run_remote(action,config,args,script,file_sha(script))
    return script


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('build','check','place','fill','submit','all'))
    p.add_argument('--config',required=True)
    p.add_argument('--enable',action='store_true',help='Opt in; default executes nothing')
    p.add_argument('--yes',action='store_true')
    p.add_argument('--token',help='Explicit package token for production submission')
    p.add_argument('--execute-remote',action='store_true',help='Use ossh once per stage; otherwise print commands')
    p.add_argument('--audit',action='store_true',help='Collect local failures; never grants release')
    p.add_argument('--reuse-build',action='store_true',help='Validate existing build instead of minting another token')
    a = p.parse_args(argv)
    os.umask(0o077)
    print('UTC '+utc(),file=sys.stderr)
    enabled(a); limit_resources(); c = read(a.config)
    require(not a.audit or a.action == 'check','--audit is only for check')
    require(not a.reuse_build or a.action in ('build','all'),'--reuse-build only applies to build/all')
    if a.action in ('build','all'):
        if a.reuse_build:
            b = built(c)
            if a.token is not None:
                require(a.token==b['report']['token'],'Explicit token differs from existing build')
            require(file_sha(b['delivery']) == b['report']['delivery_sha256'],'Existing delivery differs')
            require(unpack(Path(b['delivery']).read_bytes()) == package_files(b['package']),
                    'Existing build differs from delivery')
            structure(b['package'])
        else:
            if a.token is None:
                build(c)
            else:
                build(c,explicit_token=a.token)
    if a.action in ('check','all'):
        b = built(c)
        local_check(c,b['package'],state(c)/'checks',audit=a.audit)
        print('LOCAL_PACKAGING_PASS (allocated CPU proof still required)')
    if a.action=='all':
        plans=[]
        for action in ('place','fill','submit'):
            script=stage_remote(action,c,a,plan_only=True)
            plans.append((action,script,file_sha(script)))
        # Every package and operational-script check has passed before any
        # remote process starts. Execution uses the exact planned bytes.
        if a.execute_remote:
            for action,script,digest in plans:
                run_remote(action,c,a,script,digest)
    elif a.action in ('place','fill','submit'):
        stage_remote(a.action,c,a)


if __name__ == '__main__':
    try:
        main()
    except (GateError,ValueError,KeyError,OSError,subprocess.SubprocessError) as e:
        print('PACK_FAIL: '+str(e),file=sys.stderr)
        sys.exit(2)
