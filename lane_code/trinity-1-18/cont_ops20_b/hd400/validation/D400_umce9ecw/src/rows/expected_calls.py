"""Expected route from question text and type alone; no answer or trace lookup."""
import re

CAMERA_TYPES=('camera_displacement','camera_movement_direction','camera_rotation')
ROUTED_TYPES=CAMERA_TYPES+('object_abs_distance',)


def expected_calls(question, question_type):
    if question_type in CAMERA_TYPES:
        m=re.search(r'between\s+frames?\s+(\d+)\s+(?:and|to|-)\s*(?:frame\s+)?(\d+)',question,re.I)
        if m is None:
            m=re.search(r'from\s+frame\s+(\d+)\s+to\s+frame\s+(\d+)',question,re.I)
        if m is None:
            raise ValueError('camera_question_missing_explicit_frame_pair')
        i,j=map(int,m.groups())
        if not 1<=i<=32 or not 1<=j<=32: raise ValueError('camera_frame_outside_1_32')
        return [f'<{"turn" if question_type=="camera_rotation" else "move"} from={i} to={j}>']
    if question_type=='object_abs_distance':
        # Native distance paraphrases retain the two names verbatim in the question.
        text=question.strip().rstrip('?.')
        text=re.sub(r'\s*\([^)]*\)\s*$', '', text)
        text=re.sub(r',?\s+(?:(?:expressed|measured)\s+)?in (?:meters?|centimeters?|millimeters?|feet|foot|inches)\s*$', '', text, flags=re.I)
        text=re.sub(r'\s+using their (?:closest|nearest) points,?\s*$', '', text, flags=re.I)
        text=re.sub(r'\s+are\s*$', '', text, flags=re.I)
        patterns=[
            r'(?:between|separating|separate) (?:the (?:nearest|closest) points of )?(?:the )?(.+?) and (?:the )?(.+)$',
            r'how far apart (?:are )?(?:the closest points of )?(?:the )?(.+?) and (?:the )?(.+)$',
            r'from (?:the (?:nearest|closest) point on )?(?:the )?(.+?) to (?:the (?:nearest|closest) point on )?(?:the )?(.+)$',
            r'(?:separation of|separating) (?:the )?(.+?) from (?:the )?(.+)$',
        ]
        m=next((m for pattern in patterns if (m:=re.search(pattern,text,re.I))),None)
        if m is None:
            raise ValueError('distance_question_missing_two_object_names')
        names=[x.strip() for x in m.groups()]
        if any(not n or any(c in n for c in '\n"<>') for n in names):
            raise ValueError('invalid_question_object_name')
        a,b=names
        return [f'<ground obj="{a}" mode="box">', f'<ground obj="{b}" mode="box">',
                f'<gap a="{a}" b="{b}" rule="box_grid_5cm">']
    return []


def actual_calls(row):
    raw=row.get('routing',row)
    if 'ground_record' in raw:
        return [e['call'] for e in raw['ground_record']['events']]
    return [e['token'].strip() for e in raw.get('events',[]) if e['kind'] in ('tool_call','ground_call')]
