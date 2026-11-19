"""Simulate the orchestrator approving KERNEL_PROVENANCE.json, on a second extracted copy (./kit_appr).

Run as: bash kit_appr/scripts/cpu.sh $PWD/rk_approve.py   (W = ./kit_appr). Recorded input paths name the
delivery tree; gates.read is wrapped so they resolve to this byte-identical copy, which then behaves like the
delivery tree itself. Writes only inside ./kit_appr and ./out.
"""
import io, json, sys, unittest
from pathlib import Path
from unittest.mock import patch
H = Path(__file__).resolve().parent
import common, gates
from common import read, sha
W = common.W; assert W == H / 'kit_appr', W
DELIVERY = '/scratch/jjyeung/orch_n30/sb_rkfix2'
out = {}


def mapped(p):
    x = read(p)
    if isinstance(x, dict) and isinstance(x.get('input_sha256'), dict):
        x = dict(x, input_sha256={k.replace(DELIVERY, str(W)): v for k, v in x['input_sha256'].items()})
    return x


def err(f):
    try:
        return 'returned ' + repr(f())[:60]
    except BaseException as e:
        return type(e).__name__ + ': ' + str(e).replace(str(W), 'W')[:150]


def failures(prov, reader):
    """Every stale or missing input in the merged prerequisite records, not just the first."""
    recs = dict(mapped(prov)['input_sha256'])
    gates.merge_inputs(recs, mapped(reader)['input_sha256'])
    for n in ['S0', 'DRYRUN', 'K1_REPRODUCTION', 'TESTS']:
        gates.merge_inputs(recs, mapped(W / f'out/{n}.json')['input_sha256'])
    bad = [p.replace(str(W), 'W') for p, h in recs.items() if not Path(p).is_file() or sha(p) != h]
    return dict(files=len(recs), bad=bad)


P = W / 'configs/KERNEL_PROVENANCE.json'; R = W / 'configs/READER_RECEIPT.json'
original = P.read_bytes()
with patch.object(gates, 'read', mapped):
    out['G0_as_delivered'] = err(lambda: gates.prerequisites(P, R))
    out['G0_merged_input_failures'] = failures(P, R)
    approved = dict(json.loads(original), authorized_by='SIMULATED orchestrator approval (reviewer probe)')
    P.write_text(json.dumps(approved, indent=2) + '\n')
    out['G1_approved_in_place'] = err(lambda: gates.prerequisites(P, R))
    out['G1_merged_input_failures'] = failures(P, R)
    sys.path.insert(0, str(W / 'tests'))
    import test_roomkit
    res = unittest.TextTestRunner(stream=io.StringIO(), verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromName('test_roomkit.Tests.test_pending_kernel_authorization_blocks_launch'))
    out['G2_rerun_pending_test_after_approval'] = dict(ran=res.testsRun, failures=len(res.failures), errors=len(res.errors),
                                                       message=(res.failures or res.errors or [(None, '')])[0][1].strip().splitlines()[-1][:160].replace(str(W), 'W'))
    A = W / 'configs/KERNEL_PROVENANCE_APPROVED.json'; A.write_text(json.dumps(approved, indent=2) + '\n'); P.write_bytes(original)
    out['G3_approved_copy_at_new_path'] = err(lambda: gates.prerequisites(A, R))
print(json.dumps(out, indent=1))
json.dump(out, open(H / 'out/RK_APPROVE.json', 'w'), indent=1)
