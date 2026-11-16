"""Export offline scorer predictions after fixed-holdout generation completes."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from student_pilot.admission import authorities, load_scorer, resolve_answer_key
from student_pilot.common import binding, load_json, write_once
from student_pilot.shakedown import OUT, FLAGS, score

score()
contract, _, _, _ = authorities()
scorer, scorer_pins = load_scorer(contract)
heldout = load_json(OUT / 'heldout.json')
labels = {str(row['id']): row for row in load_json(resolve_answer_key()['path'])
          if str(row['id']) in heldout['heldout_qids']}
matched_config = None
for arm in ('base', 'answer_only', 'summary_plus_answer'):
    if not (OUT / arm / 'evaluation_complete.json').exists():
        continue
    rows = [json.loads(line) for line in (OUT / arm / 'generations.jsonl').read_text().splitlines()]
    assert len(rows) == 63 and {row['qid'] for row in rows} == set(labels)
    config = load_json(OUT / arm / 'generation_config.json')
    assert config['do_sample'] is False and config['max_new_tokens'] == 1024
    if matched_config is not None:
        assert config == matched_config, 'Decoding settings differ between arms'
    matched_config = config
    eos = config['eos_token_id']
    eos = eos if isinstance(eos, list) else [eos]
    exported = []
    for row in rows:
        row = dict(row)
        row['tag_parsed_answer'] = row['parsed_answer']
        if row['status'] == 'ok':
            tokens = row['generated_token_ids']
            assert len(tokens) == row['generated_tokens'] <= 1024
            assert len(row['frame_hashes']) == 32
            row['finish_reason'] = 'STOP' if tokens and tokens[-1] in eos else 'MAX_TOKENS' if len(tokens) == 1024 else 'UNEXPECTED_STOP'
            assert row['finish_reason'] != 'UNEXPECTED_STOP'
            record, metrics = scorer._score_entry(row, labels[row['qid']], strict=True)
            row.update(parsed_answer=metrics['pr_ans'], score_record=record)
        else:
            row.update(parsed_answer=None, score_record={'credit': 0.0, 'missing_input_or_output': True})
        exported.append(row)
    path = OUT / arm / 'scored_generations.jsonl'
    payload = ''.join(json.dumps(row, allow_nan=False) + '\n' for row in exported)
    if path.exists():
        assert path.read_text() == payload, 'Refusing to overwrite a different scored export'
    else:
        with path.open('x') as stream:
            stream.write(payload)
    write_once(OUT / arm / 'scored_export.json', dict(**FLAGS, scorer=scorer_pins, export=binding(path), questions=63))
print('Offline parsed-answer exports complete for all finished arms.')
