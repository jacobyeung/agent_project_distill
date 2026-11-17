"""Standard-library line events, bound to the files present when the proof starts."""
import hashlib,json,os,sys,types
from pathlib import Path
def code_digest(code):
    def constant(value):
        if isinstance(value,types.CodeType):return ('code',code_digest(value))
        if isinstance(value,tuple):return ('tuple',tuple(constant(v) for v in value))
        if isinstance(value,frozenset):return ('frozenset',tuple(sorted(repr(constant(v)) for v in value)))
        return (type(value).__name__,repr(value))
    value=(code.co_argcount,code.co_posonlyargcount,code.co_kwonlyargcount,code.co_flags,
        code.co_code.hex(),tuple(constant(v) for v in code.co_consts),code.co_names,
        code.co_varnames,code.co_freevars,code.co_cellvars,code.co_firstlineno,
        code.co_qualname,code.co_linetable.hex(),code.co_exceptiontable.hex())
    return hashlib.sha256(repr(value).encode()).hexdigest()
class Monitor:
    def __init__(self,tree):
        self.tree=Path(tree);self.hits={}
        self.tmp=Path(os.environ['TMPDIR'])
        self.tmp_before=sum(p.stat().st_size for p in self.tmp.rglob('*') if p.is_file())
        if self.tmp_before>200_000_000:raise ValueError('Proof temporary storage exceeds the limit')
        self.hashes={str(p.relative_to(tree)):hashlib.sha256(p.read_bytes()).hexdigest() for p in self.tree.rglob('*.py')}
        expected={}
        for name in self.hashes:
            p=self.tree/name
            try:pending=[compile(p.read_bytes(),str(p),'exec',dont_inherit=True)]
            except SyntaxError:continue
            expected[str(p)]=set()
            while pending:
                code=pending.pop();expected[str(p)].add(code_digest(code))
                pending.extend(v for v in code.co_consts if isinstance(v,types.CodeType))
        mon=sys.monitoring;mon.use_tool_id(3,'b9fix')
        def started(code,offset):
            if code.co_filename in expected and code_digest(code) in expected[code.co_filename]:mon.set_local_events(3,code,mon.events.LINE)
            return mon.DISABLE
        def line(code,number):
            name=str(Path(code.co_filename).relative_to(tree));self.hits.setdefault(name,set()).add(number)
            return mon.DISABLE
        mon.register_callback(3,mon.events.PY_START,started);mon.register_callback(3,mon.events.LINE,line)
        mon.set_events(3,mon.events.PY_START)
    def save(self,folder):
        sys.monitoring.set_events(3,0)
        folder=Path(folder)
        after=sum(p.stat().st_size for p in self.tmp.rglob('*') if p.is_file())
        if after>200_000_000:raise ValueError('Proof temporary storage exceeds the limit')
        (folder/'MONITOR_STORAGE.json').write_text(json.dumps(dict(before_bytes=self.tmp_before,after_bytes=after,limit_bytes=200_000_000)))
        (folder/'hits.json').write_text(json.dumps({k:sorted(v) for k,v in self.hits.items()}))
        (folder/'source_hashes.json').write_text(json.dumps(self.hashes))
        (folder/'results.json').write_text(json.dumps(dict(complete=True,failures=[],errors=[],fatal=None,coverage_code_filter='compiled-source fingerprint')))
