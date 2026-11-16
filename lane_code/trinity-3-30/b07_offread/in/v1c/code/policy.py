"""Camera-only dispatch, scoped to one serial decoder invocation."""
from contextlib import contextmanager
from contextvars import ContextVar
import re

SERVED=frozenset(('move','turn','pose'))
RESPONSE='error: call_unavailable; answer directly from the video'
CODE='call_unavailable'
GEOMETRY_AVAILABLE=ContextVar('geometry_available',default=True)
# The trained grammar is installed lazily after the authenticated tree.
def tail_pattern():
    from reader_policy import CALL_NAMES
    return re.compile(r'<(?:'+ '|'.join(map(re.escape,CALL_NAMES))+r')(?=[ \t\r>])[^<>\n]*>$')

def name(text):
    match=re.match(r'<([A-Za-z_][A-Za-z_0-9]*)\b',text)
    return match[1] if match else 'unknown'

@contextmanager
def camera_only(geometry_available=None):
    from student_pilot import carrier_c1_decode as D
    import perception as P
    original=D.respond_state;original_tail=D.trace313.extra_tail;tail=tail_pattern()
    original_session=P.session
    def session(geometry,ground_backend=None):
        value=original_session(geometry,ground_backend)
        if not GEOMETRY_AVAILABLE.get():value.owner.allow_own_geometry_fallback=False
        return value
    def respond(state,text,registry):
        call_name=name(text)
        if call_name not in SERVED or not GEOMETRY_AVAILABLE.get():
            return RESPONSE,dict(kind='error',code=CODE,name=call_name,refused=True,
                                 reason='camera_only' if call_name not in SERVED else 'capture_geometry_refused',direct_answer_fallback=True)
        response,info=original(state,text,registry)
        return response,dict(info,name=call_name,refused=False)
    def extra_tail(text):
        return tail.search(text) or original_tail(text)
    token=GEOMETRY_AVAILABLE.set(GEOMETRY_AVAILABLE.get() if geometry_available is None else geometry_available)
    D.respond_state=respond;D.trace313.extra_tail=extra_tail
    P.session=session
    try:yield
    finally:
        D.respond_state=original;D.trace313.extra_tail=original_tail
        P.session=original_session
        GEOMETRY_AVAILABLE.reset(token)

def records(decoded):
    result=[]
    for c in decoded['calls']:
        n=name(c['call']);refused=n not in SERVED or c['response']==RESPONSE
        if refused and (c['response']!=RESPONSE or c.get('original_kind',c.get('kind'))!='error'):
            raise ValueError('non-camera call escaped refusal policy')
        result.append(dict(name=n,text=c['call'],position=c.get('at_token',0),
                           response=c['response'],refused=refused,kind=c.get('original_kind',c['kind']),
                           refusal_reason=('capture_geometry_refused' if n in SERVED else 'camera_only') if refused else None))
    return result
