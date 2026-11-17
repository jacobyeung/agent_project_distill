"""Write the current disposition from completed evidence."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
def read(name):return json.loads((B/name).read_text())
c=read('SUITE_COMPARISON.json');v=read('CHANGED_COVERAGE.json');p=read('proofs/packet/results.json')
text=['# Build 8 status','', 'Review delivery complete; GO=false. Acceptance remains blocked by the inputs and findings listed in `out/BUILD8_REPORT.md`.','',
 '| Item | Current disposition | Evidence |','|---|---|---|',
 '| 1 | Fixture regressions repaired; BF16_CACHE_GRADIENT_PARITY retained at its original tolerance. | `proofs/regressions/DISPOSITION.json`; `SUITE_COMPARISON.json` |',
 '| 2 | R2 failure events: '+str(c['r2_failures'])+'. | `SUITE_COMPARISON.json` |',
 '| 3 | CPU statement gaps: '+str(v['classes'].get('CPU-reachable unresolved',0))+'. | `CHANGED_COVERAGE.json`; `GAPS.json` |',
 '| 4 | The sandbox refused sockets. A separate lane receipt reached the first step, then failed signal forwarding. The driver path is repaired; stop and reload remain unproved. Lane runs RUN.sh after build 8. | `proofs/stop_multirank/RESULT.codex_sandbox.json`; `proofs/stop_multirank/RESULT.json`; `proofs/stop_multirank/RUN.sh` |',
 '| 5 | Local frame propagation proved; canonical GT, dense-pose admission and production readers need their named inputs. | `proofs/audit/FRAME64_REMAINING_SITES.json` |',
 '| 6 | Every transform-review entry classified. Coordinate distortion remains; portrait share unknown: frame dimensions absent from the bound slices. | `proofs/audit/RESIZE_AUDIT.json` |',
 '| 7 | Empty-think training paths refuse with LEGACY_DIRECT_SOURCE_EMPTY_THINK_REFUSED. | `proofs/direct/results.json` |',
 '| 8 | Requested out-of-scope blockers retained. | `out/BUILD8_REPORT.md` |','',
 'Packet results: '+str(sum(x['outcome']=='passed' for x in p.values()))+' passed of '+str(len(p))+' (`proofs/packet/results.json`).',
 'Frozen tree results: '+str(c['passed'])+' passed of '+str(c['run'])+'; '+str(c['preexisting'])+' pre-existing failure events and '+str(c['regressions'])+' regression events (`SUITE_COMPARISON.json`).','',
 'The execution ledger remains in `FINAL_PASS.json`; diagnosed packet setup failures and their corrected sequential checks are recorded in `PACKET_RECOVERY.json`. The base suite resumes only from matching input-hash receipts.','',
 'Delivery pins and storage measurements: `FINAL_VERIFICATION.json`. The report and design record contain the final dispositions.']
(B/'STATUS.md').write_text('\n'.join(text)+'\n')
