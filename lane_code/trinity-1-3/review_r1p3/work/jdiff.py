import json,sys
def walk(a,b,p=''):
    if isinstance(a,dict) and isinstance(b,dict):
        for k in sorted(set(a)|set(b)):
            if k not in a: print('+',p+'/'+k,json.dumps(b[k])[:200])
            elif k not in b: print('-',p+'/'+k,json.dumps(a[k])[:200])
            else: walk(a[k],b[k],p+'/'+k)
    elif a!=b: print('~',p,json.dumps(a)[:150],'->',json.dumps(b)[:150])
walk(json.load(open(sys.argv[1])),json.load(open(sys.argv[2])))
