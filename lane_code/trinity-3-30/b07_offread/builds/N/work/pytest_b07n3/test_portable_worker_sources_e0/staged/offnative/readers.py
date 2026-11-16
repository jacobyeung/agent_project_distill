"""One interface; native and end-to-end cores stay with their existing owners."""
from typing import Protocol
from .paths import module, C8

class Reader(Protocol):
    kind: str
    def generate(self, frames, question, *, served=True): ...
    def replay(self, decoded): ...

class E2EReader:
    kind = 'e2e'
    def __init__(self, entry, replay):
        self.entry, self._replay = entry, replay

    def generate(self, frames, question, *, served=True):
        if not served:
            raise ValueError('end-to-end reader has exactly one arm')
        decoded = self.entry.generate(frames, question)
        if not isinstance(decoded, dict) or not isinstance(decoded.get('text'), str):
            raise TypeError('b04 socket must return raw text and its decode audit')
        return decoded

    def replay(self, decoded):
        return self._replay(decoded)

class HarnessReader:
    kind = 'harness'
    def __init__(self, model, processor, context, direct):
        self.model, self.processor, self.context, self.direct = model, processor, context, direct
        self._contexts = {}

    def generate(self, frames, question, *, served=True):
        if not served:
            return self.direct.generate(frames, question)
        # context owns prompt preparation, same-frame geometry and C8r mask receipt loading.
        from .c8 import ItemRefusal
        try:
            batch, geometry, backend = self.context(frames, question)
        except ItemRefusal as exc:
            import nomdg
            decoded=nomdg.refusal_decode(str(exc))
            self._contexts[id(decoded)]=(None,None)
            return decoded
        import perception
        import reader_policy
        decoded = perception.generate(self.model, self.processor, batch, geometry, backend,
                                      budget=reader_policy.DECODE_BUDGET)
        import re
        source=getattr(backend,'frozen_mask_source',None)
        if source is not None:
            names=[name for call in decoded.get('calls',[]) for name in
                   re.findall(r'\b(?:obj|a|b)="([^"<>]+)"',call['call'])]
            try:perception.require_phrases('runtime',names,source.cache['phrases'])
            except perception.MaskOperandMissing as exc:
                decoded['strict_no_answer']=True
                decoded['operand_refusal']=str(exc)
        if any('mask_cache_operand_missing' in str(c.get('code','')) or
               'mask_source_unavailable' in str(c.get('code','')) for c in decoded.get('calls',[])):
            decoded['strict_no_answer'] = True
            decoded['operand_refusal'] = True
        self._contexts[id(decoded)] = (geometry, backend)
        return decoded

    def replay(self, decoded):
        import perception
        geometry, backend = self._contexts[id(decoded)]
        if decoded.get('finish')=='program_refusal' and not decoded.get('calls'):return True
        return perception.replay(decoded, geometry, backend)['byte_equal']

class DirectReader:
    kind = 'direct'
    def __init__(self, entry):
        self.entry = entry

    def generate(self, frames, question, *, served=True):
        return self.entry.generate(frames, question)

    def replay(self, decoded):
        return not decoded.get('calls')
