"""Public identity boundary. Keep the reverse map on the private host."""
import hashlib
import json as _json
from pathlib import Path
import re
import platform

RAW_LOADS = _json.loads

IDENTITIES = {'id','qid','example_id','key','room','room_key','native','scene','dataset',
              'name','question_type','type','item_id','reader_entry'}
# Established staging roots; the remaining components must be neutral tokens.
APPROVED_PREFIXES = ('/scratch/jjyeung', '/project/community/jjyeung/okh7',
                     '/project/community/jjyeung', '/scratch', '/project')
_SEGMENT = r'(?:u[0-9a-f]+|[a-z]?[0-9a-f]+|[a-z])(?:\.[a-z0-9]+)?'
_TOKEN_PATH = re.compile(r'^'+_SEGMENT+r'(?:/'+_SEGMENT+r')*$')


def opaque_path(value):
    value = str(value)
    # Use the production screen when available. The standalone public wire
    # helper retains the identical screen for private staging without imports.
    try:
        from orchard_h10.common import opaque
    except ImportError:
        forbidden = ('split', 'revsi', 'vsibench', 'scannet', 'arkit', 'distill', 'qgen',
                     'sam', 'qwen', 'h1', 'h10', 'head', 'routing', 'faithful', 'devs1',
                     'g3t', 'camera', 'displacement', 'rotation', 'movement', 'distance',
                     'r0', 'scannetpp', 'direction', 'own', 'room', 'selector', 'parity', 'benchmark', 'dataset', 'model')
        def opaque(values):
            if any(word in str(v).lower() for v in values for word in forbidden):
                raise ValueError('Non-opaque staged path')
    try:opaque([value])
    except ValueError:return False
    for prefix in APPROVED_PREFIXES:
        if not value.startswith(prefix+'/'):continue
        rest=value[len(prefix)+1:]
        if prefix=='/project/community/jjyeung/okh7':
            rest=re.sub(r'^a15_cot_ap[a-f][0-9a-f]{10,15}(?=/|$)', 'u0', rest)
        if _TOKEN_PATH.fullmatch(rest):return True
    return False


class _PathGrammar:
    @staticmethod
    def fullmatch(value):return opaque_path(value)


OPAQUE_PATH = _PathGrammar()


def pack(value):
    """A token-only JSON wire schema; runtime field names stay in program code."""
    if isinstance(value,str):return 'u'+value.encode().hex()
    if isinstance(value,dict):return {pack(k):pack(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [pack(v) for v in value]
    return value


def unpack(value):
    if isinstance(value,str):
        if not re.fullmatch(r'u(?:[0-9a-f]{2})*',value):raise ValueError('Invalid public string token')
        return bytes.fromhex(value[1:]).decode()
    if isinstance(value,dict):return {unpack(k):unpack(v) for k,v in value.items()}
    if isinstance(value,list):return [unpack(v) for v in value]
    return value


def read_wire(value):
    return unpack(value['u0']) if isinstance(value,dict) and set(value)=={'u0'} else value


def validate_paths(settings):
    def check(value):
        if isinstance(value,dict):
            for item in value.values():check(item)
        elif isinstance(value,list):
            for item in value:check(item)
        elif isinstance(value,str) and value.startswith('/') and not OPAQUE_PATH.fullmatch(value):
            raise ValueError('Settings contain a non-opaque staged asset path')
    check(settings)


def seal_settings(settings, path):
    """Run on Trinity. Every referenced staged asset needs a neutral alias."""
    validate_paths(settings)
    Path(path).write_text(_json.dumps({'u0':pack(settings)},sort_keys=True)+'\n')


def load_settings(path, name):
    raw=RAW_LOADS(Path(path).read_bytes())
    if not isinstance(raw,dict) or set(raw)!={'u0'}:raise ValueError('Public execution requires token-only settings')
    settings=read_wire(raw)
    settings.update(settings.get('item_sets',{}).get(name,{}))
    settings['arm']='own_depth'
    return settings


def install_wire_decoder():
    """Explicit public mode only; ordinary JSON and source hash bytes stay intact."""
    def loads(value,*args,**kwargs):return read_wire(RAW_LOADS(value,*args,**kwargs))
    _json.loads=loads


def token(value):
    return 'u'+hashlib.sha256(value.encode()).hexdigest()


class Codec:
    def __init__(self, *sources):
        self.forward = {}; self.reverse = {}
        for source in sources:self.collect(source)

    def add(self, value):
        if type(value) is str and value:
            public=token(value)
            if public in self.reverse and self.reverse[public]!=value:raise ValueError('Identity token collision')
            self.forward[value]=public; self.reverse[public]=value

    def collect(self, value, field=None):
        if isinstance(value,dict):
            for key,item in value.items():self.collect(item,key)
        elif isinstance(value,(list,tuple)):
            for item in value:self.collect(item,field)
        elif isinstance(value,str):
            if field in IDENTITIES:
                self.add(value)
                if field in ('id','qid','example_id'):self.add('devrows:'+value)
            if value.startswith(('/scratch/','/project/','/tmp/','/home/','/data')):self.add(value)

    def encode(self, value):
        if isinstance(value,dict):return {self.forward.get(k,k):self.encode(v) for k,v in value.items()}
        if isinstance(value,(list,tuple)):return [self.encode(v) for v in value]
        if isinstance(value,str):
            if value.startswith(('/scratch/','/project/','/tmp/','/home/','/data')):self.add(value)
            return self.forward.get(value,value)
        return value

    def decode(self, value):
        if isinstance(value,dict):return {self.reverse.get(k,k):self.decode(v) for k,v in value.items()}
        if isinstance(value,list):return [self.decode(v) for v in value]
        if isinstance(value,str):return self.reverse.get(value,value)
        return value


class PublicJSON:
    def __init__(self, codec):self.codec=codec
    def dumps(self, value, *args, **kwargs):return _json.dumps({'u0':pack(self.codec.encode(value))},*args,**kwargs)
    def loads(self, value, *args, **kwargs):return self.codec.decode(read_wire(RAW_LOADS(value,*args,**kwargs)))


class PublicLog:
    """Never publish arbitrary library stdout/stderr or a traceback."""
    def __init__(self, stream):self.stream=stream;self.pending=''
    def write(self, text):
        self.pending+=text
        while '\n' in self.pending:
            line,self.pending=self.pending.split('\n',1)
            self.stream.write(_json.dumps({'event':token(line)})+'\n')
        return len(text)
    def flush(self):
        if self.pending:
            self.stream.write(_json.dumps({'event':token(self.pending)})+'\n');self.pending=''
        self.stream.flush()
    def __getattr__(self, name):return getattr(self.stream,name)
    def __enter__(self):return self
    def __exit__(self,*args):
        self.flush()
        return self.stream.__exit__(*args)


def install_log_boundary():
    """The explicit parity driver wraps original and extended readers equally."""
    import sys
    original=Path.open
    def open_path(path,mode='r',*args,**kwargs):
        stream=original(path,mode,*args,**kwargs)
        if path.name=='worker.log' and ('a' in mode or 'w' in mode) and 'b' not in mode:
            return PublicLog(stream)
        return stream
    Path.open=open_path
    sys.stdout=PublicLog(sys.stdout);sys.stderr=PublicLog(sys.stderr)


def validate_config(config):
    """New submission configs use neutral staged paths and numeric type slots."""
    for key in ('journal_root','items','export','export_pin','artifact_manifest','reader_root','settings'):
        if not isinstance(config.get(key),str) or not OPAQUE_PATH.fullmatch(config[key]):
            raise ValueError('Public configuration requires opaque staged paths')
    if any(type(slot) is not int or not 0<=slot<5 for slot in config['types']):
        raise ValueError('Public configuration requires numeric type slots')
    if config.get('opaque') is not True:raise ValueError('Public execution requires opaque=True')


def restore(source, destination, private_sources):
    """Run on Trinity after return; never copy this reverse map to Orchard."""
    if not re.fullmatch(r'trinity-[0-9]+-[0-9]+',platform.node().split('.')[0]):
        raise ValueError('Private restoration requires a Trinity compute node')
    codec=Codec(*private_sources)
    source=Path(source);destination=Path(destination)
    destination.mkdir(parents=True,exist_ok=False)
    # Authenticate the public commit store before rewriting its checksums and
    # filenames for private IDs. A public checksum never authenticates new bytes.
    from h1eval.h10 import atomic_journal as journal
    handled=set()
    for env_path in source.rglob('environment.json'):
        root=env_path.parent
        if not (root/'committed').is_dir():continue
        old_json=journal.json
        try:
            journal.json=PublicJSON(codec)
            reader=object.__new__(journal.AtomicJournal)
            reader.root=root;reader.directory=root/'committed'
            rows=reader.read()
            environment=journal.json.loads(env_path.read_bytes())
        finally:journal.json=old_json
        target=destination/root.relative_to(source);target.mkdir(parents=True,exist_ok=True)
        (target/'environment.json').write_text(_json.dumps(environment,indent=2)+'\n')
        try:
            journal.json=_json
            writer=journal.AtomicJournal(target)
            for row in rows:writer.commit(row)
            writer.recover()
        finally:journal.json=old_json
        handled.add(root)
    for path in source.rglob('*'):
        if not path.is_file():continue
        if path.parent in handled and path.name in ('environment.json','items.jsonl'):continue
        if any(root/'committed' in path.parents for root in handled):continue
        relative=path.relative_to(source)
        if path.suffix not in ('.json','.jsonl'):continue
        target=destination/relative;target.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix=='.jsonl':
            values=[codec.decode(read_wire(RAW_LOADS(line))) for line in path.read_text().splitlines()]
            target.write_text(''.join(_json.dumps(v,allow_nan=False)+'\n' for v in values))
        else:target.write_text(_json.dumps(codec.decode(read_wire(RAW_LOADS(path.read_bytes()))),indent=2)+'\n')
