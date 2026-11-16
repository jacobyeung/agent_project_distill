exec(open('load.py').read())
from collections import Counter,defaultdict
out=[]
def P(*a):
    s=' '.join(str(x) for x in a); print(s); out.append(s)
for qt in REL:
    ks=[k for k in nat if nat[k]['question_type']==qt]
    by=defaultdict(lambda:[0,0,0,0])
    for k in ks:
        q=T[k]['question']; m=re.search(r'frame (\d+) of (\d+)',q); f,n=int(m.group(1)),int(m.group(2))
        b=('N=32' if n==32 else 'N<32', 'early' if f<=n/3 else ('mid' if f<=2*n/3 else 'late'))
        for key in (b[0],b[1]):
            by[key][0]+=1; by[key][1]+=nat[k]['score']; by[key][2]+=cmp['f17'][k]['official_fuzzy_score']; by[key][3]+=cmp['p1m200'][k]['official_fuzzy_score']
    P(qt,{k:f"n{v[0]} nat{100*v[1]/v[0]:.0f} f17{100*v[2]/v[0]:.0f} p1{100*v[3]/v[0]:.0f}" for k,v in sorted(by.items())})
    sc=Counter(S[k]['scene'] for k in ks); P('  scenes',len(sc),'max items/scene',max(sc.values()))
    # wording variants
    P('  wording variants',len(Counter(re.sub(r'\(.*?\)|frame \d+ of \d+|relative to [a-z ]+,|is [a-z ]+ (to the|\[)','X',T[k]['question']) for k in ks)))
# nf: accuracy by GT
open('a4.txt','w').write('\n'.join(out))
