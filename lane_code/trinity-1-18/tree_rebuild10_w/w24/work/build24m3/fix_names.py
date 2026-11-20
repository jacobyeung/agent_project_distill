from common import *
s=(D/'cs.py').read_text().replace("'census.json'","'c5.json'").replace("'diagnostic.json'","'d6.json'")
replace(D/'cs.py',s)
for name in ('q','n','n_go','qd'):
 k=kit(name);replace(k/'b/cs.py',s)
 for part in ('BUILD.json','SHA256SUMS.txt'):replace(k/part,(k/part).read_bytes())
 reseal(k)
