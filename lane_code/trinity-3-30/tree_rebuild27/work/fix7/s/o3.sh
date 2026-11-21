export TZ=UTC; date -u +%TZ
TOK=$(cat <<'TOK'
v630cd91d8070
v77bce2e08bbc
v0d0ff5239074
ve7c5313aff2b
vce37d31fc5d0
v05957e87b7f0
v1ff9e9ffb907
v512d55c8f189
v56c14e1d0b2a
va7d6eb28508c
vcaedbd3880a8
vff2676b38dd9
v1b137156393b
v3242b8e28c0c
v636d9b27e234
v86c73ccfcbea
vc9f7c7970dc7
vfd814bfd0fc5
41007581
41159362
42447216
42447221
42898712
42898977
42899053
42899950
44358599
47115258
47330996
47331169
47331211
47331362
47332503
47332505
47332645
47332653
TOK
)
A=/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap
for f in $A/f02f16ad/z/v3.json $A/f02f16ad/in3/held_a3b.json $A/e84d901c/z/548bad70.tsv $A/e84d901c/z/673cdf90.json $A/544dcf9b/in/b627c840.json $A/e84d901c/z/4c230a7e.json $A/f02f16ad/s/a3v2/division.json; do
  if [ -f $f ]; then echo "FILE $f $(stat -c %s $f) $(sha256sum $f | cut -c1-16)"; echo "  HITS $(grep -o -F -f <(printf '%s\n' "$TOK") $f | sort | uniq -c | awk '{printf "%s:%s ",$2,$1}')"; else echo "NOFILE $f"; fi
done
for d in $A/f02f16ad/s/a3v2 $A/f02f16ad/a3/s $A/f02f16ad/a3/a $A/f02f16ad/z $A/f02f16ad/in3; do
  if [ -d $d ]; then echo "DIR $d n=$(ls $d | wc -l)"; ls $d | head -12 | tr '\n' ' '; echo; echo "  NAMEHITS $(ls $d | grep -F -f <(printf '%s\n' "$TOK") | head -20 | tr '\n' ' ')"; else echo "NODIR $d"; fi
done
python3 - <<'PY'
import json
A='/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'
for f in (A+'/f02f16ad/z/v3.json', A+'/f02f16ad/in3/held_a3b.json', A+'/e84d901c/z/673cdf90.json', A+'/544dcf9b/in/b627c840.json'):
    try:
        v=json.load(open(f))
        if isinstance(v,dict): print('KEYS',f[-30:],{k:(len(x) if isinstance(x,(list,dict)) else x) for k,x in list(v.items())[:12]})
        else: print('LIST',f[-30:],len(v),str(v[:2])[:300])
    except Exception as e: print('ERR',f[-30:],repr(e)[:150])
PY
date -u +%TZ
