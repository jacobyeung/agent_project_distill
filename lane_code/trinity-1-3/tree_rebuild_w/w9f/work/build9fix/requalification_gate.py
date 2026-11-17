"""Stop the next phase normally while a diagnosed source defect is repaired."""
import json
from pathlib import Path
path=Path(__file__).with_name('REQUALIFICATION.json')
if path.exists():
    value=json.loads(path.read_text())
    if value.get('pending'):
        raise SystemExit('Requalification pending: '+value['reason'])
