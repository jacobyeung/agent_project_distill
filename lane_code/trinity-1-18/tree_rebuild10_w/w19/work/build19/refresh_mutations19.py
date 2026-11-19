from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build19';p=B/'mutations19.py';s=p.read_text()
s=s.replace("results=json.loads(prior_result.read_text())['results']", "results=json.loads(prior_result.read_text())['results']\n    tests_hash=hashlib.sha256((T/'tests/test_r1_build19.py').read_bytes()).hexdigest()\n    results=[r for r in results if not r['test'].startswith('tests.test_r1_build19.') or r.get('test_sha256')==tests_hash]")
s=s.replace("status='CAUGHT',returncodes=phases,", "status='CAUGHT',returncodes=phases,test_sha256=hashlib.sha256((T/'tests/test_r1_build19.py').read_bytes()).hexdigest() if test.startswith('tests.test_r1_build19.') else None,")
p.write_text(s)
p=B/'delivery19.py';s=p.read_text().replace("'retained_kits17'","'retained_kits17','retained_kits19'");p.write_text(s)
