"""Room-area rows whose answers copy the printed footprint computation."""
import math
import re
from . import ground_v312 as G, room_v314 as R
from trace_format.contracts import geometry_mode

TYPE = 'room_size_estimation'
QUESTION = ('What is the size of this room (in square meters)? \n'
            'If multiple rooms are shown, estimate the size of the combined space.')
TOLERANCE_M2 = .0050000001


def agrees(answer, target):
    try:
        a, b = float(answer), float(target)
        return math.isfinite(a) and math.isfinite(b) and a > 0 and b > 0 and abs(a-b) <= TOLERANCE_M2
    except (ValueError, TypeError):
        return False


def render(item, session, token_count):
    if not item.get('gt_authority'):
        raise G.RowRefusal('independent_gt_authority_missing')
    if item['question'] != QUESTION or item.get('options'):
        raise G.RowRefusal('room_question_template_mismatch')
    if geometry_mode(session) != 'sensor':
        raise G.RowRefusal('room_training_requires_sensor')
    if session.events:
        raise ValueError('render requires a fresh session')
    body = session.execute(R.CALL)
    parsed = R.parse_response(body)
    answer = f"{parsed['area_m2']:.2f}"
    if not agrees(answer, item['gt_answer']):
        raise G.RowRefusal('independent_room_disagreement')
    suffix = ('<think>\nI will project the depth points onto the floor and measure their covered area.\n'
              + R.CALL + '\n' + G.wrap(body)
              + f'\nThe covered floor area is {answer} square meters.\n</think>\n<answer>{answer}</answer>')
    tokens = token_count(suffix)
    if type(tokens) is not int or not 0 <= tokens <= 5000:
        raise G.RowRefusal('suffix_cap')
    row = dict(qid=item['qid'], type=TYPE, question=item['question'], options=[],
               answer=answer, answer_content=answer, suffix=suffix, suffix_tokens=tokens,
               events=list(session.events), not_seen=False, simulated_misses=[],
               gt_answer=item['gt_answer'], gt_authority=item['gt_authority'],
               gt_accepted=True, gt_agrees=True, selection_refusal=None,
               program_audit=dict(room=session.events[-1]['audit']['room']))
    validate_computation(row)
    return row


def validate_computation(row):
    G.validate_evidence(row)
    if len(row['events']) != 1 or row['events'][0]['call'] != R.CALL:
        raise ValueError('room_requires_one_area_call')
    response = row['events'][0]['response']
    if not response.startswith('<tool_response>\n') or not response.endswith('\n</tool_response>'):
        raise ValueError('malformed_room_wrapper')
    value = R.parse_response(response[len('<tool_response>\n'):-len('\n</tool_response>')])
    if value['min_frames'] != 1:
        raise ValueError('room_training_requires_sensor')
    answer = f"{value['area_m2']:.2f}"
    if row['answer'] != answer or row['answer_content'] != answer or not agrees(answer, row['gt_answer']):
        raise ValueError('room_answer_disagrees_computation')
    expected = ('<think>\nI will project the depth points onto the floor and measure their covered area.\n'
                + R.CALL + '\n' + response
                + f'\nThe covered floor area is {answer} square meters.\n</think>\n<answer>{answer}</answer>')
    if row['suffix'] != expected:
        raise ValueError('room_prose_or_answer_mismatch')
    return value
