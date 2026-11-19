"""Transparent category-mean and unordered-pair leave-one-row-out baselines."""
import collections

def records(rows):
 return [dict(qid=r['qid'],a=(m:=r['provenance']['relative_count'])['a'],b=m['b'],na=m['count_a'],nb=m['count_b'],relation=m['relation']) for r in rows]

def fitted(data):
 sums=collections.Counter();n=collections.Counter();pairs=collections.defaultdict(collections.Counter)
 for r in data:
  a,b=r['a'],r['b'];sums[a]+=r['na'];sums[b]+=r['nb'];n[a]+=1;n[b]+=1
  pairs[tuple(sorted((a,b)))]['tie' if r['na']==r['nb'] else a if r['na']>r['nb'] else b]+=1
 return sums,n,pairs

def evaluate(data):
 sums,n,pairs=fitted(data);mean=collections.Counter();pair=collections.Counter();mean_all=collections.Counter();cat=collections.defaultdict(collections.Counter);by_template={}
 for r in data:
  a,b=r['a'],r['b'];y='tie' if r['na']==r['nb'] else a if r['na']>r['nb'] else b
  if y!='tie':
   cat[y]['larger']+=1;cat[b if y==a else a]['smaller']+=1
  if n[a]<=1 or n[b]<=1:
   mean_all['unseen_category']+=1
   if y!='tie':mean['unseen_category']+=1
  else:
   # Integer cross multiplication avoids a floating-point equality convention.
   delta=(sums[a]-r['na'])*(n[b]-1)-(sums[b]-r['nb'])*(n[a]-1)
   pred=a if delta>0 else b if delta<0 else 'tie'
   mean_all['evaluated']+=1;mean_all['correct']+=pred==y
   if y!='tie':
    if delta==0:mean['equal_mean_abstentions']+=1
    else:mean['evaluated']+=1;mean['correct']+=pred==y
  c=pairs[tuple(sorted((a,b)))].copy();c[y]-=1;c=+c
  if not c:pair['unseen_pair']+=1;continue
  maxvote=max(c.values());tied=sorted(k for k,v in c.items() if v==maxvote)
  pair['evaluated']+=1;pair['correct']+=tied[0]==y
  pair['majority_ties']+=len(tied)>1;pair['tie_correct_upper']+=y in tied
 def metric(c,total):
  d=dict(c);d['eligible_items']=total;d['accuracy']=c['correct']/c['evaluated'] if c['evaluated'] else None;d['coverage']=c['evaluated']/total if total else 0
  return d
 unequal=sum(r['na']!=r['nb'] for r in data)
 out=dict(mean_unequal=metric(mean,unequal),mean_three_way=metric(mean_all,len(data)),pair_majority=metric(pair,len(data)),categories={k:dict(v,larger_fraction=v['larger']/(v['larger']+v['smaller']),majority_fraction=max(v.values())/sum(v.values()),larger_to_smaller=v['larger']/v['smaller'] if v['smaller'] else None) for k,v in sorted(cat.items())})
 out['pair_majority']['accuracy_tie_upper']=pair['tie_correct_upper']/pair['evaluated'] if pair['evaluated'] else None
 out['definitions']={'mean_unequal':'Remove the evaluated row from both category count sums and occurrence counts; compare the remaining category means. Score only unequal GT rows with both categories represented elsewhere and unequal remaining means. Report abstentions separately.','pair_majority':'Remove the evaluated row from the unordered category-pair winner/tie counts; choose the most common label. Break vote ties lexicographically, and also report the conservative upper accuracy that credits every tied true label.','weighting':'Each delivered row contributes one observation, including repeats under different wordings. No model is run.'}
 return out
