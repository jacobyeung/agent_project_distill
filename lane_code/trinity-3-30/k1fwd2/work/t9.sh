cd /scratch/jjyeung/orch_n30/sb_own400/in || exit 1
cat own_544_fov.stream.sha256
D=own_544_fov; ls $D $D/k1fwd2; du -sb $D; ls $D/native/probe | wc -l
df -h /scratch | tail -1
/usr/bin/python3 - <<'PY'
import json,hashlib,os
D='/scratch/jjyeung/orch_n30/sb_own400/in/own_544_fov'
bars=json.load(open('/scratch/jjyeung/orch_n30/sb_own400/out/BARS_FROZEN.json'))
caps=bars['captures']
keys={r['key']:r for r in caps}
fc=json.load(open(D+'/k1fwd2/FOV_CHECK.json'))
rows={r['key']:r for r in fc['rows']}
ok=bad=0;served=0
for k,r in keys.items():
  d=D+'/native/probe/'+k
  rec=json.load(open(d+'/FOV_RECEIPT.json'))
  f=hashlib.sha256(open(d+'/fov.npz','rb').read()).hexdigest()
  own='/scratch/jjyeung/k1/own_170235/native/probe/%s/own.npz'%k
  good=(f==rec['files']['fov.npz'] and rows[k]['served_equal'] and rows[k]['receipt_ok'] and rec['canonical']==r['canonical'] and rows[k]['anchor_indices']==r['anchor_indices'] and not rec['missing'] and os.path.isfile(own))
  ok+=good; bad+=not good
print('keys',len(keys),'ok',ok,'bad',bad,'fc_summary_passed',fc['summary']['passed'])
PY
