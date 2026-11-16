import hashlib,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[2];B=L/'work/build7';T=L/'work/tree_r1'
sys.path.insert(0,str(T))
from student_pilot.response_spec import document
(T/'student_pilot/response_spec.json').write_bytes(document())
for name in ('coverage_cases.py','targeted.py','TARGETED_TEST.sh','legacy_guard_proof.py'):
 p=L/'work/build6'/name
 if p.exists(): (B/name).write_text(p.read_text().replace('work/build6','work/build7').replace("'work/build6'","'work/build7'"))
p=B/'coverage_all.py';s=p.read_text()
s=s.replace("(L/'work/build5/proofs',B/'proofs')", "(L/'work/build5/proofs',L/'work/build6/proofs',B/'proofs')")
p.write_text(s)
with (B/'DECISIONS.md').open('a') as f:
 f.write('''
BF16 cached banks failed the supplied gradient tolerance in `proofs/targeted/results.json`. The options are to change the cache algebra/storage or reject that precision. The kit defaults to an off FP32 cache and rejects enabled BF16; the unchanged parity assertion remains visible as a failure.

The bound processor configuration is absent locally. Resolution stays a required pinned parameter, with no guessed production value. The tiny fixture values are test inputs only.

The new store parameters identify family sources, but a native combined preparation receipt still needs implementation. The kit records PREPARED_MULTI_STORE_RECEIPT_BINDING_UNIMPLEMENTED and cannot launch.

The mask resize paths use a fixed canvas. Padding or preserving native dimensions changes mask coordinates and can change printed row bytes. The default is to retain the bytes and register PORTRAIT_MASK_DISTORTION until the rows lane can qualify the coordinate transform. No real frame portrait share can be computed from missing image dimensions.

Depth stencils, degree formatting and unavailable statuses cannot merely be renamed as module methods: the current read loop calls them outside forward. The options are an in-forward renderer with the b04 hook, or retaining the current reader as harness_served. The default retains the reader and records B04_FORWARD_HOOK_REQUIRED. No bound row is edited.

The frozen GF-1 stage trains only its connector. The options are changing the registered stage schedule or training scale in the subsequent joint stage. The default preserves the stage schedule; scale supervision is active but scale-head parameters are frozen in the connector-only stage. This is not a claim of scale-head learning in that stage.
''')
with (B/'STATUS.md').open('a') as f:
 f.write('\nInput contracts, policy gates, patch rebases and bounded audits are implemented. Remaining failures and incomplete integrations are explicit kit blockers. Final targeted checks precede the single frozen package run. The multi-rank stop proof is blocked by Gloo initialization; the actual shell trap proof passed (`proofs/stop/RESULTS.json`).\n')
