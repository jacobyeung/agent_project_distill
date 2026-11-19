from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];m=json.loads((L/'attic/build23b/PACKAGE_MANIFEST.json').read_text())['files']
print('\n'.join(str(v['bytes'])+' '+k for k,v in sorted(m.items(),key=lambda p:p[1]['bytes'],reverse=True)[:25]))
print('manifest bytes',sum(v['bytes'] for v in m.values()))
