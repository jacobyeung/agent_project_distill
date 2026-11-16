"""Bind dev wording to the reference programs without using trace measurements."""
import re
import pool_common as PC
import tplib as T

TYPES = {'object_abs_distance','object_size_estimation','object_counting',
         'object_rel_distance','object_rel_direction_easy','object_rel_direction_medium',
         'object_rel_direction_hard','room_size_estimation'}

def bind(row):
    t = row['question_type']
    s = row['question']
    trace = row.get('source_target','')
    names = []
    if t == 'object_counting':
        m = re.search(r'Step 1: find every (.+?) that appears in the video\.',trace)
        if not m: raise ValueError('Missing counting operand')
        names = [m[1]]
        text = f'How many {names[0]}(s) are in this room?'
    elif t == 'object_abs_distance':
        m = re.search(r'Step 1: find the (.+?) and the (.+?)\.\n',trace)
        if not m: raise ValueError('Missing distance operands')
        names = list(m.groups())
        text = f'What is the distance between the {names[0]} and the {names[1]} (in meters)?'
    elif t == 'object_size_estimation':
        m = re.search(r'Step 1: find the (.+?)\.\n',trace)
        if not m: raise ValueError('Missing size operand')
        names = [m[1]]
        text = f'What is the maximum dimension (length, width, or height) of the {names[0]}, measured in centimeters?'
    elif t.startswith('object_rel_direction'):
        m = re.search(r'Step 1: locate the centres of the (.+?), the (.+?) and the (.+?)\.\n',trace)
        if not m: raise ValueError('Missing direction operands')
        names = list(m.groups())
        text = f'If I am standing by the {names[0]} and facing the {names[1]}, is the {names[2]} to my left or right?'
    elif t == 'object_rel_distance':
        m = re.search(r'Step 1: find the (.+?) and each candidate\.\n',trace)
        if not m: raise ValueError('Missing relative distance target')
        names = [m[1]]
        cands = list(T.option_texts(row['options']).values())
        names += cands
        text = f'Considering closest points, which of these objects ({", ".join(cands)}) is the closest to the {names[0]}?'
    elif t == 'room_size_estimation':
        text = 'What is the size of this room (in square meters)?'
    else:
        raise ValueError('Unsupported reference program: '+t)
    # Operand extraction uses only the naming sentence. Never consume trace distances/angles/answers.
    for name in names:
        if name.casefold() not in s.casefold() and name not in T.option_texts(row['options']).values():
            raise ValueError('Trace operand absent from prompt: '+name)
    unit = PC.question_unit(s)
    if t in ('object_abs_distance','object_size_estimation') and unit not in PC.TO_CM:
        raise ValueError('Unknown length unit')
    if t=='room_size_estimation' and unit not in PC.TO_SQM:
        raise ValueError('Unknown area unit')
    return dict(question=text, question_type=t, options=row['options'], id=row['qid']), names, unit

def convert(pred, t, unit):
    if pred is None: return None
    if t=='object_abs_distance': return float(pred)*100/PC.TO_CM[unit]
    if t=='object_size_estimation': return float(pred)/PC.TO_CM[unit]
    if t=='room_size_estimation': return float(pred)/PC.TO_SQM[unit]
    return pred
