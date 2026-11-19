from pathlib import Path
import json
L=Path(__file__).resolve().parents[2]
source=(L/'work/build3/coverage.py').read_text()
source=source.replace("if not report.exists():continue", "if not report.exists() or snapshot.name == 'B3B_FOCUSED_':continue")
source=source.replace("'B3_COMBINED_COVERAGE.json'", "'B3B_COMBINED_COVERAGE.json'")
source=source.replace("'B3_COVERAGE_REMAP.json'", "'B3B_COVERAGE_REMAP.json'")
source=source.replace("'B3_COVERAGE_CLASSIFIED.json'", "'B3B_COVERAGE_CLASSIFIED.json'")
source=source.replace("'build3-changed-statement-coverage-v1'", "'build3b-changed-statement-coverage-v1'")
(L/'work/build3b/coverage.py').write_text(source)
source=(L/'work/build3/finish_kits.py').read_text().replace("work/build3/kits", "work/build3b/kits").replace("work/build3/CPU_DENSE_FIXTURE.json", "work/build3b/CPU_DENSE_FIXTURE.json").replace('B3_KITS.json','B3B_KITS.json')
(L/'work/build3b/finish_kits.py').write_text(source)
for name in ('B3_ALL_TEST_RESULTS.json','B3_CLOSURE_TEST_RESULTS.json','B3_GAPS_TEST_RESULTS.json'):
    value=json.loads((L/'out'/name).read_text())
    print(name, sum(max(0,r['tmp_after']-r['tmp_before']) for r in value['records']))
print('current tmp',sum(p.stat().st_size for p in (L/'work/tmp').rglob('*') if p.is_file()))
