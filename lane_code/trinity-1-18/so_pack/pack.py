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
    return datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


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
        if n.endswith('.py'):
            compile(data, n, 'exec')
    return f, pay, public, plan


def privacy(files, payload, public, extra=(), forbidden_extra=()):
    """Scan every name and every textual byte, including comments and env literals.

    Native lists are a minimum policy: an artifact cannot weaken this list.
    Nested archives and embedded bundles are scanned after decoding.
    """
    seen = [0]
    def scan(name, data, depth):
        require(depth <= 4, 'Archive nesting limit')
        opaque(name, 'file/path '+name,forbidden_extra)
        seen[0] += len(data)
        require(seen[0] <= 8*LIMIT, 'Privacy expansion exceeds limit')
        if name.endswith(('.tgz','.tar','.tar.gz')):
            for n,d in unpack(data).items():
                scan(name+'/'+n,d,depth+1)
            return
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            # Binary strings can also contain identifiers; scan printable runs.
            text = '\n'.join(x.decode('ascii') for x in re.findall(rb'[ -~]{4,}',data))
        opaque(text, 'contents/comments/env '+name,forbidden_extra)
        for old in extra:
            require(old.encode() not in data and old.encode().hex().encode() not in data,
                    'Stale identity in '+name)
        if name.endswith('BATCH.sh'):
            for n,d in bundle(data).items():
                scan(name+'/bundle/'+n,d,depth+1)
    opaque(PREFIX+token(public['token']), 'job name',forbidden_extra)
    for n,d in files.items():
        scan(n,d,0)
    return dict(scanned_bytes=seen[0], policy=list(FORBIDDEN))


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
    args = [python,'-I','-s','-B',str(here/'pack_probes.py'),mode,
            str(package),str(workspace)]
    if spec:
        path = workspace/'spec.json'; write(path,spec); args.append(str(path))
    return run(args,workspace,workspace/'probe.log',timeout=180)


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
    gate('privacy', lambda: privacy(files,pay,public,config.get('old_identities',[]),
                                  config.get('forbidden_extra',[])))
    py = config.get('python',sys.executable)
    gate('native_metadata', lambda: probe(py,'metadata',package,attempt/'a0',config))
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
                  utc=utc(),token=public['token'],package_fingerprint=fingerprint(package),
                  config_sha256=canonical(config),scope='local packaging; no allocated CPU proof')
    write(workspace/'CHECK.json', report)
    require(not errors,'Audit failed: '+', '.join(e['check'] for e in errors))
    return report


def fingerprint(package):
    return canonical({n:sha(d) for n,d in package_files(package).items()})


def enabled(args):
    require(args.enable, 'Disabled by default; pass --enable to opt in')


def state(config):
    root = Path(config['workspace']).resolve()
    require(str(root).startswith('/scratch/'), 'Workspace must be on /scratch')
    return root


def build(config):
    root = state(config); root.mkdir(parents=True,exist_ok=True)
    require(not (root/'BUILD_STATE.json').exists(),'Build state already exists; choose a fresh workspace')
    b = config['builder']; path = Path(b['path']).resolve()
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
    code = ('import runpy,sys; from pathlib import Path; '
            'p=Path(sys.argv[1]); sys.path.insert(0,str(p.parent)); '
            'sys.argv=sys.argv[1:]; runpy.run_path(str(p),run_name="__main__")')
    run([config.get('python',sys.executable),'-I','-s','-B','-c',code,str(path)]+b['args'],
        root,root/'builder.log',env=env)
    report = read(b['report'])[b['key']]
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


def built(config):
    return read(state(config)/'BUILD_STATE.json')


def checked(config):
    b = built(config); root = state(config)
    c = read(root/'checks/CHECK.json')
    require(c.get('schema') == 'so_pack-local-v1' and c.get('passed') is True,
            'No passing local packaging receipt')
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
    p = root+'/'+PREFIX+tok; opaque(p,'remote package path')
    wall = r['walltime']
    require(re.fullmatch(r'[0-9]{2}:[0-5][0-9]:[0-5][0-9]',wall),'Invalid remote walltime')
    return r,p,tok,wall


def shell_python(code):
    return "/usr/bin/python3 -I -s -B - <<'PYCODE'\n"+code+"\nPYCODE\n"


def shell_header():
    return ('set -euo pipefail\numask 077\n'
            "trap 'r=$?; if [ \"$r\" -ne 0 ]; then printf \"phase failed: exit %s line %s\\n\" \"$r\" \"$LINENO\" >&2; fi' EXIT\n")


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
  dest.chmod(m.mode & 0o700)
(p/'a').chmod(0o700)
print('placed',p)
''' % (raw.hex(),sha(raw),p)
    return shell_header()+shell_python(code)


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
        opaque(item,'fill argv')
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
    return (shell_header()+'P='+shlex.quote(p)+'\n'
            'test ! -e "$P/a/1.txt"\n'+ ' '.join(map(shlex.quote,argv))+'\n'
            + 'CUDA_VISIBLE_DEVICES= /usr/bin/python3 -I -s -B '+shlex.quote(p+'/3.py')
            +' check --gpus 1 --time '+shlex.quote(wall)+'\n'+shell_python(code))


def sealed_script(config, key):
    pin = config['remote'][key]
    raw = Path(pin['path']).read_bytes()
    require(sha(raw) == pin['sha256'],'Remote script source hash differs: '+key)
    return raw.decode()


def remote_submit(config,b):
    r,p,tok,wall = remote_settings(config,b)
    # Keep all native receipt, pool and queue guards. The CPU script may end in
    # diagnostic commands, so it is run as a separate shell with its own failure.
    cpu = sealed_script(config,'cpu_script'); sub = sealed_script(config,'submit_script')
    require(not re.search(r'^P=',cpu,re.M) and not re.search(r'^P=',sub,re.M),
            'Use parameterized D-style CPU/submit scripts; fixed-token scripts are refused')
    require('CPU.json' in sub and 'squeue' in sub and '3.py submit' in sub,
            'Submit script is missing native gates')
    require(r.get('cpu_wait_seconds',14400) <= 14400, 'CPU wait exceeds four hours')
    # CPU checking itself never grants permission to submit another token.
    receipt = p+'/a/c/CPU.json'
    return (shell_header()+'export P='+shlex.quote(p)+' T='+shlex.quote(wall)+'\n'
            'test "${P##*a15_cot_ap}" = '+shlex.quote(tok)+'\n'
            "bash -s <<'CPU_CODE'\n"+cpu+"\nCPU_CODE\n"
            'J=$(cat "$P/a/4.txt"); [[ "$J" =~ ^[0-9]+$ ]]\n'
            'start=$SECONDS\nwhile true; do\n'
            '  S=$(sacct -n -X -j "$J" --format=State | awk \'NF{print $1;exit}\')\n'
            '  case "$S" in COMPLETED) break;; FAILED*|CANCELLED*|TIMEOUT*|OUT_OF_MEMORY*|NODE_FAIL*|PREEMPTED*) cat "$P/a/4.err" >&2; exit 1;; esac\n'
            '  test $((SECONDS-start)) -lt '+str(r.get('cpu_wait_seconds',14400))+'\n'
            '  sleep 60\ndone\n'
            'test -s '+shlex.quote(receipt)+'\n'
            "bash -s <<'SUB_CODE'\n"+sub+"\nSUB_CODE\n")


def stage_remote(action,config,args):
    b = checked(config); r,p,tok,wall = remote_settings(config,b)
    if action == 'submit' or args.execute_remote:
        require(args.yes and args.token == tok,
                'submit/remote execution requires --yes and the exact explicit --token')
    fn = {'place':remote_place,'fill':remote_fill,'submit':remote_submit}[action]
    text = fn(config,b)
    # Native operational scripts are outbound bytes too. Their comments and
    # literals receive the same strict policy as package content.
    opaque(text,'outbound '+action+' script/comments/env',config.get('forbidden_extra',[]))
    root = state(config); script = root/(tok+'_'+action+'.sh')
    script.write_text(text); script.chmod(0o600)
    # ossh accepts one remote shell command and forwards stdin, as used by lane.
    transport = r['ossh']
    command = ['bash',transport,'bash -s']
    print(' '.join(map(shlex.quote,command))+' < '+shlex.quote(str(script)))
    run(['bash','-n',str(script)],root,root/(action+'_syntax.log'))
    if args.execute_remote:
        marker = root/(action+'_ATTEMPT.json')
        require(not marker.exists(),'Remote action already attempted; inspect its log; no retry')
        write(marker,dict(utc=utc(),token=tok,script_sha256=sha(text.encode())))
        with script.open('rb') as inp, (root/(action+'_remote.log')).open('wb') as out:
            result = subprocess.run(command,stdin=inp,stdout=out,stderr=subprocess.STDOUT)
        require(result.returncode == 0,'Remote '+action+' failed; stop, inspect log, do not retry')
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
    print('UTC '+utc(),file=sys.stderr)
    enabled(a); limit_resources(); c = read(a.config)
    require(not a.audit or a.action == 'check','--audit is only for check')
    require(not a.reuse_build or a.action in ('build','all'),'--reuse-build only applies to build/all')
    if a.action in ('build','all'):
        if a.reuse_build:
            b = built(c)
            require(file_sha(b['delivery']) == b['report']['delivery_sha256'],'Existing delivery differs')
            require(unpack(Path(b['delivery']).read_bytes()) == package_files(b['package']),
                    'Existing build differs from delivery')
            structure(b['package'])
        else:
            build(c)
    if a.action in ('check','all'):
        b = built(c)
        local_check(c,b['package'],state(c)/'checks',audit=a.audit)
        print('LOCAL_PACKAGING_PASS (allocated CPU proof still required)')
    for action in ('place','fill','submit'):
        if a.action in (action,'all'):
            stage_remote(action,c,a)


if __name__ == '__main__':
    try:
        main()
    except (GateError,ValueError,KeyError,OSError,subprocess.SubprocessError) as e:
        print('PACK_FAIL: '+str(e),file=sys.stderr)
        sys.exit(2)
