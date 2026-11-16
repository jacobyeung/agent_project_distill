"""Navigation text actions: `nav_grammar_v1` (VLA_SCHEMA.md 8.1), one grammar for rows, runner and codec.

    nav_seq   := nav_act (", " nav_act){0,2}                     # arms N0, N1 (`nav`); "stop" only last
    nav_act   := "forward " ("0.25"|"0.50"|"0.75") | ("turn_left " | "turn_right ") ("15"|"30"|"45") | "stop"
    click     := "<goal frame=" N " x=" D2 " y=" D2 ">"          # arm NU (`click`); N = history_frames
    big_turn  := "turn_left 90" | "turn_right 90" | "turn_around"
    nu_dec    := click | big_turn | "stop"                         # NU: exactly one per decision

D2 is a two-decimal number in [0.00, 1.00] (x left to right, y top to bottom, uv01). The text read is
what follows the last `</think>`, stripped (`answer_text`), and it must fully match the arm's form.
A failed parse re-queries once with the same input; a second failure executes FALLBACK (one
`turn_left` primitive) and is logged.

Primitives: forward = 0.25 m; turn = 15 degrees; turn_left 90 = 6 turn_left; turn_right 90 =
6 turn_right; turn_around = 12 turn_left; stop = stop. A click's primitives come from the waypoint
controller (vla_where `nav.py`, schema 8.2), not from this module.

Constrained decoding: `allowed_strings(arm, history_frames)` enumerates the arm's finite language
(910 `nav` strings; 10,205 `click` strings), and `constraint(tokenizer, ...)` builds a `TokenTrie` of
their tokenizations whose `allowed(prefix_ids)` gives the next legal ids (the end id once a string
is complete); `prefix_allowed_tokens_fn` adapts it to transformers' `generate`.
"""
from dataclasses import dataclass
import re

GRAMMAR = 'nav_grammar_v1'
ARMS = ('nav', 'click')
FORWARD = ('0.25', '0.50', '0.75')
TURNS = ('15', '30', '45')
NAV_ACTS = tuple(f'forward {v}' for v in FORWARD) + tuple(
    f'{d} {v}' for d in ('turn_left', 'turn_right') for v in TURNS) + ('stop',)
BIG_TURNS = ('turn_left 90', 'turn_right 90', 'turn_around')
MAX_ACTIONS = 3
FORWARD_STEP_M, TURN_STEP_DEG = 0.25, 15
FALLBACK = ('turn_left',)
_ACT = '|'.join(re.escape(a) for a in NAV_ACTS)
_NAV = re.compile(rf'(?:{_ACT})(?:, (?:{_ACT})){{0,{MAX_ACTIONS - 1}}}')
_CLICK = re.compile(r'<goal frame=([1-9][0-9]*) x=([01]\.[0-9]{2}) y=([01]\.[0-9]{2})>')


@dataclass(frozen=True)
class Click:
    frame: int
    x: float
    y: float

    def text(self):
        return click_text(self.frame, self.x, self.y)


def answer_text(text):
    """The part of a model output the grammar reads: after the last `</think>`, stripped."""
    return text.rsplit('</think>', 1)[-1].strip()


def nav_text(acts):
    """['forward 0.50', 'turn_left 30'] -> 'forward 0.50, turn_left 30' (validated)."""
    text = ', '.join(acts)
    if parse(text, 'nav') is None:
        raise ValueError(f'{text!r} is not a nav_seq')
    return text


def click_text(frame, x, y):
    if not (0 <= x <= 1 and 0 <= y <= 1) or int(frame) < 1:
        raise ValueError('A click needs frame >= 1 and x, y in [0, 1]')
    return f'<goal frame={int(frame)} x={x:.2f} y={y:.2f}>'


def parse(text, arm, history_frames=None):
    """Model output -> decision, or None (parse failure).
    arm 'nav': list of nav_act strings. arm 'click': a Click, a big_turn string or 'stop'. A click
    must name frame = history_frames when that is given."""
    if arm not in ARMS:
        raise ValueError(f'arm must be one of {ARMS}')
    s = answer_text(text)
    if arm == 'nav':
        if not _NAV.fullmatch(s):
            return None
        acts = s.split(', ')
        return None if 'stop' in acts[:-1] else acts
    if s in BIG_TURNS or s == 'stop':
        return s
    m = _CLICK.fullmatch(s)
    if m is None:
        return None
    frame, x, y = int(m.group(1)), float(m.group(2)), float(m.group(3))
    if x > 1 or y > 1 or (history_frames is not None and frame != history_frames):
        return None
    return Click(frame, x, y)


def primitives(decision):
    """A parsed nav or NU decision (not a Click) -> primitive names (forward, turn_left, turn_right, stop)."""
    if isinstance(decision, Click):
        raise ValueError('Click primitives come from the waypoint controller (vla_where nav.py)')
    if decision == 'stop':
        return ['stop']
    if decision in BIG_TURNS:
        return {'turn_left 90': ['turn_left'] * 6, 'turn_right 90': ['turn_right'] * 6,
                'turn_around': ['turn_left'] * 12}[decision]
    out = []
    for act in decision:
        if act == 'stop':
            out.append('stop')
            continue
        name, value = act.split(' ')
        step = FORWARD_STEP_M if name == 'forward' else TURN_STEP_DEG
        out += [name] * round(float(value) / step)
    return out


def allowed_strings(arm, history_frames=None):
    """Every string of the arm's language (`click` needs history_frames)."""
    if arm == 'nav':
        moves = [a for a in NAV_ACTS if a != 'stop']
        out = list(NAV_ACTS)
        for n in range(2, MAX_ACTIONS + 1):
            prefixes = [[]]
            for _ in range(n - 1):
                prefixes = [p + [m] for p in prefixes for m in moves]
            out += [', '.join(p + [last]) for p in prefixes for last in NAV_ACTS]
        return out
    if arm == 'click':
        if history_frames is None:
            raise ValueError('The click arm needs history_frames (the current frame number)')
        grid = [f'{i / 100:.2f}' for i in range(101)]
        return [f'<goal frame={history_frames} x={x} y={y}>' for x in grid for y in grid] + list(BIG_TURNS) + ['stop']
    raise ValueError(f'arm must be one of {ARMS}')


class TokenTrie:
    """Prefix tree over token-id sequences; `allowed(prefix)` -> sorted next ids (end_id after a full sequence)."""

    def __init__(self, seqs, end_id):
        self.root, self.end_id = {}, end_id
        for seq in seqs:
            node = self.root
            for t in seq:
                node = node.setdefault(int(t), {})
            node[None] = True

    def allowed(self, prefix):
        node = self.root
        for t in prefix:
            node = node.get(int(t))
            if node is None:
                return []
        out = sorted(k for k in node if k is not None)
        return out + [self.end_id] if None in node else out


def constraint(tokenizer, arm, history_frames=None, end_id=None):
    """TokenTrie of the arm's strings as `tokenizer` writes them (end id: tokenizer.eos_token_id)."""
    end_id = tokenizer.eos_token_id if end_id is None else end_id
    if end_id is None:
        raise ValueError('constraint needs an end id (tokenizer.eos_token_id or end_id=)')
    seqs = [tokenizer.encode(s, add_special_tokens=False) for s in allowed_strings(arm, history_frames)]
    return TokenTrie(seqs, end_id)


def prefix_allowed_tokens_fn(trie, prompt_len):
    """transformers generate(prefix_allowed_tokens_fn=...) for prompts of length prompt_len."""
    def fn(batch_id, input_ids):
        return trie.allowed(input_ids[prompt_len:].tolist()) or [trie.end_id]
    return fn
