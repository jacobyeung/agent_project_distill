"""Camera-only dispatch, scoped to one serial decoder invocation."""
from contextlib import contextmanager
import re

SERVED=frozenset(('move','turn','pose'))
RESPONSE='error: call_unavailable; answer directly from the video'
CODE='call_unavailable'
# Ordinary XML thinking and answer tags are not calls.
TAIL=re.compile(r'<(?!(?:think|answer|tool_response)\b)([A-Za-z_][A-Za-z_0-9]*)\b[^<>\n]*>$')

def name(text):
    match=re.match(r'<([A-Za-z_][A-Za-z_0-9]*)\b',text)
    return match[1] if match else 'unknown'

@contextmanager
def camera_only():
    from student_pilot import carrier_c1_decode as D
    original=D.respond_state;original_tail=D.trace313.extra_tail
    def respond(state,text,registry):
        call_name=name(text)
        if call_name not in SERVED:
            return RESPONSE,dict(kind='error',code=CODE,name=call_name,refused=True,
                                 direct_answer_fallback=True)
        response,info=original(state,text,registry)
        return response,dict(info,name=call_name,refused=False)
    def extra_tail(text):
        return TAIL.search(text) or original_tail(text)
    D.respond_state=respond;D.trace313.extra_tail=extra_tail
    try:yield
    finally:D.respond_state=original;D.trace313.extra_tail=original_tail

def records(decoded):
    result=[]
    for c in decoded['calls']:
        n=name(c['call']);refused=n not in SERVED
        if refused and (c['response']!=RESPONSE or c.get('original_kind',c.get('kind'))!='error'):
            raise ValueError('non-camera call escaped refusal policy')
        result.append(dict(name=n,text=c['call'],position=c.get('at_token',0),
                           response=c['response'],refused=refused,kind=c.get('original_kind',c['kind'])))
    return result
