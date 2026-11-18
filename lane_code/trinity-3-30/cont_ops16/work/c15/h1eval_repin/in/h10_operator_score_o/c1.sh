export TZ=UTC; date -u +%FT%TZ; hostname
W=/project/community/jjyeung/okh7/e6fc152498; T=b01ec87a6f29b00029ad2; P=/project/community/jjyeung/okh7/ae71c903/$T
ls -la $P; sha256sum $P/result.tar.gz | cut -c1-16
python3 -c "import json;d=json.load(open('$P/EXIT.json'));print({k:d.get(k) for k in ('status','complete','returncode','archive_sha256','archive_bytes')})"
cat $P/RETURN_RECEIPT.json | head -c 800; echo
sacct -j 170706 -X -n -o JobID,State,ExitCode,Start,End,Elapsed
sha256sum $W/submerge2.py $W/submerge3.py $W/sub2_ns.sh $W/sub3_ns.sh 2>&1 | cut -c1-80
ls -la $W/r2/sj | grep -i ad2; ls -la $W | grep ad2
for f in $W/sub_$T.out $W/sub3_$T.out; do echo "== $f"; tail -5 $f 2>&1; done
pgrep -af submerge | head
squeue -u $USER -h -o '%i %j %T %M' 
python3 - <<'X'
import tarfile,json,collections
t=tarfile.open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ad2/result.tar.gz')
g=lambda n:t.extractfile(n).read().decode()
print(g('SUMMARY.json')[:1200]); print(g('metadata/journals/3/0/progress.json')[:400])
L=[json.loads(l) for l in g('metadata/journals/3/0/items.jsonl').splitlines()]
print(len(L), collections.Counter(r['mode'] for r in L), collections.Counter(r['output']['finish'] for r in L), round(sum(r['seconds'] for r in L)/len(L),1))
X
