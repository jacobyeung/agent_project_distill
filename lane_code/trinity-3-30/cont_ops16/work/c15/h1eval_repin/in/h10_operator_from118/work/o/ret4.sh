P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ad2
python3 - <<'X'
import tarfile,json
t=tarfile.open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ad2/result.tar.gz')
g=lambda n:t.extractfile(n).read().decode()
print(g('SUMMARY.json')[:1500]); print(g('metadata/journals/3/0/progress.json')[:400]); print('\n'.join(l[:300] for l in g('STEPS.jsonl').splitlines()[-3:]))
import collections
L=[json.loads(l) for l in g('metadata/journals/3/0/items.jsonl').splitlines()]
print(len(L), collections.Counter(r['mode'] for r in L), collections.Counter(r['output']['finish'] for r in L), round(sum(r['seconds'] for r in L)/len(L),1))
X
python3 -c "import json;d=json.load(open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ad2/EXIT.json'));print({k:d[k] for k in ('status','complete','returncode','archive_sha256','archive_bytes')})"
TZ=UTC sacct -j 170706 -X -n -o JobID,State,ExitCode,Start,End,Elapsed
