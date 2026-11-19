"""Evaluate frozen name priors on dev-S1 after packet selection; no model output."""
from common import *
from priors import records,fitted
import collections
PATTERNS=[
 r'Are (.+?)\(s\) found in greater numbers than, lesser numbers than, or equal numbers to (.+?)\(s\) here\?',
 r'Are (.+?)\(s\) more numerous than, less numerous than, or equal in number to (.+?)\(s\) in this room\?',
 r'Are there more (.+?)\(s\), fewer \1\(s\), or the same number as (.+?)\(s\) in this space\?',
 r'Are there more, fewer, or the same number of (.+?)\(s\) as there are (.+?)\(s\) inside this room\?',
 r'Do we have more, fewer, or the same number of (.+?)\(s\) as (.+?)\(s\) in this room\?',
 r'Do you find more, fewer, or the same number of (.+?)\(s\) compared with (.+?)\(s\) here\?',
 r'Does this room contain more, fewer, or an equal number of (.+?)\(s\) compared to (.+?)\(s\)\?',
 r'In comparison with (.+?)\(s\), are there more, fewer, or an equal number of (.+?)\(s\) in this room\?',
 r'In terms of quantity, are there more, fewer, or the same number of (.+?)\(s\) as (.+?)\(s\) present here\?',
 r'In this room, are there more, fewer, or the same number of (.+?)\(s\) relative to (.+?)\(s\)\?',
 r'In this room, do (.+?)\(s\) outnumber, are outnumbered by, or equal the number of (.+?)\(s\)\?',
 r'Is the count of (.+?)\(s\) higher than, lower than, or equal to the count of (.+?)\(s\) in this room\?',
 r'Is the number of (.+?)\(s\) greater than, less than, or equal to the number of (.+?)\(s\) in this room\?',
 r'Within this room, is the quantity of (.+?)\(s\) greater than, less than, or equal to (.+?)\(s\)\?'
]
def parse(r):
 matches=[(i,re.fullmatch(p,r['question'])) for i,p in enumerate(PATTERNS)];matches=[(i,m) for i,m in matches if m]
 if len(matches)!=1:raise ValueError('MISSING unambiguous category parser for '+r['id'])
 i,m=matches[0];a,b=m.groups()
 if i==7:a,b=b,a
 opts={o[0]:o[3:] for o in r['options']};gt=opts[r['ground_truth']]
 assert gt in ['more','fewer','equal number']
 return dict(qid=r['id'],a=a,b=b,y='tie' if gt=='equal number' else a if gt=='more' else b,relation=gt,template=i)

def predict(train,dev):
 sums,n,pairs=fitted(records(train));counts=collections.defaultdict(collections.Counter);items=[];missing=collections.Counter()
 for r in dev:
  a,b,y=r['a'],r['b'],r['y'];item=dict(r)
  if not n[a] or not n[b]:
   item['mean_prediction']='MISSING';item['missing_category_means']=[c for c in (a,b) if not n[c]]
   for c in item['missing_category_means']:missing[c]+=1
  else:
   delta=sums[a]*n[b]-sums[b]*n[a];pred=a if delta>0 else b if delta<0 else 'tie';item['mean_prediction']=pred
   counts['mean_three_way']['evaluated']+=1;counts['mean_three_way']['correct']+=pred==y
   if y!='tie':
    if delta==0:counts['mean_unequal']['equal_mean_abstentions']+=1
    else:counts['mean_unequal']['evaluated']+=1;counts['mean_unequal']['correct']+=pred==y
  c=pairs[tuple(sorted((a,b)))]
  if not c:item['pair_prediction']='MISSING'
  else:
   tied=sorted(k for k,v in c.items() if v==max(c.values()));pred=tied[0];item['pair_prediction']=pred;item['pair_vote_ties']=tied
   counts['pair_majority']['evaluated']+=1;counts['pair_majority']['correct']+=pred==y;counts['pair_majority']['tie_correct_upper']+=y in tied
  items.append(item)
 for key,c in counts.items():
  total=sum(r['y']!='tie' for r in dev) if key=='mean_unequal' else len(dev)
  c['eligible_items']=total;c['missing_or_abstained']=total-c['evaluated'];c['accuracy']=c['correct']/c['evaluated'] if c['evaluated'] else None;c['correct_over_all_eligible']=c['correct']/total
  if key=='pair_majority':c['accuracy_tie_upper']=c['tie_correct_upper']/c['evaluated'] if c['evaluated'] else None
 return dict(metrics={k:dict(c) for k,c in counts.items()},missing_category_means=dict(missing),items=items)

def main():
 build=load(ROOT/'out/BUILD.json');packet=list(rows(ROOT/'out/relative_count.jsonl'));assert PINS[str(ROOT/'out/relative_count.jsonl')]==build['output']['sha256']
 corpus=load(BASE/'in/WORDING_CORPUS.json');devfile=next(p for p in corpus['file_question_counts'] if p.endswith('/legs1_reads/work/vendor/r3/TASKS.jsonl'))
 devrows=[r for r in rows(devfile) if r.get('question_type',r.get('type'))=='relative_count'];assert len(devrows)==139 and PINS[devfile]==corpus['input_sha256'][devfile]
 dev=[parse(r) for r in devrows];frozen=predict(packet,dev)
 old=list(rows(ROOT.parent/'relcnt/out/relative_count.jsonl'));baseline=predict(old,dev)
 # A separate within-dev pair LOO diagnostic needs only comparison labels, not missing per-category counts.
 pair=collections.defaultdict(collections.Counter)
 for r in dev:pair[tuple(sorted((r['a'],r['b'])))][r['y']]+=1
 correct=upper=covered=ties=0
 for r in dev:
  c=pair[tuple(sorted((r['a'],r['b'])))].copy();c[r['y']]-=1;c=+c
  if not c:continue
  labels=sorted(k for k,v in c.items() if v==max(c.values()));covered+=1;correct+=labels[0]==r['y'];upper+=r['y'] in labels;ties+=len(labels)>1
 code_pins()
 result=dict(status='DIAGNOSTIC_ONLY',input_sha256=dict(PINS),command='bash code/run.sh code/dev_diagnostic.py',dev_items=139,parsed_items=len(dev),label_source='ground_truth with this item\'s displayed options',selection_dependency=False,protocol='Selection is complete before reading dev-S1. The exact category-mean and pair-winner estimators are fitted to packet counts, then frozen for held-out dev prediction. No dev row enters these fits, so leave-one-out subtraction is unnecessary. Categories are literal question spans; no synonym mapping or invented counts.',selected_packet=frozen,source_packet=baseline,within_dev_pair_loo=dict(evaluated=covered,correct=correct,accuracy=correct/covered,accuracy_tie_upper=upper/covered,majority_ties=ties,missing_pairs=139-covered),within_dev_mean_loo=dict(status='MISSING',required_input='Per-category counts for each of the 139 relative-count items',expected_location=devfile+' :: per-category counts (not present in these rows)',explanation='Comparison labels do not determine category counts. Frozen packet-trained means are reported instead.'),model_outputs=False)
 dump(ROOT/'out/DEV_S1_DIAGNOSTIC.json',result)
 status(f'The frozen name-prior diagnostic covers all 139 dev-S1 items with explicit MISSING predictions where training category means or pair counts are absent. It selects no packet rows and runs no model. The packet has {len(packet)} rows; remaining validation and review results are recorded in out/.')
 print(json.dumps(dict(items=139,selected=frozen['metrics'],source=baseline['metrics'],within_dev_pair_loo=result['within_dev_pair_loo'])),flush=True)
if __name__=='__main__':main()
