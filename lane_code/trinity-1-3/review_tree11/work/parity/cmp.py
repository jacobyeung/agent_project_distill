import json,collections,sys
a=json.load(open(sys.argv[1]));b=json.load(open(sys.argv[2]))
kinds=collections.Counter();diff=0;ex=[];err=collections.Counter()
for x,y in zip(a,b):
    assert x['seed']==y['seed'] and x['epoch']==y['epoch']
    for (c1,t1),(c2,t2) in zip(x['res'],y['res']):
        assert c1==c2; kinds[c1.split()[0][1:]]+=1
        if 'invalid own depth' in t1: err['b9f_invalid_depth']+=1
        if t1!=t2: diff+=1; ex.append((x['seed'],c1,t1,t2))
print(dict(kinds),sum(kinds.values()),'diff',diff,dict(err),ex[:3])
