"""Navigation text actions (design record 1.5, `codec: nav`): the NaVILA / Aux-Think mid-level
vocabulary. A decision writes one to three actions, comma-separated, for example
"forward 0.50, turn_left 30". Each executes as 0.25 m and 15 degree primitives.

    encode([Action('forward', 0.5), Action('turn_left', 30)]) -> 'forward 0.50, turn_left 30'
    decode(text) -> list[Action] | None (None = parse failure: re-query once, then FALLBACK)
    primitives(actions) -> ['forward', 'forward', 'turn_left', 'turn_left', ...] (+ 'stop')
"""
from dataclasses import dataclass
import re

VALUES = {'forward': (0.25, 0.50, 0.75), 'turn_left': (15, 30, 45), 'turn_right': (15, 30, 45), 'stop': (None,)}
MAX_ACTIONS = 3
FALLBACK = 'turn_left 15'
FORWARD_STEP_M, TURN_STEP_DEG = 0.25, 15


@dataclass(frozen=True)
class Action:
    name: str
    value: object = None

    def __post_init__(self):
        if self.name not in VALUES:
            raise ValueError(f'Unknown navigation action {self.name!r}')
        if self.value not in VALUES[self.name]:
            raise ValueError(f'{self.name} takes one of {VALUES[self.name]}, got {self.value!r}')

    def text(self):
        if self.name == 'stop':
            return 'stop'
        return f'forward {self.value:.2f}' if self.name == 'forward' else f'{self.name} {int(self.value)}'


def encode(actions):
    actions = list(actions)
    if not 1 <= len(actions) <= MAX_ACTIONS:
        raise ValueError(f'A decision holds 1 to {MAX_ACTIONS} actions')
    if any(a.name == 'stop' for a in actions[:-1]):
        raise ValueError('stop can only be the last action')
    return ', '.join(a.text() for a in actions)


_ITEM = re.compile(r'^(forward|turn_left|turn_right)\s+([0-9]+(?:\.[0-9]+)?)$|^(stop)$')


def decode(text):
    items = [s.strip() for s in text.strip().split(',') if s.strip()]
    if not 1 <= len(items) <= MAX_ACTIONS:
        return None
    out = []
    for item in items:
        m = _ITEM.match(item)
        if m is None:
            return None
        if m.group(3):
            out.append(Action('stop'))
            continue
        name, raw = m.group(1), float(m.group(2))
        value = raw if name == 'forward' else int(raw)
        if value not in VALUES[name]:
            return None
        out.append(Action(name, value))
    if any(a.name == 'stop' for a in out[:-1]):
        return None
    return out


def primitives(actions):
    out = []
    for a in actions:
        if a.name == 'stop':
            out.append('stop')
        elif a.name == 'forward':
            out += ['forward'] * round(a.value / FORWARD_STEP_M)
        else:
            out += [a.name] * (a.value // TURN_STEP_DEG)
    return out
