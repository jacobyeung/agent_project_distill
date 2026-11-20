W=/scratch/jjyeung/orch_n30/tree_rebuild10_w; date -u +%TZ; S=$W/w24z7/out/tgcs; D=$W/work/tgcs2; test -e $D && { echo EXISTS; exit 1; }
mkdir -p $D && cp $S/run_tgcs.sh $S/driver.py $S/observe.py $D/ && cd $D
/scratch/jjyeung/envs/p1cpu/bin/python -I -s -B - <<'PY'
p='observe.py'; s=open(p).read()
a=s.index('Original=http.client.HTTPSConnection'); b=s.index('http.client.HTTPSConnection=Connection')+len('http.client.HTTPSConnection=Connection')
new='''Original=http.client.HTTPSConnection
_gr=Original.getresponse
def _getresponse(self):
 try:
  r=_gr(self)
  with (O/'logs/http.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),http=r.status,range=r.getheader('Range')))+'\\n')
  return r
 except Exception as e:
  with (O/'logs/http.jsonl').open('a') as f:f.write(json.dumps(dict(time=time.time(),error=mask(repr(e))))+'\\n')
  raise
Original.getresponse=_getresponse'''
s=s[:a]+new+s[b:]; open(p,'w').write(s); print('patched')
PY
diff $S/observe.py observe.py | head -40; sha256sum observe.py | cut -c1-16
O=$W/work/tgcs_900001b; timeout 400 bash $D/run_tgcs.sh 900001 /scratch/jjyeung/orch_n30/n_ops8_x/sess_900001.json $W/w24z4/out/kit_n $O; echo rc=$?
M='s#https?://[^ "]*#[URL]#g'; cd $O; sed -E "$M" RESULT.json | head -60; echo ==HTTP; sed -E "$M" logs/http.jsonl 2>/dev/null | sort | uniq -c | sort -rn | head; echo ==GCERR; sed -E "$M" logs/gc.stderr | tail -8; echo ==GCOUT; tail -4 logs/gc.stdout
