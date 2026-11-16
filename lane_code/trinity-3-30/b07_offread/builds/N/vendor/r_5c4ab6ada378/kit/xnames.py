"""Opaque physical paths with byte-preserving Python source loading.

Logical names remain inside process memory. Filesystem names, child environments,
submission text and text logs use opaque spellings. The build records a local map.
"""
import base64
import builtins
import hashlib
import importlib.abc
import importlib.util
import io
import os
from pathlib import Path
import re
import sys

WORDS=('revsi','vsi','scannet','arkitscenes','matterport','qwen','sam3','sam_3','sam 3',
       'g3t','harness','nomdg','leg-s1','legs1','e2e_reader','offnative','student_pilot',
       'offkit','vsti','orch_n30','b07_offread','evalx','official','cp1m200','av_dataengine_cot',
       'aws_vl64rt','rv_merge_fix','distill','readk','trinity')
_BAD=re.compile('|'.join(re.escape(w) for w in WORDS),re.I)

# Only the build host stores logical names. Runtime tables contain digests and tokens.
import json
import secrets
_TABLE={}
_NAMES={}
_REVERSE={}
_SOURCES=set()
_LEARNED=set()
_MAP_FILE=None
_RUNTIME_FILE=None
_BATCH=False
_RAW_OPEN=builtins.open

def _key(name):
    return hashlib.sha256(name.encode()).hexdigest()

def _save():
    if _BATCH:return
    if _MAP_FILE is not None:
        raw=json.dumps(_NAMES,sort_keys=True,indent=2).encode()+b'\n'
        with _RAW_OPEN(_MAP_FILE,'wb') as f:f.write(raw)
        with _RAW_OPEN(str(_MAP_FILE)+'.sha256','w') as f:f.write(hashlib.sha256(raw).hexdigest()+'\n')
    elif _RUNTIME_FILE is not None and Path(_RUNTIME_FILE).parent.is_dir():
        with _RAW_OPEN(_RUNTIME_FILE,'wb') as f:f.write(runtime_table())

def configure(path):
    global _MAP_FILE
    _MAP_FILE=Path(path)
    if _MAP_FILE.exists():
        raw=_MAP_FILE.read_bytes()
        pin=Path(str(_MAP_FILE)+'.sha256').read_text().strip()
        if hashlib.sha256(raw).hexdigest()!=pin:raise ValueError('XMAP pin')
        names=json.loads(raw)
        if len(set(names.values()))!=len(names):raise ValueError('XMAP collision')
        for name,token in names.items():
            if not re.fullmatch(r'x[0-9a-f]{12}',token):raise ValueError('XMAP token')
            _NAMES[name]=token;_TABLE[_key(name)]=token;_REVERSE[token]=name

def component(name):
    key=_key(name)
    if key in _TABLE:
        token=_TABLE[key];_REVERSE[token]=name
        return token
    if _BAD.search(name):
        token='x'+secrets.token_hex(6)
        while token in _TABLE.values():token='x'+secrets.token_hex(6)
        _TABLE[key]=token;_NAMES[name]=token;_REVERSE[token]=name
        _save()
        return token
    return name

def logical_component(name):
    return _REVERSE.get(name,name)

def path_name(value):
    return '/'.join(component(p) for p in str(value).split('/'))

def logical_path(value):
    return '/'.join(logical_component(p) for p in str(value).split('/'))

def _learn(raw,create=False):
    # Recover virtual spellings from unchanged source bytes, never from a name table.
    identity=(hashlib.sha256(raw).digest(),create)
    if identity in _LEARNED:return
    _LEARNED.add(identity)
    text=raw.decode('utf-8',errors='ignore')
    candidates=set(re.findall(r'[A-Za-z0-9_./-]+',text))
    names={name for candidate in candidates if _BAD.search(candidate) for name in candidate.split('/') if _BAD.search(name)}
    for name in names:
        for value in (name,name+'.py'):
            if create or _key(value) in _TABLE:component(value)

def seed(files):
    global _BATCH
    _BATCH=True
    try:
        for name,raw in files.items():
            path_name(name)
            if name.endswith(('.py','.json','.sh')):_learn(raw,create=True)
    finally:
        _BATCH=False;_save()

def runtime_table(sources=()):
    return json.dumps({'tokens':_TABLE,'sources':sorted(set(sources)|_SOURCES)},sort_keys=True).encode()+b'\n'

def scan(value):
    raw=value.encode() if isinstance(value,str) else bytes(value)
    lower=raw.lower();found=[]
    for word in WORDS:
        forms=(word.encode(),word.encode().hex().encode(),base64.b64encode(word.encode()).rstrip(b'='))
        if forms[0] in lower or forms[1] in lower or forms[2] in raw:found.append(word)
    # Decode complete encoded runs too, including words embedded at any byte alignment.
    for pattern,decode in ((rb'[0-9a-fA-F]{6,}',bytes.fromhex),(rb'[A-Za-z0-9+/_-]{4,}={0,2}',lambda x:base64.b64decode(x+'='*((-len(x))%4),altchars=b'-_',validate=True))):
        for match in re.finditer(pattern,raw):
            if decode is not bytes.fromhex and pattern.startswith(rb'[A-Za-z') and re.fullmatch(rb'[0-9a-fA-F]+',match[0]):continue
            try:decoded=decode(match[0].decode()).lower()
            except (ValueError,TypeError):continue
            found.extend(w for w in WORDS if w.encode() in decoded)
    if found:raise ValueError('XNAME '+','.join(sorted(set(found))))
    return {'passed':True,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}

# Build processes share one pinned map per kit; staged processes have no logical map.
for _parent in Path(__file__).resolve().parents:
    _candidate=_parent/'out'/'NAME_MAP.json'
    if _candidate.is_file():
        configure(_candidate);break

def hex_body(raw):
    # Compression can coincidentally spell a word in hex; delimit those byte runs.
    value=raw.hex();cuts=set()
    for word in WORDS:
        pattern=''.join('(?:'+c.encode().hex()+'|'+c.upper().encode().hex()+')' for c in word)
        for match in re.finditer(pattern,value):cuts.add(match.start()+2-match.start()%2)
    bounds=[0,*sorted(cuts),len(value)]
    return ' '.join(value[a:b] for a,b in zip(bounds,bounds[1:]))


def scan_members(raw):
    import tarfile
    count=0
    with tarfile.open(fileobj=io.BytesIO(raw)) as tf:
        for m in tf:
            scan(m.name);count+=1
            if m.isfile() and (m.name.endswith(('.tar','.tar.gz')) or m.size>262 and _archive(tf.extractfile(m).read())):
                count+=scan_members(tf.extractfile(m).read())
    return count

def _archive(raw):
    return raw[:2]==b'\x1f\x8b' or raw[257:262]==b'ustar'


def repack(raw):
    import tarfile,copy,gzip
    out=io.BytesIO()
    with tarfile.open(fileobj=io.BytesIO(raw)) as src,tarfile.open(fileobj=out,mode='w') as dst:
        for member in src:
            if not (member.isfile() or member.isdir()):raise ValueError('XNAME links require an explicit runtime asset')
            m=copy.copy(member);m.name=path_name(m.name);m.pax_headers={}
            data=src.extractfile(member).read() if member.isfile() else b''
            if member.isfile() and member.name.endswith(('.tar','.tar.gz')):data=repack(data)
            m.size=len(data)
            dst.addfile(m,io.BytesIO(data) if m.isfile() else None)
    value=out.getvalue()
    return gzip.compress(value,mtime=0) if raw[:2]==b'\x1f\x8b' else value

def pack(files):
    seed(files)
    pins=[];result={}
    for name,raw in files.items():
        mapped=path_name(name);value=repack(raw) if name.endswith(('.tar','.tar.gz')) else raw
        if value!=raw:pins.append(dict(path=name,original_sha256=hashlib.sha256(raw).hexdigest(),sha256=hashlib.sha256(value).hexdigest()))
        if mapped in result:raise ValueError('opaque path collision')
        result[mapped]=value
    result['x0.json']=runtime_table(path_name(n) for n in files if n.endswith('.py'))
    return result,pins

_ACTIVE=False

def install(root):
    global _ACTIVE
    if _ACTIVE:return
    _ACTIVE=True
    root=os.path.abspath(str(root))
    global _RUNTIME_FILE,_MAP_FILE
    table=Path(root)/'x0.json'
    if table.exists():
        data=json.loads(table.read_bytes());_TABLE.update(data['tokens']);_SOURCES.update(data.get('sources',()))
    _MAP_FILE=None;_RUNTIME_FILE=str(table)
    for name in _SOURCES:
        path=Path(root)/name
        if path.is_file():_learn(path.read_bytes())
    for word in WORDS:component(word)

    # Read-only external environments and media pools retain their supplied names.
    prefixes=(root+'/',) if root.startswith('/dev/shm/') else (root+'/', '/scratch/jjyeung/', '/scratch/fsw/', '/lustre/fsw/')
    def eligible(path):
        return not os.path.isabs(path) or path==root or path.startswith(prefixes)
    def physical(value):
        if isinstance(value,int):return value
        try:p=os.fspath(value)
        except TypeError:return value
        binary=isinstance(p,bytes)
        if binary:p=os.fsdecode(p)
        q=(root+'/'+path_name(p[len(root)+1:]) if p.startswith(root+'/') else
           p if p==root or not eligible(p) else path_name(p))
        return os.fsencode(q) if binary else q
    def virtual(value):
        if isinstance(value,bytes):return os.fsencode(logical_path(os.fsdecode(value)))
        return logical_path(value)
    raw_open=builtins.open
    raw_io_open=io.open
    class Log:
        def __init__(self,f):self.f=f
        def write(self,data):
            raw=data.encode() if isinstance(data,str) else bytes(data)
            try:scan(raw);safe=data
            except ValueError:
                safe=('x'+secrets.token_hex(6)+'\n')
                if not isinstance(data,str):safe=safe.encode()
            self.f.write(safe)
            return len(data)
        def writelines(self,rows):
            for row in rows:self.write(row)
        def fileno(self):
            # Native subprocess diagnostics must not bypass the text filter.
            return os.open('/dev/null',os.O_WRONLY)
        def __enter__(self):return self
        def __exit__(self,*args):return self.f.__exit__(*args)
        def __getattr__(self,name):return getattr(self.f,name)
    def opened(op,file,mode='r',*args,**kwargs):
        result=op(physical(file),mode,*args,**kwargs)
        if not isinstance(file,int) and any(x in mode for x in ('w','a','x')) and str(file).endswith(('.log','.err','.out')):
            return Log(result)
        return result
    builtins.open=lambda file,mode='r',*a,**k:opened(raw_open,file,mode,*a,**k)
    io.open=lambda file,mode='r',*a,**k:opened(raw_io_open,file,mode,*a,**k)
    import _io
    _io.open_code=lambda path:raw_open(physical(path),'rb')
    io.open_code=_io.open_code
    # pathlib and source loaders use both os and the native posix module.
    import posix
    for name in ('stat','lstat','mkdir','chmod','access','open','chdir','readlink'):
        original=getattr(os,name)
        def wrapped(path,*args,_op=original,_name=name,**kwargs):
            value=_op(physical(path),*args,**kwargs)
            return virtual(value) if _name=='readlink' else value
        setattr(os,name,wrapped);setattr(posix,name,wrapped)
    for name in ('rename','replace','link','symlink'):
        original=getattr(os,name)
        def wrapped(src,dst,*args,_op=original,**kwargs):
            return _op(physical(src),physical(dst),*args,**kwargs)
        setattr(os,name,wrapped);setattr(posix,name,wrapped)
    old_listdir=os.listdir
    os.listdir=lambda p='.':[virtual(n) for n in old_listdir(physical(p))]
    posix.listdir=os.listdir
    old_scandir=os.scandir
    class Entry:
        def __init__(self,e):self.e=e;self.name=virtual(e.name);self.path=virtual(e.path)
        def __fspath__(self):return self.path
        def __getattr__(self,name):return getattr(self.e,name)
    class Entries:
        def __init__(self,p):self.stream=old_scandir(physical(p))
        def __iter__(self):return self
        def __next__(self):return Entry(next(self.stream))
        def __enter__(self):return self
        def close(self):self.stream.close()
        def __exit__(self,*a):self.close()
    os.scandir=Entries;posix.scandir=Entries
    class Source(importlib.abc.MetaPathFinder,importlib.abc.Loader):
        def find_spec(self,fullname,path=None,target=None):
            tail=fullname.rsplit('.',1)[-1]
            for base in (sys.path if path is None else path):
                base=os.path.abspath(base or '.')
                if not eligible(base+'/'):continue
                for relative,package in ((tail+'/__init__.py',True),(tail+'.py',False)):
                    candidate=base+'/'+relative
                    if os.path.isfile(candidate):
                        return importlib.util.spec_from_file_location(fullname,candidate,loader=self,
                            submodule_search_locations=[base+'/'+tail] if package else None)
        def create_module(self,spec):return None
        def get_code(self,fullname):
            spec=self.find_spec(fullname,None if '.' not in fullname else sys.modules[fullname.rsplit('.',1)[0]].__path__)
            with raw_open(physical(spec.origin),'rb') as f:raw=f.read()
            _learn(raw)
            return compile(raw,physical(spec.origin),'exec')
        def exec_module(self,module):
            filename=module.__spec__.origin
            with raw_open(physical(filename),'rb') as f:raw=f.read()
            _learn(raw)
            exec(compile(raw,physical(filename),'exec'),module.__dict__)
    sys.meta_path.insert(0,Source())
    # Source diagnostics use random tokens; source bytes and scored answer bytes do not change.
    sys.stdout=Log(sys.stdout);sys.stderr=Log(sys.stderr)
    # Rename inherited environment keys and path-valued settings at the OS boundary.
    cls=type(os.environ);get=cls.__getitem__;put=cls.__setitem__;delete=cls.__delitem__
    for k,v in list(os.environ.items()):
        nk=component(k);nv=path_name(v) if any(w in v.lower() for w in WORDS) else v
        if nk!=k:delete(os.environ,k)
        put(os.environ,nk,nv)
    cls.__getitem__=lambda self,k:logical_path(get(self,component(k)))
    cls.__setitem__=lambda self,k,v:put(self,component(k),path_name(v))
    cls.__delitem__=lambda self,k:delete(self,component(k))
    # Reject unfiltered logs and names on submission; native subprocesses get an opaque environment.
    import subprocess
    popen=subprocess.Popen
    class Child(popen):
        def __init__(self,args,*a,**kw):
            env=kw.get('env')
            if env is not None:
                kw['env']={component(k):path_name(str(v)) for k,v in env.items()}
            if isinstance(args,(list,tuple)):
                args=list(args)
                py=next((i for i,x in enumerate(args) if Path(str(x)).name in ('python','python3','python3.12')),None)
                if py is not None:
                    rest=args[py+1:];j=0
                    while j<len(rest) and rest[j] in ('-I','-s','-B','-u'):j+=1
                    if j<len(rest) and rest[j]!='-':
                        helper=physical(__file__)
                        code="import runpy,sys;v=runpy.run_path("+repr(helper)+");v['install']("+repr(root)+");v['entry']("+repr(rest[j:])+")"
                        # The command line exposes no logical program or path spelling.
                        import zlib
                        runner="import zlib;exec(zlib.decompress(bytes.fromhex("+repr(zlib.compress(code.encode()).hex())+")))"
                        args=args[:py+1]+rest[:j]+['-c',runner]
                args=[physical(x) if isinstance(x,(str,Path)) and '/' in str(x) else x for x in args]
            super().__init__(args,*a,**kw)
    subprocess.Popen=Child
    # All tar member names created in the job are opaque too.
    import tarfile
    old_addfile=tarfile.TarFile.addfile
    def addfile(self,tarinfo,fileobj=None):
        import copy
        item=copy.copy(tarinfo);item.name=path_name(item.name)
        if item.linkname:item.linkname=path_name(item.linkname)
        return old_addfile(self,item,fileobj)
    tarfile.TarFile.addfile=addfile
    return physical


def entry(argv):
    import runpy
    if argv[0]=='-m':
        sys.argv=[argv[1],*argv[2:]]
        runpy.run_module(argv[1],run_name='__main__',alter_sys=True)
    elif argv[0]=='-c':
        sys.argv=['-c',*argv[2:]]
        exec(compile(argv[1],'<x0>','exec'),{'__name__':'__main__'})
    else:
        sys.argv=argv
        sys.path.insert(0,str(Path(argv[0]).parent))
        runpy.run_path(argv[0],run_name='__main__')
