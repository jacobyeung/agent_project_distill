"""Install explicit fail-closed gates on unsupported evaluation entrypoints."""
import ast
import json
from pathlib import Path

L = Path(__file__).resolve().parents[2]
T = L/'work/tree_r1'
entries = {
    'student_pilot/carrier_c1_run.py': ['inference', 'probe', 'evaluate'],
    'student_pilot/carrier_c1_canary.py': ['run'],
    'student_pilot/decoupled_v_run.py': ['evaluate', 'probe'],
    'student_pilot/grounding_eval.py': ['load_runtime', 'run_worker', 'merge', 'to_ground'],
    'student_pilot/mdg_eval.py': ['load_runtime', 'run_export', 'run_pointing', 'run_w10'],
    'evalpath/runtime.py': ['load_model'],
    'evalpath/items.py': ['load_items'],
    'evalpath/run.py': ['load_request_items', 'run_worker'],
    'evalpath/routed_dev.py': ['load_tasks'],
    'evalpath/vqa_direct.py': ['load_tasks', 'run_worker'],
    'evalpath/pointing_candidates.py': ['run_worker'],
    'evalpath/pointing_markers.py': ['load_tasks', 'run_worker'],
    'evalpath/heldout_loss.py': ['run_worker'],
    'evalpath/official.py': ['score_official_vsibench', 'score_our_cell'],
    'evalpath/parity.py': ['run_suite'],
    'verifykit/prepare.py': ['prepare_dev', 'prepare_pointing'],
    'verifykit/score.py': ['evaluate'],
    'step0_runtime_v1/run_cell.py': ['run'],
    'step0_runtime_v1/diag_worker.py': ['run'],
    'tools/stage1_dev_metrics.py': ['main'],
    'tools/run_gate_eval_pdg.py': ['main'],
    'tools/headcall_eval_summary.py': ['main'],
    'headcall/gate_eval.py': ['main'],
    'rk/report.py': ['main'],
    'scripts/tracecold_read_native.py': ['readout'],
    'scripts/orchard/eval_job.py': ['main'],
    'scripts/gpu_native_selector.py': ['main'],
    'student_pilot/diagnostic.py': ['evaluate'],
    'student_pilot/gate_driver.py': ['run_gate', 'main'],
    'student_pilot/trace_readout.py': ['main'],
    'student_pilot/shakedown.py': ['evaluate', 'score'],
    'student_pilot/run_live_parity.py': ['main'],
    'student_pilot/mdg_runtime.py': ['load_runtime'],
    'rk/sets.py': ['_dev_rows', '_revsi_rows', 'dev_items', 'revsi_items', 'answers', 'cache_revsi', 'scene_labels'],
    'rk/programs.py': ['run', 'main'],
    'tools/hc_v3_decode_check.py': ['check', 'probe', 'main'],
    'headcall/gate_eval.py': ['load_rows', 'main'],
    'scripts/head_probe.py': ['main'],
}
for package in ('benchmark_eval', 'orchard_eval'):
    entries[f'student_pilot/{package}/generate.py'] = ['generate_run']
    entries[f'student_pilot/{package}/prepare.py'] = ['prepare']
    entries[f'student_pilot/{package}/score.py'] = ['score_run', 'compare_scores', 'export_bank']
    entries[f'student_pilot/{package}/contracts.py'] = ['load_generation']
entries.update({
    'evalpath/kit_inputs.py':['official_rows'],
    'tools/pdg_v3_gate.py':['load_pqs','load_questions','main'],
    'headcall/eval_hook.py':['evaluate_head_vs_shuffled'],
    'student_pilot/all_frame_readout.py':['evaluate'],
    'student_pilot/gate_eval.py':['evaluate'],
    'student_pilot/benchmark_eval/__main__.py':['main'],
    'student_pilot/orchard_eval/__main__.py':['main'],
})
records = []
module_gates={'rk/programs.py','rk/report.py','step0_runtime_v1/run_cell.py','step0_runtime_v1/diag_worker.py'}
for relative, names in entries.items():
    path = T/relative
    source = path.read_text()
    if relative in module_gates:
        source=(L/'work/base/tree_b01ce449'/relative).read_text()
        nodes=ast.parse(source).body
        first=nodes[1] if isinstance(nodes[0],ast.Expr) and isinstance(nodes[0].value,ast.Constant) else nodes[0]
        lines=source.splitlines(keepends=True)
        lines.insert(first.lineno-1,"from student_pilot.r2_policy import unsupported_entry\n"
                     +f"unsupported_entry({(relative+':import')!r})\n")
        path.write_text(''.join(lines))
        records.extend(dict(file=relative,function=name,adapter='module-refuse',
                            reason='Refuse before external or script-local legacy imports') for name in names)
        continue
    lines = source.splitlines(keepends=True)
    inserts = []
    for node in ast.parse(source).body:
        if not isinstance(node, ast.FunctionDef) or node.name not in names:
            continue
        first = node.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            first = node.body[1]
        label = relative+':'+node.name
        records.append(dict(file=relative, function=node.name, adapter='refuse',
                            reason='Legacy format lacks an authenticated item-identity adapter'))
        if not any(isinstance(n,ast.Name) and n.id=='unsupported_entry' for n in ast.walk(node)):
            indent=' '*first.col_offset
            inserts.append((first.lineno-1, indent+'from student_pilot.r2_policy import unsupported_entry\n'
                            +indent+f'unsupported_entry({label!r})\n'))
    for offset, text in sorted(inserts, reverse=True):
        lines.insert(offset, text)
    source=''.join(lines)
    ast.parse(source)
    path.write_text(source)
(L/'out/B3_BANK_ENTRYPOINTS.json').write_text(json.dumps(records,indent=2)+'\n')
