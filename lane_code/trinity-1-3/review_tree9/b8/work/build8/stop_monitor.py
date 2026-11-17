"""Exact-source statement monitoring for the native rank process."""
import hashlib,json,sys,types
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
    def __init__(self,tree,output):
        self.tree,self.output=tree,output;self.hits={};self.hashes={};self.expected={}
        for p in tree.rglob('*.py'):
            if any(v in p.parts for v in ('__pycache__','.git','artifacts','tests')):continue
            raw=p.read_bytes();self.hashes[str(p.relative_to(tree))]=hashlib.sha256(raw).hexdigest()
            try:pending=[compile(raw,str(p),'exec',dont_inherit=True)]
            except SyntaxError:continue
            codes=set()
            while pending:
                c=pending.pop();codes.add(code_digest(c));pending.extend(v for v in c.co_consts if isinstance(v,types.CodeType))
            self.expected[str(p)]=codes
        self.mon=sys.monitoring;self.mon.use_tool_id(4,'rank-stop-proof')
        self.mon.register_callback(4,self.mon.events.PY_START,self.start)
        self.mon.register_callback(4,self.mon.events.LINE,self.line)
        self.mon.set_events(4,self.mon.events.PY_START)
    def start(self,code,offset):
        if code.co_filename in self.expected and code_digest(code) in self.expected[code.co_filename]:
            self.mon.set_local_events(4,code,self.mon.events.LINE)
        return self.mon.DISABLE
    def line(self,code,number):
        name=str(Path(code.co_filename).relative_to(self.tree));self.hits.setdefault(name,set()).add(number)
        return self.mon.DISABLE
    def finish(self,complete):
        self.mon.set_events(4,0);self.output.mkdir(exist_ok=True)
        for name,value in [('source_hashes',self.hashes),('hits',{k:sorted(v) for k,v in self.hits.items()}),
                           ('results',dict(complete=complete,coverage_code_filter='compiled-source fingerprint'))]:
            (self.output/(name+'.json')).write_text(json.dumps(value)+'\n')
