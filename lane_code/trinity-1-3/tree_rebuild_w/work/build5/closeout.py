"""Record completion and the measured storage limitation without stale tasks."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
audit=json.loads((L/'work/build5/FINAL_AUDIT.json').read_text())
assert audit['status']=='CPU QUALIFIED; PRODUCTION CLOSED'
note=('Legacy teacher fixtures exceeded the temporary cap on both source versions. '
      'The harness recorded refusals and compacted their products; measured peaks and test names '
      'are in `work/build5/REPORT_DETAILS.json`. This is not a claim that temporary usage never exceeded the cap.')
status=L/'work/build5/STATUS.md'
body=status.read_text().split('\nStorage qualification:',1)[0]
status.write_text(body.rstrip()+'\n\nStorage qualification: '+note+'\n')
design=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
body=design.read_text()
head,section=body.split('\n## Build 5\n',1)
section=section.split('\n**Measured storage limit.**',1)[0]
design.write_text(head+'\n## Build 5\n'+section.rstrip()+'\n\n**Measured storage limit.** '+note+'\n')
(L/'work/build5/NEXT.md').write_text('# Build completion\n\n'
    'The delivery driver and final audit completed. No test process remains active. '
    'The source, both closed kits and delivered archive are bound by `FINAL_AUDIT.json`. '
    'Read `out/BUILD5_REPORT.md` for counts, causes, coverage and limitations. '
    'The next work is independent review and the explicitly unexecuted real-byte checklist in '
    '`out/FRAME_HOST_JOB.md`; no launch or remote call is authorized.\n\n'+note+'\n')
print(audit['status'])
