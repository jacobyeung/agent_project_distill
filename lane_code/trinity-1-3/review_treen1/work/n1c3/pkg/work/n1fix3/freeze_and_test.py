from pathlib import Path
import json,subprocess,sys
L=Path(__file__).resolve().parents[2];B=L/'work/n1fix3'
code=subprocess.run([sys.executable,'-I','-s','-B',str(B/'make_delivery.py')],cwd=L).returncode
if code:raise SystemExit(code)
delivery=json.loads((B/'DELIVERY.json').read_text())
(B/'STATUS.md').write_text('# Build n1fix status\n\nThe final source and GO=false kits are frozen. Package suite groups are running from the archive; unchanged base groups require exact source/fixture hashes and normalized runner equivalence before reuse. Evidence: DELIVERY.json and proofs/package.\n')
code=subprocess.run(['bash',str(B/'PACKAGE_TEST.sh'),str(L/delivery['path'])],cwd=L).returncode
if code<0:raise SystemExit('A suite process was killed; stop without retry.')
raise SystemExit(code)
