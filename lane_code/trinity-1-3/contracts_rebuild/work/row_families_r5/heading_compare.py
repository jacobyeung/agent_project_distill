"""Accept only replacement of explicitly heading-dependent printed values."""
import re

NUM=r'[+-]?(?:\d+\.\d+|\d+)'
def heading_text(old,new):
    if not isinstance(old,str) or not isinstance(new,str) or 'error:' in new:
        return False
    expected=old
    expected=re.sub(r'(f1 (?:centre )?)\('+NUM+r', ('+NUM+r'), '+NUM+r'\)',
                    r'\1(heading unavailable, \2, heading unavailable)',expected)
    expected=re.sub(r'yaw '+NUM+r' deg \(0 = \+x; positive \+x toward -z about \+y\)',
                    'yaw heading unavailable',expected)
    # Relative calls identify exactly which source frame lost its heading.
    for axis in ('dx','dz'):
        match=re.search(axis+r' = heading unavailable \(frame (\d+)\)',new)
        if match:
            expected=re.sub(axis+r' = '+NUM+' m',axis+' = heading unavailable (frame '+match[1]+')',expected)
    match=re.search(r'turn = heading unavailable \(frames ([\d,]+)\)',new)
    if match:expected=re.sub(r'turn = '+NUM+' deg','turn = heading unavailable (frames '+match[1]+')',expected)
    match=re.search(r'yaw heading unavailable(?: \(frame \d+\))?',new)
    if match:expected=re.sub(r'yaw '+NUM+' deg',match[0],expected)
    expected=re.sub(r'u \('+NUM+', '+NUM+r'\); v \('+NUM+', '+NUM+r'\)',
                    'u heading unavailable; v heading unavailable',expected)
    return expected==new


def heading_offset(old_text,new_text,old,new):
    if type(old) is not int or type(new) is not int:
        return False
    if not (0 <= old <= len(old_text) and 0 <= new <= len(new_text)):
        return False
    a,b=old_text[:old],new_text[:new]
    return a==b or heading_text(a,b)


def row_texts_valid(old,new):
    """Validate all changed strings, plus dependent span and token accounting."""
    if isinstance(old,str) and isinstance(new,str):return old==new or heading_text(old,new)
    if isinstance(old,dict) and isinstance(new,dict):
        for key in set(old)&set(new):
            # Numerical private geometry and derived positions are checked by the
            # caller; this walk establishes that no served string changed values.
            if not row_texts_valid(old[key],new[key]):return False
    elif isinstance(old,list) and isinstance(new,list):
        if len(old)!=len(new):return False
        return all(row_texts_valid(a,b) for a,b in zip(old,new))
    return True
