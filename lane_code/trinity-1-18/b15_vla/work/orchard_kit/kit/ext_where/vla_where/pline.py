"""The where line (schema 5.4, P-line style):

  where_line  := "where: " entity_text ("; " entity_text)? "."
  entity_text := role ' "' phrase '" ' body
  body        := "p " P2 " agent " view " wrist " view metric
               | "not seen"   (low_presence or no_point in every view)
               | "unsure"     (no_lift, cross_view or behind_wrist)
               | "withheld"   (training dropout and the withheld evaluation check)
  view        := "[" U1000 "," V1000 "]" | "out of view"
  metric      := " cam (" M2 ", " M2 ", " M2 ") m reach (" M2 ", " M2 ", " M2 ") m size " M2 " x " M2 " x " M2 " m"
               | " scale unknown"

P2 and M2 print with two decimals ("-0.00" prints "0.00"); in-frame U1000 = min(floor(1000 u01 + 1e-9), 999) from the
float64 value, never from the fp32 record (schema 0).
An entity without a phrase (a step without a place) prints nothing.
"""
import math

NOT_SEEN = ('low_presence', 'no_point')
UNSURE = ('no_lift', 'cross_view', 'behind_wrist')


def number(value):
    value = float(value)
    if not math.isfinite(value):
        raise ValueError('Nonfinite where value')
    text = f'{value:.2f}'
    return '0.00' if text == '-0.00' else text


def uv1000(u01):
    return min(math.floor(1000 * float(u01) + 1e-9), 999)


def view_text(uv):
    u, v = uv
    if not (0 <= u < 1 and 0 <= v < 1):
        return 'out of view'
    return f'[{uv1000(u)},{uv1000(v)}]'


def triple(values):
    return '(' + ', '.join(number(v) for v in values) + ')'


def body(e):
    if e.withheld:
        return 'withheld'
    if not e.valid:
        if e.reason in NOT_SEEN:
            return 'not seen'
        if e.reason in UNSURE:
            return 'unsure'
        raise ValueError(f'No body for an invalid entity with reason {e.reason!r}')
    text = f'p {number(e.presence)} agent {view_text(e.uv_agent)} wrist {view_text(e.uv_wrist)}'
    if not e.metric:
        return text + ' scale unknown'
    return (text + f' cam {triple(e.X_wrist)} m reach {triple(e.reach_base)} m size '
            + ' x '.join(number(v) for v in e.size) + ' m')


def entity_text(e):
    return f'{e.role} "{e.phrase}" {body(e)}'


def format_line(entities):
    parts = [entity_text(e) for e in entities if e.phrase]
    if not parts:
        raise ValueError('A where line needs at least one entity with a phrase')
    return 'where: ' + '; '.join(parts) + '.'
