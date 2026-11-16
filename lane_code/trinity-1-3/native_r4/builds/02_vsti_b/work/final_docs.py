from pathlib import Path
import ast,sys,json
B=Path(__file__).resolve().parents[1];R=B.parents[1];sys.path.append(str(B/'code'))
from adapter import *

def where(file,name):
    p=B/'code'/file
    node=next(n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name)
    return '`code/'+file+':'+str(node.lineno)+'`'
g='sj/orch_cd/evalx/work/milestone/native/out2/geometry.py'
p='sj/orch_cd/evalx/work/milestone/native/out2/perception.py'
text=f'''The read serves only move, turn and pose from the frozen tower run on this read's verified frames. The step-544 checkpoint supplies depth scale and gravity. All other recognized trained calls receive `error: call_unavailable; answer directly from the video`; this is the trace-3.13 recoverable error format, not a program refusal. Tags outside the trained grammar remain text.

- {where('policy.py','tail_pattern')} builds the extra detector from `reader_policy.CALL_NAMES`; {where('policy.py','camera_only')} preserves the original decoder and trace tail and injects the fixed refusal. `tests/test_read.py` checks every non-camera trained name, the three served names, ordinary tags and continued decoding.
- {where('adapter.py','prepare')} verifies selection and PNG SHA pins, writes the same 32 anchors, and separates scoring labels from prompts. The source is the comparator-prepared VSI-Bench copy, not a release-video claim. `out/RELEASE_CHECK.json` records the absent release inputs; `out/RELEASE_CHECK_SYNTHETIC.json` records the synthetic MP4 test.
- {where('engine.py','tower')} invokes the public frozen tower on these frames. Its weight/configuration hashes and revision remain the trainer's constants; `out/FAMILY.json:tower_members` seals the two member hashes. This build fits no tower or checkpoint parameters.
- {where('engine.py','prepare_geometry')} calls C8r's factored capture preparation at {where(g,'prepare_capture')}. Its depth query, scale estimator, camera conversion and gravity guard are shared with C8r's preparation command. No evaluation answer label conditions them. `out/GEOMETRY_CPU.json` records bit-identical scale, camera_to_world, K and guard decisions on an actual raw cache with the same synthetic checkpoint heads.
- {where(p,'camera_geometry')} remains the original serving conversion. The reader disables own-pose fallback for scored calls. Geometry refusals retain explicit zero-score records; the refused-geometry test verifies this accounting.
- {where('proof.py','run')} restores C8r's original code, inputs and serving in a separate process. {where('proof.py','preparation_check')} recomputes the selected captures through this read's preparation entry point using C8r's original conditioning questions. The original return contains prepared arrays; the comparison includes scale, camera matrices, K, status, errors, gravity diagnostics and prefill token digest. This GPU comparison has not run during the build.
- {where('o.py','run')} stages inherited C8r assets and the four additional pinned archives. The proof namespace includes the original evaluation inputs. The read namespace binds its own frames, prepared inputs, checkpoint assets and frozen tower; it does not bind the original evaluation masks/raw caches as read inputs.
- {where('engine.py','run')} commits complete item pairs and binds the proof to the request. {where('engine.py','merge')} verifies the request, configuration, geometry, journal and proof pins. {where('report.py','build')} refuses a non-synthetic report without that bound ten-item proof and prints its outcome and the frame caveat on separate single lines.

The official scorer copies are byte-identical to their supplied authorities; `out/SCORER_COPIES.json` lists their SHA256 values separately from the source patches. `out/SCORER_CHECK.json` reproduces both comparator scores. The report labels those comparisons as other models and preserves same-item pairing.

Unchecked: actual H100 restoration, prefill, greedy decoding and historical equality; full-frame staging; release-video pixels; Orchard namespace admission and both remote returns; V1b namespace rehearsal outside the sandbox. `out/UNEXECUTED.json` separates unexecuted reachable lines from shipped unreachable code. Its zero requirement applies to unexplained lines authored in V1/V1b, not to untested inherited code.
'''
(B/'out/LEGALITY.md').write_text(text)
for path in [B/'out/RUN_TRINITY.md',B/'out/RUN_ORCHARD.md']:
    s=path.read_text().replace('work/rehearsal_b/RESULT.json','work/rehearsal_delivery/RESULT.json').replace('work/cli_b/RESULT.json','work/cli_delivery/RESULT.json')
    path.write_text(s)
reasons={
 'a.py':'Runs the preparation and read phases, restores verified inputs on resume, and produces the bound report.',
 'budget.py':'Reserves return time and projects each item from measured rates with a margin.',
 'engine.py':'Shares capture preparation, preserves source-line attribution for parity coverage, and authenticates resumed journals and proof pins.',
 'entry.py':'Exposes proof-result, release-check, deadline and resume arguments while preserving the fallback commands.',
 'o.py':'Builds the primary packet, stages pinned additions through C8r, isolates the proof namespace, and publishes complete bounded returns.',
 'p.py':'Starts the historical proof in a fresh interpreter with the original module namespace.',
 'pixels.py':'Checks release-video hashes and measures selected RGB pixel differences under av 17.1.',
 'policy.py':'Limits added detection to trained call names and preserves recoverable refusal bytes.',
 'proof.py':'Recomputes the selected capture geometry, compares arrays and repeated traces, and honors the item deadline.',
 'proof_stage.py':'Places original raw caches at their authenticated logical path for the fallback proof.',
 'report.py':'Requires the bound production proof and prints the proof outcome and frame caveat, including the release check.',
 'u.py':'Verifies both uploaded copies before sealing their SHA, byte count and cloud generation.',
 'geometry.py':'Factors the original capture preparation into a shared helper without changing its numerical operations.'}
(B/'out/DIFF_FILES.md').write_text('Changes are measured against the refreshed V1 tree and C8r. The byte-identical scorer copies are listed separately in `SCORER_COPIES.json`.\n\n'+ '\n'.join(f"- `{r['file']}`: +{r['added']}/−{r['removed']} against V1; {reasons.get(Path(r['file']).name,'Preserves the inherited read contract.')}" for r in load(B/'out/DIFF_STATS.json')['V1']['files'])+'\n')
# Fresh rehearsal evidence replaces inherited result slots; retain historical data only as provenance.
for name,source in [('LOGIC_RESULT.json',B/'work/rehearsal_delivery/RESULT.json'),('CLI_RESULT.json',B/'work/cli_delivery/RESULT.json'),('RESULT.json',B/'work/rehearsal_delivery/RESULT.json')]:
    if source.exists():(B/'out/rehearsal'/name).write_bytes(source.read_bytes())
dump(B/'out/rehearsal/NAMESPACE.json',dict(status='operator_pending',command='./work/py out/rehearsal/run_rehearsal.py --fixture-tower',
    prior=pin(B.parent/'01_vsti/work/ns_op_c6ad71d3/run/job/RESULT.json'),prior_log=pin(B.parent/'01_vsti/work/ns_op.log'),current_namespace_executed=False))
