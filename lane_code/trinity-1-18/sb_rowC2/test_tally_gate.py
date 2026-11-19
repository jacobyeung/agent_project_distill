"""Adversarial checks for the standalone tally grammar, without changing N."""
import copy,json,pathlib,random
from tally_gate import validate
from novelty import Filter
from build_rows import levenshtein

def exercise():
 r={'question_type':'relative_count','answer':'B','student_input':{'question':'Compare "chair" and "table".','options':['A. fewer','B. more','C. equal number']},'target':'<think>\nTally new instances at their first sampled frame:\nchair: frame 1: 2; frame 7: 1 -> 3.\ntable: frame 5: 1 -> 1.\n3 > 1.\n</think>\n\nB'}
 assert validate(r)['totals']==[3,1]
 substitutions={
 'duplicate_frame':('frame 7: 1','frame 1: 1'),
 'descending_frame':('frame 1: 2; frame 7: 1','frame 7: 1; frame 1: 2'),
 'frame_zero':('frame 1: 2','frame 0: 2'),
 'frame_33':('frame 7: 1','frame 33: 1'),
 'zero_new_count':('frame 7: 1','frame 7: 0'),
 'negative_new_count':('frame 7: 1','frame 7: -1'),
 'wrong_sum':('-> 3.','-> 4.'),
 'missing_category':('table: frame 5','desk: frame 5'),
 'wrong_comparison':('3 > 1.','3 < 1.'),
 'wrong_operand':('3 > 1.','2 > 1.'),
 'letter_restated_in_trace':('3 > 1.','B. 3 > 1.'),
 'unclosed_think':('</think>',''),
 }
 refused=[]
 for name,(old,new) in substitutions.items():
  x=copy.deepcopy(r);x['target']=x['target'].replace(old,new)
  try:validate(x)
  except ValueError:refused.append(name)
  else:raise AssertionError(name)
 x=copy.deepcopy(r);x['answer']='A';x['target']=x['target'].removesuffix('B')+'A'
 try:validate(x)
 except ValueError:refused.append('wrong_final_option')
 else:raise AssertionError('wrong_final_option')
 x=copy.deepcopy(r);x['student_input']['options']=['A. more','A. fewer','C. equal number']
 try:validate(x)
 except ValueError:refused.append('duplicate_option')
 else:raise AssertionError('duplicate_option')
 # Actual equality and each valid limit remain accepted.
 x=copy.deepcopy(r);x['answer']='C';x['target']=x['target'].replace('table: frame 5: 1 -> 1.','table: frame 32: 3 -> 3.').replace('3 > 1.','3 = 3.').removesuffix('B')+'C';assert validate(x)['relation']=='equal number'
 rng=random.Random(73);strings=['']+[''.join(rng.choices('abcé',k=rng.randrange(1,100))) for _ in range(200)]
 f=Filter(strings);queries=strings+[''.join(rng.choices('abcé',k=rng.randrange(1,100))) for _ in range(200)]
 for q in queries:
  expected=next((i for i,s in enumerate(strings) if levenshtein(q,s)<=max(len(q),len(s))/4),-1)
  assert f.match(q)==expected
 return {'negative_tally_mutations':refused,'positive_tally_cases':2,'native_filter_reference_crosschecks':len(queries)}
if __name__=='__main__':print(json.dumps(exercise(),indent=2))
