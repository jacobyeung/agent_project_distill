"""Restrict selection using points, preserving text proposals and linking."""
from contextlib import contextmanager
from unittest.mock import patch
from . import c,w
from .points import resolve


def eligible_tracks(record,frame_points):
    hits=set()
    for proposal in record['proposals']:
        point=frame_points[proposal['frame']-1]
        if point is None:continue
        mask=c.unrle(proposal['mask']); h,width=mask.shape
        x,y=point
        if mask[min(int(y*h),h-1),min(int(x*width),width-1)]:hits.add(proposal['id'])
    tracks={str(t['id']) for t in record['linked_tracks'] if hits.intersection(t['members'])}
    return [i for i,candidate in enumerate(record['candidates']) if str(candidate['id']) in tracks]


@contextmanager
def restricted_context(gen,ref,points):
    import torch
    from e2e_reader import stage1
    current={}
    class RestrictedCapture(c.Capture):
        def __enter__(self):
            current['capture']=self
            return super().__enter__()
        def observe(self,frame,event,result):
            super().observe(frame,event,result)
            if event=='return' and self.codes.get(frame.f_code)=='select' and result is not None:
                v=frame.f_locals;record=self.by_name[v['inputs']['name']]
                record['selector'].update(restricted=True,eligible_indices=v['eligible'],
                                          points_name=v['mapped'],name_binding=v['binding_rule'])

    @torch.no_grad()
    def select(self,inputs):
        name=inputs['name'];mapped,binding_rule=resolve(name,points,stage1.name_key)
        frame_points=[points[mapped][str(s)] if mapped is not None else None for s in ref['source_indices']]
        record=current['capture'].by_name[name]
        eligible=eligible_tracks(record,frame_points)
        # Score the original pool so all relational features and the head's
        # null slot remain identical to deployed selection.
        slots=self.head.with_null(inputs['x'],None,name)
        if self.rule!='candidates_argmax':raise ValueError('restricted selector requires deployed candidates_argmax')
        choice=eligible[int(torch.argmax(slots[eligible]))] if eligible else -1
        if name in self.diagnostics:
            diagnostic=self.diagnostics[name]
            for candidate,logit in zip(diagnostic['candidates'],slots):candidate['logit']=float(logit)
            diagnostic.update(null_logit=float(slots[-1]),chosen_index=choice,
                              null_would_win=int(torch.argmax(slots))==len(slots)-1,
                              restricted=True,eligible_indices=eligible)
        return choice

    with patch.object(stage1.StageOne,'select',select),patch.object(w,'Capture',RestrictedCapture):
        yield
