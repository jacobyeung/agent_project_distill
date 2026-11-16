<!-- recovered by seal_plan: transcript=71f94277 line=33966 utc=2026-11-14T22:54:48.923Z kind=commands original_path=(bash command)  -->
S=/tmp/claude-25409/-scratch-jjyeung-orch-home-distill/71f94277-362e-467c-a4bc-ccc9ae6b87c8/scratchpad; B=/scratch/jjyeung/orch_cd/evalx/work/milestone; mkdir -p $S/p7diff/a $S/p7diff/b; /scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<EOF
import json,hashlib,tarfile,os,difflib
B='$B'; S='$S/p7diff'
o=json.load(open(B+'/native_package_s24_01/seal/FAMILY.json')); n=json.load(open(B+'/native_package_s24_02/seal/FAMILY.json'))
print('old',hashlib.sha256(open(B+'/native_package_s24_01/seal/FAMILY.json','rb').read()).hexdigest()[:16],'new',hashlib.sha256(open(B+'/native_package_s24_02/seal/FAMILY.json','rb').read()).hexdigest())
po,pn=o['code_pins'],n['code_pins']
ch=sorted(k for k in set(po)|set(pn) if po.get(k)!=pn.get(k))
print('changed code pins',len(ch))
for k in ch: print('  ',k.split('/milestone/')[-1], (po.get(k) or 'NEW')[:10],'->',(pn.get(k) or 'GONE')[:10])
def members(tarpath):
    out={}
    t=tarfile.open(tarpath)
    for m in t.getmembers():
        if m.isfile(): out[m.name]=t.extractfile(m).read()
    return out
ta=members(B+'/native_package_s24_01/packages/code.tar'); tb=members(B+'/native_package_s24_02/packages/code.tar')
print('archive b sha',hashlib.sha256(open(B+'/native_package_s24_02/packages/code.tar','rb').read()).hexdigest()[:16])
tot=0
with open(S+'/F1_F4.diff','w') as f:
    for name in sorted(set(ta)|set(tb)):
        a=ta.get(name,b''); b=tb.get(name,b'')
        if a==b: continue
        try: al=a.decode().splitlines(); bl=b.decode().splitlines()
        except Exception: print('binary change',name); continue
        d=list(difflib.unified_diff(al,bl,'a/'+name,'b/'+name,lineterm='',n=2))
        tot+=len(d); print('  diff',name.split('/milestone/')[-1],len(d),'lines')
        f.write('\n'.join(d)+'\n')
print('total diff lines',tot)
# assets/worker contract changes
def flat(d,p=''):
    out={}
    if isinstance(d,dict):
        for k,v in d.items(): out.update(flat(v,p+'/'+str(k)))
    elif isinstance(d,list):
        for i,v in enumerate(d): out.update(flat(v,p+'/'+str(i)))
    else: out[p]=d
    return out
fo,fn=flat(o),flat(n)
oth=[k for k in sorted(set(fo)|set(fn)) if fo.get(k)!=fn.get(k) and '/code_pins/' not in k and '/bootstrap_pins/' not in k and '/members/' not in k]
for k in oth[:30]: print('  other',k[-70:],'|',str(fo.get(k))[:22],'->',str(fn.get(k))[:22])
EOF