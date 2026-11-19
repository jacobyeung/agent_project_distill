"""Bind the reused validation harness to the final build inputs."""
import hashlib,json
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build8'
for name in ('TRAINABLE_POLICY.json','PACKET_INPUTS.json'):
 (B/name).write_bytes((L/'work/build7'/name).read_bytes())
assert (B/'test_runner.py').read_bytes()==(L/'work/build7/test_runner.py').read_bytes()
with (B/'DECISIONS.md').open('a') as f:
 f.write('\n- Use the existing native scratch census (`R2_FAST_CENSUS=1`) during the final package suite. It measures the same files before and after each test; the test runner retains its build-7 bytes and base receipt identity. This choice changes neither test assertions nor coverage collection.\n')
 f.write('\n- Keep camera-row selection blocked without the exact sealed goal-scene exclusion file. Test the real pose adapter, per-row producer, C1 packer and model reader with synthetic inputs; do not replace the exclusion check. The canonical GTScene loader still binds a fixed legacy frame inventory, so its full 64-frame path remains unqualified.\n')
 f.write('\n- Retain the native production allocation/admission checks. The stop rehearsal executes the extracted native r.sh trap and native h.forward/i.relay chain around a two-rank CPU run_steps entry. It does not qualify the GPU admission wrapper. The sandbox refused socket creation before rank launch; no multi-rank pass is claimed.\n')
 f.write('\n- Frame-count shape checks validate input dimensions only. The inference selector, response computation, thresholds and fallback behavior remain unchanged. The outside-weight source inventory is supplied for the independent acceptance review.\n')
for name in ('stop_multirank.py','frame_changes.py','direct_changes.py','resolve_resize.py'):
 compile((B/name).read_bytes(),str(B/name),'exec')
pins={str(p.relative_to(L)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (B/'stop_multirank.py',B/'proofs/stop_multirank/RUN.sh')}
(B/'proofs/stop_multirank/DRIVER_PINS.json').write_text(json.dumps(dict(files=pins,
 status='Prepared; full driver unverified because socket allocation was refused. No rank step or artifact was produced.'),indent=2)+'\n')
