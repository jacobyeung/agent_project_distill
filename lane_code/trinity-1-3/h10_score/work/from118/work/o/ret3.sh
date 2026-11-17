P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ac6
python3 - <<'X'
import tarfile,json
t=tarfile.open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ac6/result.tar.gz')
g=lambda n:t.extractfile(n).read().decode()
print(g('SUMMARY.json')[:1500]); print(g('metadata/journals/4/0/progress.json')[:400]); print('\n'.join(l[:300] for l in g('STEPS.jsonl').splitlines()[-3:]))
for l in g('metadata/journals/4/0/items.jsonl').splitlines():
    r=json.loads(l);o=r['output'];print(r['id'],r['mode'],round(r['seconds']),o['finish'],json.dumps(o['calls']['calls']))
X
python3 -c "import json;d=json.load(open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ac6/EXIT.json'));print({k:d[k] for k in ('status','complete','returncode','archive_sha256','archive_bytes')})"
TZ=UTC sacct -j 170694 -X -n -o JobID,State,ExitCode,Start,End,Elapsed
