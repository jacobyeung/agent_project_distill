"""Import-time stand-in for llguidance 1.7.6 on hosts with glibc < 2.30 (its native _lib needs GLIBC_2.30).
Provides only the names vLLM 0.32.0 touches at import time; any real use raises, so a structured-output
(guidance) request fails loudly instead of silently changing behaviour. Unstructured greedy decoding never calls it."""
_MSG = 'llguidance stub: guidance structured outputs are unavailable on this host (glibc 2.28)'


class _Unavailable:
    def __init__(self, *a, **k):
        raise RuntimeError(_MSG)


class LLMatcher(_Unavailable):
    pass


class LLTokenizer(_Unavailable):
    pass


class LLInterpreter(_Unavailable):
    pass


def __getattr__(name):
    raise AttributeError(_MSG + ' (attribute %r)' % name)
