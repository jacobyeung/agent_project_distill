export TZ=UTC
sacct -j 172843 -n -P -o JobID,JobName%30,State,ExitCode,Elapsed,NodeList,Start,End,Reason 2>&1 | head
P=/project/community/jjyeung/okh7/a15_cot_apd50ba921ef1f4
ls -la $P $P/a | head -40
ls -la /project/community/jjyeung/okh7/ae71c903 | grep d50ba || echo no_pool_dir
cat $P/a/8.txt; cat $P/2.json | head -c 400; echo
python3 - <<'PY'
import ast,io,tarfile,json,hashlib
for t in ('d60a20ec01296','d50ba921ef1f4'):
    p='/project/community/jjyeung/okh7/a15_cot_ap'+t
    l=[x for x in open(p+'/BATCH.sh').read().splitlines() if x.startswith('b=bytes.fromhex(')][0]
    raw=bytes.fromhex(ast.literal_eval(ast.parse(l).body[0].value.args[0]))
    m={x.name:hashlib.sha256(tarfile.open(fileobj=io.BytesIO(raw)).extractfile(x).read()).hexdigest()[:12] for x in tarfile.open(fileobj=io.BytesIO(raw)).getmembers()}
    c=json.load(open(p+'/a/c/CPU.json'))
    print(t,m,'cpu keys',sorted(c)[:20])
PY
