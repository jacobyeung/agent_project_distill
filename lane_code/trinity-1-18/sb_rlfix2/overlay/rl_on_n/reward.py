"""Benchmark correctness, bounded thought length, and routed call placement."""
import math
import re
from dataclasses import dataclass

@dataclass(frozen=True)
class Weights:
    correct: float = 1.0
    short: float = 0.1
    route: float = 0.1
    short_tokens: int = 128
    long_tokens: int = 1024

    def __post_init__(self):
        if any(not math.isfinite(v) or v < 0 for v in (self.correct,self.short,self.route)):
            raise ValueError('Reward weights must be finite and nonnegative')
        if not 0 <= self.short_tokens < self.long_tokens:
            raise ValueError('Invalid length range')

# Tool names come from N's native head and calculator protocol. Unknown tags get no routing credit.
CALL = re.compile(r'<(?:depth_at|pose|move|turn|ground|gap|surface_pair|extent_ends|box_3d|dist|angle|closest)\b[^<>\n]*>')
RESPONSE = re.compile(r'<tool_response>\s*(.*?)\s*</tool_response>', re.S)
HEADS = {'camera_displacement': {'move'}, 'camera_movement_direction': {'move'},
         'camera_rotation': {'turn'}, 'object_abs_distance': {'ground', 'gap'},
         'absolute_distance_object': {'ground', 'gap'}}

def score(prompt, record, tokenizer, route_table, weights=None):
    from evalpath.run import score_item
    if record.get('diagnostic_arm'):
        raise ValueError('Diagnostic own heads cannot enter the reward path')
    if record.get('refusal') or record.get('tower_error') or record.get('strict_no_answer') or record.get('finish')=='max_calls':
        return dict(correct=0., short=0., route=0., thought_tokens=0, answer=None, total=0.)
    w = weights or Weights()
    kind = prompt['type']
    if kind not in route_table or route_table[kind] not in ('route', 'direct'):
        raise ValueError('Unknown route type: '+str(kind))
    text = record['text']
    body = text.split('</think>', 1)[0].removeprefix('<think>')
    prose = RESPONSE.sub('', body)
    n = len(tokenizer.encode(prose, add_special_tokens=False))
    official = score_item(dict(question_type=kind, ground_truth=str(prompt['gt_answer']),
                               options=prompt.get('options') or []),
                          dict(text=text, finish=record.get('finish')))
    c, answer = official['score'], official['official_fuzzy_pred'] or None
    closed = '</think>' in text and record.get('finish') == 'eos' and not record.get('budget_hit', False)
    short = max(0.0, 1.0-max(0,n-w.short_tokens)/(w.long_tokens-w.short_tokens)) if closed and prose.strip() else 0.0
    calls = record.get('calls', [])
    printed = RESPONSE.findall(text)
    forced_ok = len(printed) == len(calls) and all(
        p == str(call.get('response','')).strip() for p,call in zip(printed,calls))
    attempted = CALL.findall(RESPONSE.sub('',text))
    # Calls must occur within the thought and in decoder order, with an injected response each.
    offsets=[]; start=0
    for call in calls:
        at=text.find(call['call'],start)
        offsets.append(at); start=at+len(call['call']) if at>=0 else start
    end = text.find('</think>')
    placed = all(at>=0 and (end<0 or at<end) for at in offsets)
    kinds = {re.match(r'<([a-z0-9_]+)',c['call'])[1] for c in calls if re.match(r'<([a-z0-9_]+)',c['call'])}
    good = [c for c in calls if c.get('served',True) and c.get('kind') != 'error' and not c.get('direct_answer_fallback')
            and not re.search(r'error:|"status"\s*:\s*"(?:not_seen|unresolved|error)"',str(c.get('response','')))]
    if route_table[kind]=='direct':
        route = float(not calls and not attempted and not printed)
    else:
        needed = HEADS.get(kind)
        if needed is None:
            raise ValueError('No native head requirement for routed type: '+kind)
        route = float(bool(good) and len(good)==len(calls) and forced_ok and placed and len(attempted)==len(calls)
                      and needed == kinds)
        if kind in ('object_abs_distance','absolute_distance_object'):
            ground_positions=[i for i,c in enumerate(good) if c['call'].startswith('<ground')]
            gap_positions=[i for i,c in enumerate(good) if c['call'].startswith('<gap')]
            route *= float(len(ground_positions)>=2 and bool(gap_positions) and ground_positions[1]<gap_positions[0])
    # Match the official final-answer boundary; no reward for hidden second thoughts.
    closes = re.findall(r'</think\s*>', text, re.IGNORECASE)
    if c == 0 or text.count('</think>') != 1 or len(closes) != 1:
        short = route = 0.0
    short*=c; route*=c
    return dict(correct=c, short=short, route=route, thought_tokens=n, answer=answer,
                total=w.correct*c+w.short*short+w.route*route)
