from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];B=L/'work/build12';source=L/'work/build10/harness_coverage10.py'
s=source.read_text().replace("('g8_contract','g8_available','adapter_manifest')","('g8','l1','harness_extra','adapter_manifest')")
s=s.replace("(B/'HARNESS_COVERAGE.json')","(L/'work/build12/HARNESS_COVERAGE.json')")
exec(compile(s,str(source),'exec'),{'__file__':str(source),'__name__':'__main__'})
v=json.loads((B/'HARNESS_COVERAGE.json').read_text())
print(json.dumps([r for r in v['statements'] if not r['executed']]))
