import sys; sys.path.insert(0,'.')
exec(open('probe.py').read().split("f=int")[0])
f,k=0,2
P=world(f); Ii=I[f].reshape(-1); valid=D[f].reshape(-1)>0
loc=(P-cen[k])@A[k].T; h=L[k]/2; lab=Ii==k
inside=(np.abs(loc)<=h+0.03).all(1)
oi=np.nonzero(valid&~lab&inside)[0]
print(len(oi))
for p in oi[::max(1,len(oi)//12)]:
    y,x=divmod(p,320); print(y,x,'d=%.3f'%D[f,y,x],'loc/h',np.round(loc[p]/h,3),'world',np.round(P[p],3))
li=np.nonzero(lab)[0]
for p in li[::len(li)//6]:
    y,x=divmod(p,320); print('LAB',y,x,'d=%.3f'%D[f,y,x],'loc/h',np.round(loc[p]/h,3),'world',np.round(P[p],3))
