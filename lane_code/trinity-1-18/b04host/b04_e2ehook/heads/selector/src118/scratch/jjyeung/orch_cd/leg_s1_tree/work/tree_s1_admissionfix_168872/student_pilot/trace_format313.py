"""Optional v3.13 response session; masks and geometry belong to its provider."""
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps
from copy import deepcopy
import inspect
import re

_current=ContextVar('trace313_session',default=None)
_rows=ContextVar('trace313_rows',default=None)
TAIL=re.compile(r'<(?:ground|gap|surface_pair|extent_ends)\b[^<>\n]*>$')

def bind_state(state):
    session=_current.get()
    if session is not None and hasattr(session,"bind_state"):session.bind_state(state)

def active():return _current.get() is not None

def extra_tail(text):return TAIL.search(text) if active() else None

def respond(call,registry):
    session=_current.get()
    if session is None or not call.startswith(('<ground','<gap','<surface_pair','<extent_ends')):
        return None
    session.registry=registry
    try:
        text=session.execute(call)
    except ValueError as exc:
        return 'error: '+str(exc)+'; answer directly from the video',dict(kind='error',code=str(exc),spec_version=session.spec_version,direct_answer_fallback=True)
    registry._points=session.registry._points
    session.registry=registry
    return text,dict(kind='gap' if call.startswith('<gap') else 'ground' if call.startswith('<ground') else 'keypoint',spec_version=session.spec_version,spec_revision=5 if session.spec_version=='3.13' else 1,audit=deepcopy(session.events[-1].get('audit',{})))

@contextmanager
def row(index):
    sessions=_rows.get()
    if sessions is None:
        yield;return
    token=_current.set(sessions[index])
    try:yield
    finally:_current.reset(token)

def bind_generate(generate):
    @wraps(generate)
    def bound(model,processor,batch,*args,trace_session=None,trace_program_version=None,geometry_mode=None,**kwargs):
        from .trace_version import model_version
        if trace_session is None and (trace_program_version is not None or (getattr(model,'trace_program_version',None) is not None and kwargs.get('ground_backend') is not None)):
            trace_program_version=model_version(model,trace_program_version)
        if trace_session is not None:
            sessions=trace_session if isinstance(trace_session,(list,tuple)) else [trace_session]
            for s in sessions:model_version(model,s.spec_version)
        elif trace_program_version is None and getattr(model,'trace_program_version',None)=='3.14':
            from trace_format.program_errors import ProgramRefusal
            raise ProgramRefusal('trace_program_version_missing')
        if trace_program_version is not None:
            if trace_session is not None:raise ValueError('Specify a session or a program version')
            from .live_trace313 import LiveSession
            backend=kwargs.get('ground_backend')
            if backend is None:raise ValueError('Live trace version requires ground_backend')
            trace_session=([LiveSession(b,program_version=trace_program_version,geometry_mode=geometry_mode) for b in backend]
                           if isinstance(batch,(list,tuple)) else LiveSession(backend,program_version=trace_program_version,geometry_mode=geometry_mode))
        if trace_session is None:return generate(model,processor,batch,*args,**kwargs)
        if active() or _rows.get() is not None:raise ValueError('Recursive trace session')
        if kwargs.get('reread') is not None:raise ValueError('Trace formatter and HRP reread require separate calls')
        if isinstance(batch,(list,tuple)):
            if not isinstance(trace_session,(list,tuple)) or len(trace_session)!=len(batch):
                raise ValueError('One trace session per batch row is required')
            if len({id(s) for s in trace_session})!=len(trace_session):raise ValueError('Trace sessions must be distinct')
            context=_rows
        else:context=_current
        sessions=trace_session if isinstance(trace_session,(list,tuple)) else [trace_session]
        if any(getattr(s,'spec_version',None) not in ('3.13','3.14') or not callable(getattr(s,'execute',None)) for s in sessions):
            raise ValueError('Use the pinned trace_format.ground_v313.Session')
        token=context.set(trace_session)
        try:return generate(model,processor,batch,*args,**kwargs)
        finally:context.reset(token)
    signature=inspect.signature(generate);parameters=list(signature.parameters.values())
    position=next((i for i,p in enumerate(parameters) if p.kind==inspect.Parameter.VAR_KEYWORD),len(parameters))
    parameters[position:position]=[
        inspect.Parameter('trace_session',inspect.Parameter.KEYWORD_ONLY,default=None),
        inspect.Parameter('trace_program_version',inspect.Parameter.KEYWORD_ONLY,default=None),
        inspect.Parameter('geometry_mode',inspect.Parameter.KEYWORD_ONLY,default=None)]
    bound.__signature__=signature.replace(parameters=parameters)
    return bound
