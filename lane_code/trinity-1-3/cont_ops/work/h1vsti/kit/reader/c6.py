"""Flag affirmative camera-as-object citations in generated model traces.

The regex recognizes explicit lexical forms, not arbitrary coreference or
quoted discussion of a bad trace. Apply it to the generated trace only.
"""
import re
FRAME=r'(?:\d+|[NM])\b'
RULE=(r'(?ix)\b(?:the\s+)?camera\b\s*[,:(-]?\s*'
 r'(?:(?:(?:is|was|can\s+be)\s+)?'
 r'(?:(?:first\s+(?:seen|appears?|appeared|visible|located|observed))|seen|located|visible|observed)\s+(?:in|at)\s+frame\s+'+FRAME+
 r'|(?:is|was)\s+(?:in|at)\s+frame\s+'+FRAME+r')'
 r'|\bseen\s*:\s*(?:the\s+)?camera\s+(?:in|at)\s+frame\s+'+FRAME)
_PATTERN=re.compile(RULE)
def flag(trace: str) -> bool:
 """Return True for an explicit affirmative camera-as-object citation."""
 return bool(_PATTERN.search(trace))
