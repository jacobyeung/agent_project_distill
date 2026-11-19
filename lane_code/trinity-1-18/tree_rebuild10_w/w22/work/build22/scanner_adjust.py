from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build21'
# Positive inheritance controls now name a proven standard-library callee.
p=B/'naming_test21g.py';s=p.read_text();a=s.index('    def test_inherited_positive');b=s.index('    def test_inherited_negative')
s=s[:a]+s[a:b].replace('run(env=','subprocess.run(env=')+s[b:];p.write_text(s)
p=B/'naming_test21d.py';s=p.read_text().replace('run(env=env)\\nos.environ.update(Q=', 'subprocess.run(env=env)\\nos.environ.update(Q=');p.write_text(s)
