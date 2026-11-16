"""Stop before an item would consume the reserved return interval."""
from datetime import datetime,timezone
import time

DEFAULT='2026-11-16T16:15:00Z'
RETURN_SECONDS=600
MARGIN=1.25
BASE={'camera_displacement':6.0,'camera_movement_direction':7.3}

def timestamp(value):
    parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    if parsed.tzinfo is None:raise ValueError('deadline must include timezone')
    return parsed.timestamp()

class Budget:
    def __init__(self,deadline=None,return_seconds=RETURN_SECONDS,clock=time.time):
        self.deadline=timestamp(deadline) if deadline else None
        self.return_seconds=return_seconds;self.clock=clock;self.rates={}
        if return_seconds<0:raise ValueError('return reserve must be nonnegative')
    def observe(self,kind,seconds):
        if seconds<0:raise ValueError('negative item duration')
        self.rates.setdefault(kind,[]).append(seconds)
    def projected(self,kind):
        values=self.rates.get(kind,[])
        rate=max(values) if values else BASE.get(kind,100.)
        return MARGIN*max(rate,BASE.get(kind,0.))
    def allows(self,kind):
        return self.deadline is None or self.clock()<self.item_cutoff()
    def max_item_seconds(self):
        return max([100.]+[v for values in self.rates.values() for v in values])
    def item_cutoff(self):
        return None if self.deadline is None else self.deadline-self.return_seconds-MARGIN*self.max_item_seconds()
    def remaining(self):
        return None if self.deadline is None else max(0.,self.deadline-self.return_seconds-self.clock())
    def record(self):
        return dict(deadline_epoch=self.deadline,return_seconds=self.return_seconds,margin=MARGIN,rates=self.rates,
                    max_item_seconds=self.max_item_seconds(),item_cutoff=self.item_cutoff(),
                    subprocess_kill=None if self.deadline is None else self.deadline-self.return_seconds)
