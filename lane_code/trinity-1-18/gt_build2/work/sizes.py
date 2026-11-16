import json, os, zipfile
G='/scratch/jjyeung/orch_n30/gt_build'
P={r['canonical']:r for r in json.load(open(G+'/work/cr/PILOT300_INPUTS.json'))}
bad=open('/tmp/gb2_bad.txt').read().split()
ups=set(open(G+'/work/ups.txt').read().split())
for c in bad:
    r=P.get('arkitscenes/'+c) or P.get('scannetpp/'+c); pin=r['gt_bytes']
    row=[c, 'up' if c in ups else '  ', pin]
    for d in ['out/rejected/arkit_gt','out/variants/all_r180_pose64','out/variants/arkit_r180','out/variants/bad_r180_f32']:
        f=f'{G}/{d}/{c}.npz'
        row.append(os.path.getsize(f)-pin if os.path.exists(f) else None)
    print(*row, sep='\t')
