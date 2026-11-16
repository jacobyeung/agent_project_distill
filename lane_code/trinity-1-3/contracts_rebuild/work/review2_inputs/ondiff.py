import json,sys,difflib,re,collections
R=sys.argv[1]
def load(a):
    d=json.load(open(f'{R}/{a}.json'))['results']+json.load(open(f'{R}/supplement_{a}.json'))['results']
    return {(r['family'],r['variant']):r for r in d}
B,O,N=load('base'),load('off'),load('on')
# OFF parity on row content
bad=[k for k in B if json.dumps(B[k].get('row'),sort_keys=False)!=json.dumps(O[k].get('row'),sort_keys=False) or B[k]['status']!=O[k]['status']]
print('off mismatches',bad)
cats=collections.Counter();examples=collections.defaultdict(list)
def text(r):
    row=r.get('row') or {}
    return row.get('target') or row.get('suffix') or ''
for k in sorted(B):
    if B[k]['status']!='rendered':continue
    a,b=text(B[k]),text(N[k])
    if a==b:continue
    al,bl=a.split('\n'),b.split('\n')
    for op in difflib.SequenceMatcher(None,al,bl).get_opcodes():
        if op[0]=='equal':continue
        old='\n'.join(al[op[1]:op[2]]);new='\n'.join(bl[op[3]:op[4]])
        # normalise numbers
        key=(re.sub(r'-?\d+\.\d+|-?\d+','#',old)[:160],re.sub(r'-?\d+\.\d+|-?\d+','#',new)[:160])
        cats[key]+=1
        if len(examples[key])<2: examples[key].append((k,old[:300],new[:300]))
for key,c in cats.most_common():
    print('====',c,'\n OLD:',key[0],'\n NEW:',key[1])
    for e in examples[key]: print('  ex',e[0]); print('   -',e[1].replace('\n','|')); print('   +',e[2].replace('\n','|'))
