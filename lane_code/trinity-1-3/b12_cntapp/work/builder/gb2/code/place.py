"""Copy pin-equal R1 builds of the 41 previously deferred captures into out/dose_pool/out/arkit_gt/gt; write PIN_CHECK.tsv for all 300."""
import json, hashlib, shutil, os, csv
L2='/scratch/jjyeung/orch_n30/gt_build2'; G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
old=list(csv.reader(open(G+'/out/PIN_CHECK.tsv'),delimiter='\t'))
hdr,rows=old[0],old[1:]
r1={json.loads(l)['c']:json.loads(l) for l in list(open(L2+'/logs/VARIANT_R1.jsonl'))[1:]}
od=L2+'/out/dose_pool/out/arkit_gt/gt'; os.makedirs(od,exist_ok=True)
out=[hdr]; new=0; sums=[]
for cap,pin,built,verdict in rows:
    ds,c=cap.split('/')
    if verdict.startswith('deferred') and ds=='arkitscenes' and r1[c].get('match'):
        src=f'{L2}/out/variants/R1/{c}.npz'; h=hashlib.sha256(open(src,'rb').read()).hexdigest(); assert h==pin
        dst=od+'/'+os.path.basename(P[cap]['gt_path']); shutil.copyfile(src,dst)
        assert hashlib.sha256(open(dst,'rb').read()).hexdigest()==pin
        sums.append(f'{pin}  dose_pool/out/arkit_gt/gt/{os.path.basename(dst)}'); new+=1
        out.append([cap,pin,h,'matched (gt_build2 rule set R1)'])
    elif verdict.startswith('deferred') and ds=='arkitscenes':
        out.append([cap,pin,r1[c]['sha'],'deferred: R1 build differs from pin (R1 = us dt rule, floor band + exempt boxes, float32 depth lift with float64 pose); flip search found none'])
    elif verdict.startswith('deferred'):
        out.append([cap,pin,built,verdict+'; gt_build2: no raycast tie between instances at 1e-9, no hole candidate at 1e-5, no visible crossing triangle'])
    else:
        out.append([cap,pin,built,verdict+('; R1 rerun equal' if ds=='arkitscenes' and r1[c].get('match') else '')])
        if ds=='arkitscenes': assert r1[c].get('match'), c
with open(L2+'/out/PIN_CHECK.tsv','w') as f:
    for r in out: f.write('\t'.join(r)+'\n')
open(L2+'/out/RASTERS_SHA256SUMS_NEW','w').write('\n'.join(sums)+'\n')
print('new',new,'matched total',sum(1 for r in out[1:] if r[3].startswith('matched')))
