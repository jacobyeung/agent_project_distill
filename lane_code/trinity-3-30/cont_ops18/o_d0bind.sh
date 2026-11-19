K=/project/community/jjyeung/okh7; R=$K/x_f5c353f7/runs/359fcc3c/inputs; P=$(ls -d $R/prepare_* | head -1); echo P=$P
cat $K/x_f5c353f7/o/gcs_359fcc3c_m200.done; ls $K/x_f5c353f7/o/ | grep 359fcc3c
sha256sum $P/config.json $P/prepared/s1_receipt.json $R/data_receipt.json
/usr/bin/python3 -c "
import json,sys
d=json.load(open('$P/prepared/s1_receipt.json'))
def walk(v,p=''):
  if isinstance(v,dict):
    for k,x in v.items():
      if k in ('config_sha256','base_identity','frame_layout','lineage','base_model_identity','identity') and not isinstance(x,(dict,list)): print(p+'/'+k,x)
      walk(x,p+'/'+k)
walk(d)" | head -12
tail -3 $K/813f42db/d544/pf.log
