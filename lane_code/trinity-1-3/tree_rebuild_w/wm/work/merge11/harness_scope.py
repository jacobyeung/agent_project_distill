from pathlib import Path
import hashlib,json
L=Path(__file__).resolve().parents[2]
source=L.parent/'work/design/eat1_v7/eat1/adapters/b04_tiny.py'
target=L/'work/build10/eat1/adapters/b04_tiny.py'
target.write_bytes(source.read_bytes())
(L/'work/merge11/HARNESS_SCOPE.json').write_text(json.dumps(dict(file=str(target.relative_to(L)),sha256=hashlib.sha256(target.read_bytes()).hexdigest(),reason='Unused bundled b04 adapter retains clean-v7 bytes. The replay uses the separately staged supplied b04 adapter, whose runnable paths are localized.'),indent=2)+'\n')
