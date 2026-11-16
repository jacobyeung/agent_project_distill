"""Render the governed run sheet with the existing operator tokens and report pin."""
from pathlib import Path
import json,sys
B=Path(__file__).resolve().parents[1];O=B/'out'
sys.path.insert(0,str(O/'guard_kit'))
from worker import REPORT_SHA256
template=(B/'work/RUN_G4.template.md').read_text()
for step,token in json.loads((O/'OPERATOR_TOKENS.json').read_text()).items():
    template=template.replace('@TOKEN_'+step+'@',token)
template=template.replace('@REPORT_SHA256@',REPORT_SHA256)
assert '@TOKEN_' not in template and '@REPORT_SHA256@' not in template
(O/'RUN.md').write_text(template)
