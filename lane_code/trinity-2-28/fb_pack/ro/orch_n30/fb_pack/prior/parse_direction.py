"""Parse explicit question clauses, answer options and forward trace lines."""
import re

def parse(r):
 q=r['question'].casefold()
 # Restrict clause parsing to the first sentence, before answer alternatives and
 # explanatory Cartesian-plane wording. Away patterns have precedence.
 head=q.split('?',1)[0].split(', is ',1)[0]
 if re.search(r'\b(?:fac(?:e|ing)|look(?:ing)?|turn(?:ed|ing)?)\s+away\b|\b(?:with\s+)?my\s+back\s+(?:to|toward|towards)\b|\bfacing in the opposite direction\b',head):clause='away'
 elif re.search(r'\b(?:fac(?:e|ing)|look(?:ing)?|viewing|gazing at)\b|\b(?:oriented|directed|aiming|turned) toward(?:s)?\b|\bmy gaze fixed on\b|\bdirecting my view towards\b|\bnext to me and the .+ ahead\b|\bahead of (?:me|you)\b',head):clause='toward'
 else:clause='MISSING'
 difficulty=r['question_type'].rsplit('_',1)[-1]
 import json
 opts=json.loads(r['options_json']);answer=r['answer']
 if isinstance(opts,dict):label=opts.get(answer,'MISSING')
 else:
  found=[re.sub(r'^[A-Z][.)]\s*','',v).strip() for v in opts if isinstance(v,str) and re.match(r'^'+re.escape(answer)+r'[.)]\s*',v)]
  label=found[0] if len(found)==1 else 'MISSING'
 label=label.casefold().strip()
 side='back' if re.search(r'\b(?:back|behind)\b',label) else 'front' if re.search(r'\bfront\b',label) else 'other' if label!='missing' else 'MISSING'
 lines=r['target'].splitlines()
 forward=[s for s in lines if s.startswith(('Step 2:','Standing at ','If I stood at '))]
 if len(forward)!=1:
  relation='MISSING';line=' | '.join(forward)
 else:
  line=forward[0]
  # Ignore reference-object names. Match the explicit observer-relative phrase.
  front=bool(re.search(r'\bin front of me\b|\bahead of me\b',line,re.I))
  behind=bool(re.search(r'\bbehind me\b|\bin back of me\b',line,re.I))
  relation='front' if front and not behind else 'behind' if behind and not front else 'lateral' if re.search(r'\b(?:to|on|out to) my (?:left|right)\b',line,re.I) and not front and not behind else 'MISSING'
 return dict(clause=clause,difficulty=difficulty,forward_relation=relation,answer_label=label,answer_side=side,forward_line=line)
