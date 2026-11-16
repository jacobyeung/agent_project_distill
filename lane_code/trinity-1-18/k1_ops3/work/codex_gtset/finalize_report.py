"""Collect review artifacts without touching deployment or live run roots."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys
from build_evidence import ROOT, KIT, OLD, FILES, E, MANIFEST, sha, write


def main():
    identity = json.loads((E / 'identity_proof.json').read_text())
    dependencies = {}
    for executable in ['/scratch/jjyeung/envs/p1cpu/bin/python',
                       '/scratch/jjyeung/envs/sam3_capretry_native_v1/bin/python']:
        dependencies[executable] = json.loads(subprocess.check_output([
            executable, '-B', '-c',
            'import importlib.util,json,sys;print(json.dumps(dict(python=sys.version,'
            'sklearn=importlib.util.find_spec("sklearn") is not None)))'], text=True))
    required = [OLD.parents[2] / 'grd_selector/work/setsel/setlib.py',
                OLD.parents[2] / 'devs1_masks/out/kit/work/vendor/MODELS.json']
    dependencies['refit_files'] = {str(p): p.exists() for p in required}
    write(E / 'refit_prerequisites.json', dependencies)
    # The functions that define the registered report statistics and the cache
    # identity checks remain exactly equal as syntax trees.
    unchanged = {}
    for filename, names in [('work/k1_report.py', ['report', 'mra', 'constant', 'auc']),
                            ('work/k1_pipeline.py', ['cached', 'cache_capture', 'raw_proposals',
                                                    'native_backend', 'printed_cues', 'cache_run'])]:
        def functions(root):
            return {n.name: ast.dump(n, include_attributes=False)
                    for n in ast.parse((root / filename).read_text()).body if isinstance(n, ast.FunctionDef)}
        old, new = functions(OLD), functions(KIT)
        for name in names:
            assert old[name] == new[name], name
            unchanged[filename + ':' + name] = True
    write(E / 'unchanged_functions.json', unchanged)
    docs = [Path('/data2/jjyeung/agent_project_data/distill_design/REFREEZE_AMENDMENT_1_K1_RASTERS_20261115.md'),
            Path('/data2/jjyeung/agent_project_data/distill_design/REFREEZE_PREREGISTRATION_20261115.md'),
            Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/orch_n30/events/k1_ops3/PART_B_JOB_DESCRIPTION.md')]
    hashes = {str(p): sha(p) for p in [MANIFEST, *docs]}
    for name in FILES + ['out/DEPENDENCIES.json', 'work/k1_phases.py', 'out/K1_RULES.json', 'out/K1_RULES.sha256']:
        hashes[str(KIT / name)] = sha(KIT / name)
    for name in ['GT_SET_PRIMARY_296.json', 'GT_SET_SENSITIVITY_300.json', 'SHA256SUMS']:
        p = ROOT.parent / 'gt_sets' / name
        hashes[str(p)] = sha(p)
    for p in sorted((ROOT / 'real_phase_copies').rglob('*')):
        if p.is_file(): hashes[str(p)] = sha(p)
    for p in sorted(E.iterdir()):
        if p.is_file() and p.name != 'file_hashes.json': hashes[str(p)] = sha(p)
    for name in ['DEPENDENCIES.json', 'gtset.diff', 'operator_commands.sh', 'test_gtset.py',
                 'build_evidence.py', 'finalize_report.py']:
        hashes[str(ROOT / name)] = sha(ROOT / name)
    write(E / 'file_hashes.json', hashes)
    tests = ['test_kit.log', 'test_guards.log', 'test_gtset_final.log', 'test_real_bridge.log']
    for name in tests:
        content = (E / name).read_text()
        assert '\nOK\n' in content and '\nFAILED ' not in content, name
    report = '''K1 declared-GT-set downstream patch — ready for independent review; not deployed.

The scratch kit supports --gt-set for tables, refit, render/responses and report.
The manifest remains byte-identical. No capture dictionary or capture digest changes.
The declared set controls GT reads and capture iteration. Pinned entries must match
the manifest SHA; every raster read verifies the declared SHA. Unpinned entries
require --sensitivity. Receipts and reports retain valid JSON and put SENSITIVITY
on their first line when that flag is present.

The gt_set receipt object records path, SHA256, n, pinned/unpinned counts, selected
captures, skipped canonicals and analysis label. FIT_RECEIPT pins TABLE_RECEIPT.
RENDER_RECEIPT pins the fit, table receipt and analysis rows. Per-capture COMPLETE
receipts carry the same set metadata. Report --ids-from derives the expected row
IDs from the tabled captures in the unchanged manifest and verifies table/fit
lineage. Missing, extra, duplicate or wrongly assigned outcome rows are refused.

Deployment changes (five source files plus DEPENDENCIES.json):
  work/gt_set.py: new shared set validation, selection and receipt helper.
  work/k1_pipeline.py: optional selection for GT checks, tables and responses.
  work/k1_cli.py: downstream-only --gt-set and --sensitivity flags.
  work/refit/train.py: table/set validation and fit receipt propagation.
  work/k1_report.py: --ids-from, declared denominator and report provenance.
DEPENDENCIES.json retains all original entries and changes only four existing
source pins, adding the new helper pin. All keys use the kc deployment paths.
The scratch tests verify those keys through an explicit scratch-path mapping;
they do not re-pin the deployment to the scratch copy or edit the live kit.

Identity evidence:
  B.source_identity() is equal before/after at the scratch location.
  Mapping the scratch prefix to the deployment prefix equals the separately
  imported original identity and the copied live tower/SAM BINDING sources.
  k1_phases.py, native_kit/*, K1_RULES.* and all phase producer pins are unchanged.
  The original executed kit still matches the complete copy-time hash inventory.
  cached(), cache_capture(), raw_proposals(), cache_run(), native_backend(),
  printed_cues() and every report statistic function have identical syntax trees.

Tests and limits:
  Native kit: 19 tests pass. Native guards: 7 tests pass.
  Downstream suite: 16 tests pass; real-proposal bridge: 1 test passes.
  All tests use nice -n 10, empty CUDA visibility and one OMP/MKL/OpenBLAS thread.
  Candidate and nonempty pair tables are byte-identical to unchanged-kit output
  for an all-capture fixture. Default report bytes are exactly equal. Default
  TABLE_RECEIPT bytes match after substituting only different output-directory
  paths. The all-set report's scientific payload is byte-identical after removing
  the requested provenance fields. Whole enriched receipts/reports cannot also
  be byte-identical: the request requires them to contain new set metadata.
  Subset tests check selected rows, skipped lists, hashes and report denominator.
  Sensitivity tests check refusal without the flag and first-line labels through
  tables, fit, render and report. Hash/digest/missing-cache checks fail closed.
  Old code rejects the new keyword and the subset report denominator.
  The full downstream fixture executes native table construction and rendering.
  Refit estimator calls, metrics and missing reference dependencies use explicit
  test stand-ins. These tests validate handoffs, not fitted coefficients or K1
  numerical results. No production analysis was run or scored.

Real-capture compatibility:
  Two copied run_tower_sam_2 directories pass unchanged checked_phase() with the
  documented deployment-path mapping. Their BINDING manifest/source/producer
  identities match the new kit. They contain PHASE_COMPLETE, tower, proposals
  and parity files, not CACHE_COMPLETE or geometry. Direct cached() therefore
  correctly refuses them. Literal acceptance of these raw directories as
  converted caches is neither possible nor safe.
  A separate bridge combines their real tower/proposal bytes with explicitly
  synthetic own depth/gravity and the old converted-cache schema. Both old and
  patched cached() accept it, and patched tables pass their actual cache-entry
  checks. GT loading and label construction are stubbed only in this bridge.
  It proves schema compatibility, not completion of production own/convert.
  DEPENDENCIES verifies installed source bytes at startup; its aggregate digest
  is not stored in phase BINDING. The changed downstream source files and new
  helper are outside B.source_identity(). Existing phase receipts thus remain
  valid when the patch is deployed at the original paths with the new pins.

Production prerequisites still required:
  A completed own/convert cache is not present under /scratch/jjyeung/k1.
  Neither supplied Python environment has scikit-learn.
  The existing refit's setlib.py and current MODELS.json paths are absent.
  Restore those approved dependencies; this patch does not invent model weights
  or replace the frozen fitting algorithms. The operator script checks them.
  K1_CONVERT_CACHE and K1_REFIT_PY are required operator parameters because their
  completed/approved values are not available in this workspace.

Orchard Part B:
  The own-only package needs no change for this feature. Its phase code, native
  sources, capture identities and producer pins remain equal. Its returned own
  artifacts must pass the unchanged convert stage with tower/SAM, after which
  both analyses use this same patched tables -> refit -> render -> report chain.
  If an operator chooses to deploy these downstream files on Orchard too, copy
  the new helper and matching DEPENDENCIES together. That is not required to
  execute own. No Orchard package file was edited.

Deployment and operation:
  Independent review must finish before use. Nothing has been copied into kc.
  After tower_sam has ended, the operator copies the five listed source files
  from this scratch kit to their identical relative paths in the executed kit,
  then installs the provided DEPENDENCIES.json as out/DEPENDENCIES.json.
  Do not deploy test artifacts, test dependency stand-ins, or scratch lane links.
  Run operator_commands.sh with K1_CONVERT_CACHE and K1_REFIT_PY set. It contains
  the exact eight stage commands, writes fresh analysis roots inside this
  workspace, and does not run any phase or edit any manifest/GT set.
  If stages fail, preserve their outputs; do not relaunch cluster-killed work
  without the required operator answer. The primary/sensitivity verdict handling
  remains the amendment's rule: disagreement on a registered mark declares no
  verdict and goes to the orchestrator. This patch changes no mark or threshold.

Writing skill: no-archaeology. The old/new comparisons below are retained because
the requested compatibility and identity proofs require a reference implementation.

'''
    sections = [('IDENTITY PROOF', E / 'identity_proof.json'),
                ('NEW PINS', E / 'new_pins.json'),
                ('REAL PHASE CHECKS', E / 'real_phase_checks.json'),
                ('REAL CACHE BRIDGE', E / 'real_cache_bridge.json'),
                ('REFIT PREREQUISITES', E / 'refit_prerequisites.json'),
                ('EXACT OPERATOR COMMANDS', ROOT / 'operator_commands.sh'),
                ('UNIFIED DIFF (also gtset.diff)', ROOT / 'gtset.diff')]
    for name, path in sections:
        report += '\n=== ' + name + ' ===\n' + path.read_text()
    # Keep all diagnostic and final test output, including fixture failures.
    for path in sorted(E.glob('*.log')):
        report += '\n=== FULL LOG: ' + path.name + ' ===\n' + path.read_text()
    report += '\n=== FILE HASHES ===\n' + (E / 'file_hashes.json').read_text()
    (ROOT / 'REPORT.txt').write_text(report)
    (ROOT / 'REPORT.sha256').write_text(sha(ROOT / 'REPORT.txt') + '  REPORT.txt\n')
    print('Wrote REPORT.txt, REPORT.sha256 and evidence/file_hashes.json')


if __name__ == '__main__':
    main()
