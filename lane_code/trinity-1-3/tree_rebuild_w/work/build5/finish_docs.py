"""Write the design decision and final status from measured qualification receipts."""
import json
from pathlib import Path
L=Path(__file__).resolve().parents[2]
def read(name):return json.loads((L/name).read_text())
suite=read('work/build5/SUITE_COMPARISON.json')
coverage=read('work/build5/CHANGED_COVERAGE.json')
delivery=read('work/build5/DELIVERY.json')
complete=not suite['regressions'] and not suite['fatal'] and not coverage['classes'].get('CPU-reachable unresolved',0)
status='CPU qualification complete; production remains blocked' if complete else 'CPU qualification incomplete; production remains blocked'
record=L/'out/DESIGN_RECORD_tree_rebuild_20261115.md'
prior=record.read_text() if record.exists() else '# Design record\n'
prior=prior.split('\n## Build 5\n',1)[0]
section='''
## Build 5

**Question.** Can the packaged source satisfy the CPU suite and changed-statement obligations while retaining conservative admission and making the missing frame-host work explicit?

**Answer.** STATUS_VALUE. The package binds the final sampler to admitted reader offsets, reserves retained archives, joins program frame metadata through the native pinned map reader, and requires every frame-host receipt before success. Evidence: `out/BUILD5_REPORT.md`, `work/build5/SUITE_COMPARISON.json`, `work/build5/CHANGED_COVERAGE.json`.

**Reasons.** A refusal after frame resolution changes reader offsets and must also change sampler indices. Native checkpoint files and their retained transport archives consume the same local disk. Missing frame metadata requires an authenticated map input. Runtime execution, archive staging, bank membership, vocabulary and native output visibility require actual host bytes. The implementation and CPU boundary tests are identified in `out/BUILD5_REPORT.md`; the real-byte obligations are in `out/FRAME_HOST_JOB.md`.

**Options rejected.** Keeping pre-refusal indices would select the wrong rows. Omitting retained archives would understate disk demand. Inventing frame metadata from answers would violate evidence provenance. Calling a synthetic host receipt a real-byte qualification would hide missing inputs. Weakening the repeat limit or full-store guard to fit a local test would alter admission. Keeping every scratch payload would violate the storage budget; completed owned scratch products instead become in-place hash receipts under the bounded harness.

**What might not work and how we notice.** The actual interpreter or archive layout may differ from the pinned plan; the runtime and staging steps refuse. Real map coverage or exclusions may reduce admitted populations; materialization records refusals and the sampler rechecks repeats. Real bank or vocabulary bytes may differ; the corresponding checklist step refuses. Native output paths, directory links or JSON may violate the visibility scanner; the output step refuses rather than granting an exception. The small transport round trip does not qualify a full trainer-state restore. A changed source, input or receipt invalidates its hash binding.

**Tests that would settle it.** Execute every numbered frame-host step against the pinned runtime, archives, map, bank files and export witness; inspect all receipts and the native-output scan. Separately qualify a durable full trainer-state restore before production authorization. No remote execution is authorized by this record.

**Status.** STATUS_VALUE. The source and package identities are in `out/TREE_SEAL.json` and `work/build5/DELIVERY.json`. Both kit authorizations remain closed. Exact suite counts, coverage classes and unexecuted checks are in `out/BUILD5_REPORT.md`.
'''.replace('STATUS_VALUE',status)
record.write_text(prior.rstrip()+'\n'+section)
(L/'work/build5/STATUS.md').write_text('# Build 5 status\n\n'+status+'.\n\n'
    'The final report is `out/BUILD5_REPORT.md`. Suite outcomes and untouched-base comparisons are in '
    '`work/build5/SUITE_COMPARISON.json`; current-source coverage is in `work/build5/CHANGED_COVERAGE.json`. '
    'The frame-host checklist is `out/FRAME_HOST_JOB.md`.\n\n'
    'The package is `'+delivery['path']+'`; its identity is in `work/build5/DELIVERY.json`. '
    'The source seal and kit verification receipts are `out/TREE_SEAL.json` and `work/build5/kits/RESULTS.json`.\n\n'
    'No launch, remote call or GPU work was performed. Actual frame-host bytes and production qualification remain outstanding.\n')
print(status)
