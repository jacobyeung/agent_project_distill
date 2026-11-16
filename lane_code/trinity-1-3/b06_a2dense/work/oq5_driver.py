import json,glob,tarfile,gzip,io
I='/project/community/jjyeung/distill/okit/in/cr/'
def peek(name,src,n=1):
    s=Store(src); print('==',name,'tables',{k:v[1][:120] for k,v in s.tables().items()})
    for k,(rid,vals) in enumerate(s.rows('rows')):
        r=json.loads(vals[1]); 
        si=r.get('student_input',{})
        print(' keys',sorted(r.keys())); print(' si', json.dumps({a:(b if not isinstance(b,list) or len(b)<5 else [len(b),b[:3]]) for a,b in si.items()})[:2500])
        print(' rest', json.dumps({a:b for a,b in r.items() if a not in ('student_input','target')})[:1500])
        if k+1>=n: break
peek('a2v3', SplitFile(sorted(glob.glob(I+'ca8d40ab9b55.p0[0-9]'))))
off,size=tar_member(I+'rt_b8b60bcef027.tar','ap/5e1d07a4/f/h/r16/rows.sqlite')
peek('r16', SplitFile([I+'rt_b8b60bcef027.tar'],off,size))
with tarfile.open(I+'rt_b8b60bcef027.tar') as t: print('r16 receipt', t.extractfile('ap/5e1d07a4/f/h/r16/receipt.json').read()[:2500].decode())
print('a2v3 receipt', open(I+'c855379fcefb.p00').read()[:3000])
print('a3v2 receipt', open(I+'66b8c94c7ee3.p00').read()[:1500])
