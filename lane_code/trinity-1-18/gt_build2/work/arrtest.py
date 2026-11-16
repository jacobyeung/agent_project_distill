import numpy as np, io, hashlib, json, sys
C={p['canonical']:(p['gt']['expected_sha256'],p['gt']['bytes']) for p in json.load(open('/scratch/jjyeung/orch_cd/k1_build/work/kit_k1a/out/CAPTURES.json'))['pilot']}
def save(a): b=io.BytesIO(); np.savez_compressed(b,**a); return b.getvalue()
for c in sys.argv[1:]:
    z=np.load(f'/scratch/jjyeung/orch_n30/gt_build2/out/variants/R1/{c}.npz'); A={k:z[k] for k in z.files}
    pin,pb=C['arkitscenes/'+c]
    miss=np.nonzero(~A['depth'].reshape(32,-1).any(1))[0]
    tests={}
    def T(name,**ch):
        a=dict(A); a.update(ch); d=save(a); tests[name]=(len(d)-pb, hashlib.sha256(d).hexdigest()==pin)
    T('base')
    e=A['c2w'].copy(); e[miss]=np.eye(4); T('c2w_eye_missing',c2w=e)
    e=A['c2w'].copy(); e[miss]=0; T('c2w_zero_missing',c2w=e)
    e=A['c2w'].copy()
    for m in miss: e[m]=e[m-1] if m>0 else e[m+1]
    T('c2w_prev_missing',c2w=e)
    k=A['K_frames'].copy(); k[miss]=0; T('K_zero_missing',K_frames=k)
    v=A['valid'].copy(); v[miss]=False; T('valid_false_missing',valid=v)
    print(c,'missing',miss.tolist(),tests)
