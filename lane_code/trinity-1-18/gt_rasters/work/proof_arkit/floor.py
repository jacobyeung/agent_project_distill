exec(open('fit3.py').read().split("from collections")[0])
allz=[]; 
for f in frames:
    P,valid=src_world2(f,0.5,False); allz.append(P[valid,2])
z=np.concatenate(allz)
print('box floor',floor)
for q in [0.1,0.5,1,2,5,10]: print(q, np.percentile(z,q))
# exact threshold bracket per frame
for f in frames[:12]:
    P,valid=src_world2(f,0.5,False); a=assign(P,valid,0.03,-1.0).reshape(192,256)[np.ix_(yi,xi)]
    Pz=P[:,2].reshape(192,256)[np.ix_(yi,xi)]
    cand=(a>=0)
    inc=cand&(I[f]>=0); exc=cand&(I[f]<0)&(Pz<floor+0.05)
    lo=Pz[exc].max() if exc.any() else np.nan; hi=Pz[inc].min() if inc.any() else np.nan
    print(f,'excluded max z-floor %.5f  included min z-floor %.5f'%(lo-floor,hi-floor))
