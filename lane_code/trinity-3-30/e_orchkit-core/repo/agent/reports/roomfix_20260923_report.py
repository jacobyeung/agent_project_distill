import hashlib
import json
from pathlib import Path

WT = Path('/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_roomfix_fullset_20260923T1152Z/work/repo')
OUT = WT.parents[1] / 'out'
S = Path('/data2/jjyeung/agent_project_data/student_diagnostic_pilot_20260918')
report = json.loads((OUT / 'VERIFICATION.json').read_text())
assert report['verdict'] == 'PASS'
paths = report['paths']
paths.update(worktree=str(WT), output=str(OUT), temporary=str(WT.parents[1] / 'tmp'), data_root=str(S),
             compact_source=str(S / 'diagnostic_set_compact_v25_uncapped_20260923'),
             source_labels='/data2/jjyeung/agent_project_data/vsi_distill_training_20260917/source/vsi_590k.jsonl',
             planner_python='/data2/jjyeung/envs/planner/bin/python',
             gt_python='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/lanes/swarm_h05_gtmonly/work/gt_cpu_env/bin/python',
             audit_packet='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/lanes/swarm_h05_gtmonly/out/ROOM_SIZE_AUDIT.md',
             fix_packet='/data2/jjyeung/agent_project_data/distillation_orchestrator_20260918/claude_swarm_20260923T0835Z/lanes/swarm_h05_gtmonly/out/ROOM_FIX.md',
             fix_review='/home/jjyeung/agent_project_distill/agent/scratch/codex_runs/20260923T114628Z_room_fix_18b7f3a_review/final_message.md')

def pin(path):
    path = Path(path)
    with path.open('rb') as handle:
        checksum = hashlib.file_digest(handle, 'sha256').hexdigest()
    return {'path': str(path), 'sha256': checksum, 'bytes': path.stat().st_size}

artifacts = {}
for key, names in {'corpus':['MANIFEST.json','CONFIG.json','CONVENTIONS.json','ROOM_REPAIR.json','COVERAGE.json','split.json','train.jsonl','heldout.jsonl'],
                   'mix':['MANIFEST.json','split.json','split_trainer.json','train.jsonl','heldout.jsonl'],
                   'trainer':['MATERIALIZATION.json','candidate_index.jsonl','split.json']}.items():
    artifacts[key] = {name: pin(Path(paths[key]) / name) for name in names}
receipt = {**report, 'artifacts': artifacts, 'tests': json.loads((OUT / 'TESTS.json').read_text()),
           'reviewed_room_fix_commit': '18b7f3ae7033dca689876312731980cdd58cf336',
           'corpus_build_commit': json.loads((Path(paths['corpus']) / 'MANIFEST.json').read_text())['repo_commit'],
           'mix_build_commit': json.loads((Path(paths['mix']) / 'MANIFEST.json').read_text())['repo_commit'],
           'training_launched': False}
(OUT / 'PATHS.json').write_text(json.dumps(paths, indent=2, sort_keys=True) + '\n')
(OUT / 'ARTIFACTS.json').write_text(json.dumps(artifacts, indent=2, sort_keys=True) + '\n')
(WT / 'agent/reports/roomfix_20260923_manifest.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
lines = ['The rebuilt corpus, mix, and trainer layout passed the independent byte, label, census, and split audit.', '',
         'The corpus contains 1,562 corrected room rows; 204 held-out room rows defer with room_label_not_training. No training label is missing. All 7,024 non-room corpus rows retain their exact source bytes.',
         f"The median rounded-target/source-label ratio is {report['target_label_ratio_median']:.6f}; its range is {report['target_label_ratio_min']:.9f} to {report['target_label_ratio_max']:.9f}. The unrounded scalar/label median is {report['scalar_label_ratio_median']:.6f}.",
         f"Among the 1,562 repaired rows, {report['room_answers_changed']} answer strings changed; every repaired row has corrected convention and label provenance.", '',
         '| Family/type | Corpus before | Corpus after | Mix train before | Mix train after | Mix heldout before | Mix heldout after |',
         '|---|---:|---:|---:|---:|---:|---:|']
families = sorted({f for field in ['corpus_counts_before','corpus_counts_after','mix_counts_before','mix_counts_after'] for side in report[field].values() for f in side['by_family']})
for f in families:
    values = [sum(v['by_family'].get(f,0) for v in report[field].values()) for field in ['corpus_counts_before','corpus_counts_after']]
    values += [report[field][side]['by_family'].get(f,0) for side in ['train','heldout'] for field in ['mix_counts_before','mix_counts_after']]
    lines.append('| ' + f + ' | ' + ' | '.join(map(str,values)) + ' |')
lines += ['', '| Source | Corpus before | Corpus after | Mix before | Mix after |', '|---|---:|---:|---:|---:|']
for source in ['compact','gtmeasure_v1']:
    values = [sum(v['by_source'].get(source,0) for v in report[field].values()) for field in ['corpus_counts_before','corpus_counts_after','mix_counts_before','mix_counts_after']]
    lines.append('| ' + source + ' | ' + ' | '.join(map(str,values)) + ' |')
lines += ['', 'All 305 exact scene identities retain their side. The trainer round trip preserves all 285 physical groups with zero new hashed groups and zero side changes. Training qids and their order are unchanged. The recipe replay reproduces every mixed row, its order, the split, and the 0.5 selection exactly.',
          '', 'The trainer contains 9,232 candidates and exactly 9,232 target directories, including both split sides. Its file mapping and serialization match the original Set B layout. The independent audit checks every row, target, index pin, and the complete target-tree digest.',
          '', 'New index SHA-256: ' + report['trainer_after']['index_sha256'], 'New targets SHA-256: ' + report['trainer_after']['targets_tree_sha256'],
          'Original index SHA-256 verified: ' + report['trainer_before']['index_sha256'], 'Original targets SHA-256 verified: ' + report['trainer_before']['targets_tree_sha256'],
          '', 'Verification: 121 compact tests passed; 113 GT tests passed; three corruption checks passed. The native-token regression remains unconfirmed because of the dependency/import limitation recorded in TESTS.json. The source-byte preservation check replaces non-room geometry regeneration; authenticated label replay verifies every corrected room row.',
          '', 'The source corpus and both original mix layouts retain their pinned bytes. PATHS.json lists all inputs and output roots; ARTIFACTS.json pins the generated files. No training, GPU, network, paid API, branch switch, push, rebase, or deletion occurred.']
(OUT / 'STEP_3.md').write_text('\n'.join(lines) + '\n')
print(json.dumps({'receipt':str(WT/'agent/reports/roomfix_20260923_manifest.json'),'index':report['trainer_after']['index_sha256'],'targets':report['trainer_after']['targets_tree_sha256']},sort_keys=True))
