from common import *
s=(D/'census_tests.py').read_text().replace("F=D/'census'","F=D/'census_final'")
s=s.replace("  J.write(root/'p/q/ss.json',source)", """  sp=J.write(root/'p/q/ss.json',source)
  (root/'p/i').mkdir()
  mp=J.write(root/'p/i/staging.json',dict(entries={'ss.json':dict(sha256=sp['sha256'],bytes=(root/'p/q/ss.json').stat().st_size)}))
  J.write(root/'p/q/host.json',dict(staging_plan_sha256=mp['sha256']))""")
s=s.replace("dict(status='PASS',config_identity=identity(config),assertions=", "dict(staging_plan_sha256=mp['sha256'],status='PASS',config_identity=identity(config),assertions=")
s=s.replace("D/'CENSUS_TESTS.json'","D/'CENSUS_FINAL_TESTS.json'")
(D/'census_final_tests.py').write_text(s)
