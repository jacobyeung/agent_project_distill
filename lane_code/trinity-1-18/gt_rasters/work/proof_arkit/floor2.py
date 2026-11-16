exec(open('floor.py').read().split("print('box floor'")[0])
target=floor+0.03657
print('target cutoff',target)
for b in [0.005,0.01,0.02,0.05]:
    h,e=np.histogram(z,bins=np.arange(z.min(),z.max()+b,b)); i=h.argmax(); print('mode bin',b,e[i],e[i]+b/2,'-> +0.03',e[i]+b/2+0.03)
lowz=z[z<floor+0.1]
print('median of z<floor+0.1', np.median(lowz), 'mean',lowz.mean())
print('frac below target', (z<target).mean())
