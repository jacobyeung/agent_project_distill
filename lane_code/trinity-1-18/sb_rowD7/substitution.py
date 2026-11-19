"""Change one facing clause, preserving every other source question character.

The codeA/build_away.py pattern uses one anchored re.subn substitution and asserts
exactly one edit. Its delivered rule handles away-to-opposite. These explicit
rules extend that pattern to the toward phrases accepted by the reviewer mask.
Unmatched or ambiguous clauses are refused, never regenerated from a template.
"""
import re
PATTERN=r'\b(facing toward|facing|looking at|looking toward|look toward|face toward|face)\b(?= the {heading}(?:\b|[.,?!]))'
MASK=r'\b(facing away from|turned away from|with my back to|face away from|face toward|facing toward|facing|looking at|looking toward|look toward|toward|face|ahead)\b'
def masked(question,names):
 for name in sorted(set(names),key=len,reverse=True):question=question.replace(name,'<N>')
 return re.sub(MASK,'<C>',question)
def rewrite_question(question,names):
 x,y,z=names
 pat=PATTERN.format(heading=re.escape(y));matches=list(re.finditer(pat,question))
 if len(matches)!=1:raise ValueError('clause_substitution_not_unique')
 m=matches[0];old=m[0];new='face away from' if old in ('face','face toward','look toward') else 'facing away from'
 rewritten,n=re.subn(pat,new,question,count=1);assert n==1
 assert masked(question,names)==masked(rewritten,names),'reviewer_mask_differs'
 return rewritten,dict(start=m.start(),end=m.end(),source_clause=old,new_clause=new,rule='single_clause_substitution')
