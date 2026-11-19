from adapter import *
ins=input_code();ins[str(Path(__file__).resolve())]=sha(__file__);rows=[]
for cap,expected in [('scannetpp/067e2e4e61',14.73),('scannetpp/036bce3393',39.35)]:
 p=W/'out/s1/k1_64'/cap.replace('/','__')/'pred.npz';d=p.parent/'DONE.json';rec=read(d)
 assert rec['pred_sha256']==sha(p);ins[str(p)]=sha(p);ins[str(d)]=sha(d)
 result=pipeline(p,W/'out/s1a_geom'/(cap.replace('/','__')+'.npz'))
 error=abs(result['area_m2']/expected-1)
 rows.append(dict(capture=cap,area_m2=result['area_m2'],stored_gpu_m2=expected,relative_error=error,within_5pct=error<=.05,seconds=rec['seconds'],peak_rss_gib=rec['peak_rss_kib']/1024**2))
write(W/'out/S1A.json',dict(verdict='PASS' if all(r['within_5pct'] for r in rows) else 'FAIL',rows=rows),ins)
print(json.dumps(rows,indent=2))
status('S1a full 64-frame CPU tower forwards are complete; comparison is in out/S1A.json. Both workers are running 32-anchor K1 forwards, followed by the two R0-rl plumbing forwards. S0, S1b and all 22 CPU tests pass. No GPU or network activity has occurred.')
