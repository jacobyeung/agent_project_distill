from common import *
p=D/'rcj_scan.py';s=p.read_text().replace("  for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))","  if p.suffix=='.sh':\n   for i,line in enumerate(p.read_text().splitlines(),1):check(line,'rcj/'+p.name+':'+str(i))")
replace(p,s);(D/'rcj_scan.log').rename(L/'attic/build24m4j/rcj_scan_second.log')
