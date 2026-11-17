P=/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ab2
python3 - <<'X'
import tarfile,json
t=tarfile.open('/project/community/jjyeung/okh7/ae71c903/b01ec87a6f29b00029ab2/result.tar.gz')
g=lambda n:t.extractfile(n).read().decode()
print(g('SUMMARY.json')[:1500]); print(g('metadata/journals/3/0/progress.json')[:400]); print('\n'.join(l[:300] for l in g('STEPS.jsonl').splitlines()[-3:]))
for l in g('metadata/journals/3/0/items.jsonl').splitlines():
    r=json.loads(l);o=r['output'];print(r['id'],r['mode'],round(r['seconds']),o['finish'],json.dumps(o['calls']['calls']))
X
