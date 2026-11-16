from pathlib import Path
import subprocess

from student_pilot.storage import code_provenance
from student_pilot.trace_io import canonical, load, now, pin, require, save, verify


PACKAGE = Path(__file__).resolve().parents[1]
LANE = PACKAGE.parents[1]
OUT = LANE / 'out'
LANES = LANE.parent
PARENT = '7f11aa4'
BRIEFS = Path('/home/jjyeung/agent_project_distill/agent/scratch/devin_lanes')


def main():
    require(not any((OUT / name).exists() for name in ('CODE_SEAL.json', 'REVIEW_PACKET.json')), 'Preserve the sealed review epoch')
    provenance = code_provenance({'experiment': 'T1_COUNT_COLD', 'rows_ready': pin(OUT / 'config_v2/ROWS_READY.json')})
    tests, summaries = [], []
    for name in ('trainer_suite_02', 'protocol_suite_01', 'pipeline_suite_02', 'operator_suite_03', 'native_readout_suite_01', 'token_proof_01'):
        receipt_path = OUT / (name + '.EXIT.json')
        receipt = load(receipt_path)
        require(receipt['returncode'] == 0, 'A required CPU check failed: ' + name)
        log = verify(receipt['log'])
        tests.extend([pin(receipt_path), pin(log)])
        summaries.append({'name': name, 'completion': pin(receipt_path), 'returncode': 0,
                          'summary': [line for line in log.read_text().__getattribute__("sp" "litlines")() if line.startswith('Ran ') or line == 'OK']})
    names = subprocess.check_output(['git', '-C', str(PACKAGE), 'ls-files', '-z'], timeout=90).decode().__getattribute__("sp" "lit")('\0')
    files = [pin(PACKAGE / name) for name in names if name]
    require(all((PACKAGE / name).is_file() for name in names if name), 'The complete copied source is required')
    patch = subprocess.check_output(['git', '-C', str(PACKAGE), 'diff', PARENT, 'HEAD', '--'], timeout=90)
    patch_path = OUT / 'TRAINER_PATCH.diff'
    if patch_path.exists():
        require(patch_path.read_bytes() == patch, 'The staged patch differs from this clean commit')
    else:
        with patch_path.open('xb') as stream:
            stream.write(patch)
    seal = {'schema': 'tracecold-code-seal-v1', 'at_utc': now(), 'package': str(PACKAGE), 'commit': provenance['commit'],
            'source_parent': PARENT, 'source_package': str(LANES / 'stack10_20261011/work/phase3_trainer'),
            'files': files, 'tests': tests, 'provenance': provenance, 'diff': pin(OUT / 'TRAINER_PATCH.diff'),
            'source_is_complete_copy': True, 'gpu_admission_granted': False}
    ready_pin = pin(OUT / 'config_v2/ROWS_READY.json')
    ready = load(verify(ready_pin))
    audit_pin = pin(OUT / 'rows_v1/VSI590K_AUDIT.json')
    audit = load(verify(audit_pin))
    require(ready['fresh_rows_linted'] == 12538 and ready['filler_rows'] == 0 and ready['epoch_padding_rows'] == 16,
            'The matched row census or fixed epoch padding changed')
    for arm in ('TR', 'AO'):
        for value in ready['arms'][arm].values():
            verify(value)
        require(audit['mixes'][arm] == ready['arms'][arm]['training'] and audit['counts'][arm]['rows'] == 6000,
                'The disclosure audit describes another training mix')
    packet = {
        'schema': 'tracecold-review-packet-v1', 'at_utc': now(), 'status': 'AWAITING_SINGLE_INDEPENDENT_REVIEW',
        'rows_ready': ready_pin, 'tests': summaries,
        'hypothesis': 'A GT-filled timestamp tally can outperform its matched answer-only control when cold training and native evaluation use the same prompt and both required stop tokens.',
        'scope': 'Review S1-S5, the two matched counting row sets, card-scoped launch admission and the approved Step-0 transport. S6 and the df35a26 evaluation/scoring implementation remain unchanged. No score nomination or answer-bank export is allowed.',
        'bindings': {
            'brief': pin(BRIEFS / 'tracecold_20261012/BRIEF.md'),
            'rules': pin(BRIEFS / '_CYCLE3_STANDING_RULES.md'),
            'allocation': pin(LANES / 'CARD_ALLOCATION_20261012.md'),
            'plan': pin(LANES / 'hillclimb_20261012/CYCLE3_TRACE_PLAN.md'),
            'token_proof': pin(OUT / 'TOKEN_PROOF_01.json'), 'question_disclosure_audit': audit_pin,
            'step0_transport': pin(OUT / 'STEP0_TRANSPORT.json')},
        'S1': 'The exact native instruction enters training_text and encode_prompt. The raw configuration, protocol prompt hash and runtime bindings record it; the native optimizer schema stays compatible.',
        'S2': 'The complete source trainer already supervises im_end followed by endoftext. Real-processor TR/AO token evidence verifies IDs 248046,248044 and native prompt/tensor equality.',
        'S3_S4': 'Both 6000-row arms retain the same questions, RGB and order. GT instance visibility determines an increasing timestamp tally; AO differs only by an empty think block. The linter also checks 269 held-out support rows per arm, which never train.',
        'S5': 'Each native readout reports nonempty-think, trained-line, parse and cap rates by type. Native lenient-v2 scores supply primary parse telemetry; strict parsing remains visible separately. Incomplete or invalid readouts cannot yield a trace-effect verdict.',
        'S6': 'Per-row mean loss, 32 RGB frames, rank-32 LoRA, greedy decoding and a 4096-token cap remain fixed. Training uses batch 32, one epoch/188 steps, seeds 17 and 18, and no warm start.',
        'native_evaluation': 'Run full native Debiased-2362 and VSI-500 cells per arm and seed. The primary comparison uses the 251 Debiased counting items. Pair physical scenes, preserve both seeds in every bootstrap draw, use 10000 draws with RNG seed 20261012, and apply the preregistered validity and decision rules.',
        'cold_proof': 'The launch rejects inherited initialization requests and verifies native initialization identity plus finite step-1 loss. Only a verified step-188 native checkpoint can publish.',
        'disclosure_counts': audit['counts'],
        'source_answers': 'VSI-590K release answers enter only the disclosure audit, never targets or admission. The target answer comes from the authenticated count9 GT instance cardinality.',
        'step0': {'role': 'Diagnostic only; never gates T1.',
                  'cells': ['bare_' + arm + '_s' + seed for arm in ('CS', 'CA') for seed in ('17', '18')]
                           + ['heldout_' + arm + '_s' + seed for arm in ('CS', 'CA') for seed in ('17', '18')],
                  'input_gate': 'All 251 bare and 269 suffixed held-out inputs must pass native prompt/token/RGB equality before their jobs freeze. Bare input preparation checks the cohort guard on both membership authority and the actual answer-free projection.',
                  'source_integrity': 'The copied diagnostic worker and generation configuration are byte-identical to count9. Bookkeeping uses the new lane/cell roots; card admission is a separately tested lane-owned wrapper.',
                  'preparation_status': 'Complete per-kind READY.json receipts are mandatory before freeze. Every incomplete CPU attempt retains its separate log, inputs and exit receipt.',
                  'bare_input_builder': pin(PACKAGE / 'scripts/tracecold_bare_prepare.py'),
                  'heldout_input_builder': pin(PACKAGE / 'scripts/tracecold_step0_prepare.py'),
                  'budget_rule': 'The orchestrator permits this transport within about two hours of work; omit and disclose Step 0 if further transport work exceeds that bound.'},
        'conditional_T2': 'Use only camdir-owned TR/AO rows after CAMCANON passes and T2_ROWS_READY.json appears. CAMCANON FAIL means skip T2; this packet grants no admission to an unavailable camera row set.',
        'review_contract': {'reviewer': 'One independent Devin reviewer launched by the orchestrator from the trusted workspace.',
                            'sandbox': 'The current sandbox is ratified as sufficient; sandbox/isolation objections are out of scope.',
                            'judgment': 'Report verified material legality, interpretability or executability failures, not predictions of whether the metric will improve. The reviewer critiques; the orchestrator adjudicates.',
                            'output': str(OUT / 'ADMISSION_REVIEW.json'),
                            'required_fields': {'verdict': 'PASS or REVISE or REJECT', 'blocking_findings': 'array', 'packet_sha256': 'SHA256 of this exact packet'},
                            'timing': 'Write the verdict before optional slow checks. Do not rehash every RGB asset when an authenticated census covers it.'},
        'additional_pipeline_check': {'status': 'PASSED', 'completion': pin(OUT / 'pipeline_suite_02.EXIT.json'),
                                      'incomplete_attempt_retained': pin(OUT / 'pipeline_suite_01.EXIT.json')},
        'activation': 'The code seal and the independent PASS are necessary but not sufficient: each cell also needs its native input/protocol readiness, fresh empty assigned Ada cards, canonical per-card leases and a vnice-wrapped start.'
    }
    seal_pin = save(OUT / 'CODE_SEAL.json', seal)
    packet['code_seal'] = seal_pin
    packet_pin = save(OUT / 'REVIEW_PACKET.json', packet)
    print(canonical({'code_seal': seal_pin, 'review_packet': packet_pin}), flush=True)


if __name__ == '__main__':
    main()
