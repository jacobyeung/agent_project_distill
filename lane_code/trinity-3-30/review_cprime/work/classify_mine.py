# Independent classifier (review_cprime). Rule on the target text only:
#  LIST  := the <think> block contains an enumerated first-seen entry ": frame <int>" (optionally "(left|middle|right)")
#  TOTAL := the <think> block contains an "add them" summation step  (cross-checked against question naming >1 "(s)" category)
#  PROC  := single "Step 1:" line, no integer other than the step number in <think>, no "frame <int>" token
import json,collections,re,sys
LIST=re.compile(r':\s*frame \d+(\s*\((left|middle|right)\))?(\s*;\s*frame \d+(\s*\((left|middle|right)\))?)*\s*\.')
ADD=re.compile(r'Step \d+: add them:')
def think(t):
    m=re.search(r'<think>(.*?)</think>',t,re.S); return m.group(1) if m else None
def classify(r):
    th=think(r['target'])
    if th is None: return 'NO_THINK'
    lst=bool(LIST.search(th)); tot=bool(ADD.search(th))
    steps=re.findall(r'^Step (\d+):',th,re.M)
    nums=re.findall(r'\d+',re.sub(r'^Step \d+:','',th,flags=re.M))
    proc=(steps==['1'] and not nums and not re.search(r'frame \d',th))
    return ('TOTAL_' if tot else 'SINGLE_')+('LIST' if lst else 'PROC' if proc else 'OTHER')
def qmulti(q): return len(re.findall(r'\(s\)',q or ''))>1
if __name__=='__main__':
    rows=[json.loads(l) for l in open('all_rows_compact.jsonl')]
    qidc=collections.Counter(r['qid'] for r in rows)
    print('store rows',len(rows),'dup qids',sum(1 for v in qidc.values() if v>1))
    by={r['qid']:r for r in rows}
    B1=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/r1_ops6/cf/final_evidence/COUNT_FIX_REMOVE_B1.jsonl')]
    N=[json.loads(l) for l in open('/scratch/jjyeung/orch_n30/r1_ops6/snapm/snap_9dd2fbb7/out/records/n.json')]
    b1k={x['row_key'] for x in B1}; nk={x['row_key'] for x in N}
    out={}
    # (a)
    miss=[x for x in B1 if x['row_key'] not in by]
    mism=[x for x in B1 if x['row_key'] in by and (by[x['row_key']]['qt']!=x['question_type'] or by[x['row_key']]['pool']!=x['pool'] or f"{by[x['row_key']]['ds']}/{by[x['row_key']]['scene']}"!=x['scene'])]
    out['a']=dict(B1_lines=len(B1),B1_unique=len(b1k),missing_in_store=len(miss),field_mismatch=len(mism),
                  store_qt=dict(collections.Counter(by[k]['qt'] for k in b1k if k in by)))
    cr=[r for r in rows if r['qt']=='object_counting']
    cls={r['qid']:classify(r) for r in cr}
    out['class_all_counting']=dict(collections.Counter(cls.values()))
    out['class_x_pool']={f"{p}|{c}":v for (p,c),v in collections.Counter((r['pool'],cls[r['qid']]) for r in cr).items()}
    # totals cross-check
    out['total_vs_qmulti_disagree']=sum(1 for r in cr if cls[r['qid']].startswith('TOTAL')!=qmulti(r['q']))
    out['totalflag_counts']=dict(collections.Counter(cls[r['qid']].split('_')[0] for r in cr))
    mine={q for q,c in cls.items() if c.endswith('LIST') or c.startswith('TOTAL')}
    out['b']=dict(mine=len(mine),B1=len(b1k),in_mine_not_B1=len(mine-b1k),in_B1_not_mine=len(b1k-mine),
                  in_mine_not_B1_and_in_n=len((mine-b1k)&nk),in_mine_not_B1_not_n=len((mine-b1k)-nk))
    out['b_disagree_rows']=[dict(qid=q,pool=by[q]['pool'],cls=cls.get(q),in_B1=q in b1k,in_n=q in nk) for q in sorted(mine^b1k)][:20]
    out['b_B1_class']=dict(collections.Counter(cls.get(k,'NOT_COUNTING') for k in b1k))
    rem=[r for r in cr if r['qid'] not in b1k and r['qid'] not in nk]
    out['c']=dict(remaining_counting=len(rem),remaining_class=dict(collections.Counter(cls[r['qid']] for r in rem)),
                  remaining_pools=dict(collections.Counter(r['pool'] for r in rem)),
                  remaining_with_frame_token=sum(1 for r in rem if 'frame' in (think(r['target']) or '')),
                  remaining_with_semicolon=sum(1 for r in rem if ';' in (think(r['target']) or '')),
                  remaining_target_template=dict(collections.Counter(re.sub(r'(distinct( instances of)?|each distinct) .*?(;|,)',r'\1 X\3',think(r['target']).strip()) for r in rem).most_common(10)))
    out['d']=dict(n_rows=len(nk),B1_and_n=len(b1k&nk),union=len(b1k|nk),n_counting=sum(1 for k in nk if by.get(k,{}).get('qt')=='object_counting'),n_missing_in_store=sum(1 for k in nk if k not in by))
    out['e']=dict(B1_non_counting=sum(1 for k in b1k if by[k]['qt']!='object_counting'),
                  B1_categories=dict(collections.Counter(by[k]['cat'] for k in b1k)))
    json.dump(out,open('../out/CLASSIFY_MINE.json','w'),indent=1)
    json.dump({q:c for q,c in cls.items()},open('../out/MY_COUNTING_CLASSES.json','w'))
    print(json.dumps(out,indent=1))
