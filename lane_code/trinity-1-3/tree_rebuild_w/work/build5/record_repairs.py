"""Record the rationale for explicit legacy test updates."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
rows=[
 dict(files=['student_pilot/gf1.py','student_pilot/carrier_c1_run.py','tests/test_gf1_contracts.py','tests/test_gf1_review.py'],
      kind='native defect',reason='The artifact validator, native loader and export metadata dereferenced a camera connector absent from the required visual-only arm.',
      retained='Real native model loading, artifact export/readback and logit equality with tiny pretrained/tower boundaries; absent camera metadata is omitted. The legacy nonzero-camera-context validator remains tested on an explicit legacy head.'),
 dict(files=['tests/test_gf1.py','tests/test_gf1_contracts.py'],kind='contract expectation',
      reason='The visual-only arm reconstructs once and does not execute a second camera path.',
      retained='Tower-call counts, shared-feature identity, cache lifetime and connector gradients.'),
 dict(files=['tests/test_c1_blockers.py','tests/test_carrier_c1_clip.py','tests/test_gx_s6.py'],kind='contract expectation',
      reason='Unauthenticated legacy bank readers must refuse before native model or bank access.',
      retained='Native optional-depth readouts, trajectory metrics, milestone-gate validation and explicit front-door refusal.'),
 dict(files=['tests/test_mdg_eval.py','tests/test_mdg_features.py'],kind='contract expectation',
      reason='Unauthenticated runtime/export entry points must refuse; CLI parity can separately use a declared tiny loader boundary.',
      retained='Real low-level prediction, packed serialization/readback, output immutability and CLI pass/fail behavior with a tiny loader.'),
 dict(files=['tests/test_gx_carrier.py'],kind='fixture repair',
      reason='Checkpoint doubles must return the native receipt path consumed by durable handoff.',
      retained='Fail-fast history, stopping steps and checkpoint/export decisions.'),
 dict(files=['tests/test_gx_dense_binding.py'],kind='contract expectation',
      reason='The required pose-row change invalidates the old dense-cache identity.',
      retained='Every current module hash is independently recomputed, and only the pose-row module may differ from the old identity.'),
 dict(files=['tests/test_pd_build2.py'],kind='contract expectation',
      reason='The bank evaluation entry refuses unauthenticated callers.',
      retained='Native per-scene metrics, summaries, threshold checks and held-out membership run directly on synthetic arrays; the entry refusal is asserted separately.'),
 dict(files=['tests/test_provisional.py','tests/test_provisional_pipeline.py','tests/test_orchard_eval_qwen36_27b.py'],kind='contract expectation',
      reason='Evaluation refuses before lease or model access; option flags do not authorize an unsupported reader.',
      retained='Training admission and slow-staging lease checks remain intact; evaluation and CLI tests assert that downstream access does not occur.'),
]
for row in rows:row['files']=['work/tree_r1/'+p for p in row['files']]
(L/'work/build5/LEGACY_ADAPTATIONS.json').write_text(json.dumps(dict(
    status='Implemented; final package results determine validation',adaptations=rows),indent=2)+'\n')
