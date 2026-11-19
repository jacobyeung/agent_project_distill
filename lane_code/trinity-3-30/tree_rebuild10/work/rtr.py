import json,glob,os,re,statistics as st
T='/scratch/jjyeung/orch_n30/tree_rebuild10_w/w16b/work/build16/proofs/traces'
for f in sorted(glob.glob(T+'/*.jsonl')):
    R=[json.loads(l) for l in open(f)]
    if not R: print('##',os.path.basename(f),'EMPTY');continue
    L=[len(r['trace']) for r in R]; ans=[r['target_text'].split('</think>')[-1].strip() for r in R]
    tool=sum(1 for r in R if re.search(r'<(tool|call|head)|\[(pose|depth|tool)',r['target_text'],re.I))
    nums_unsup=0
    for r,a in zip(R,ans):
        t=r['trace']; 
        if re.fullmatch(r'-?[\d.]+',a or '') and a not in t and not re.search(r'[=×x*/+-]',t): nums_unsup+=1
    print('##',os.path.basename(f)[:-6],'n',len(R),'trace_len min/med/max',min(L),int(st.median(L)),max(L),'toolmarks',tool,'numeric_answer_not_in_trace_no_arith',nums_unsup,'uniq_traces',len(set(r['trace'] for r in R)))
    for r in R[:2]:
        print('  Q:',r['prompt'][-160:].replace('\n',' '))
        print('  T:',r['target_text'][:700].replace('\n',' | '))
