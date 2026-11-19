"""The reason_generate stop/append loop on a toy decoder and toy heads."""
import importlib.util
import unittest

import torch

from tests.auxiliary_toys import ROOT, SPECIALS, TIMES, Toy, ToyTokenizer, encoded_row, install_runner

install_runner()
from student_pilot import auxiliary_config as config  # noqa: E402
from student_pilot import auxiliary_reason as reason  # noqa: E402
from student_pilot.auxiliary_losses import attach, video_features  # noqa: E402

COUNT, TIME, ANGLE, COORD = (reason.QUERY_TOKENS[kind] for kind in ('COUNT', 'TIME', 'ANGLE', 'COORD'))
QUESTION = 'How many tables are in the room?'


def settings():
    return config.normalize({'reason_weight': .5, 'head_width': 16})


def load_generator():
    spec = importlib.util.spec_from_file_location('reason_generate', ROOT / 'scripts/reason_generate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class GenerationLoopTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(17)
        torch.set_num_threads(1)

    def test_stop_read_append_resume_on_a_toy_model(self):
        generator = load_generator()
        tokenizer = ToyTokenizer()
        table = reason.token_table(tokenizer)
        eos = [SPECIALS.index('<|endoftext|>')]
        script = tokenizer.encode(f'There are {COUNT}9 tables at {TIME}1.0 seconds; turn {ANGLE}+45 now and walk {COORD}+2.0 m.<|endoftext|>')
        model = Toy()
        heads = attach(model, settings(), tokenizer)
        prompt = encoded_row(tokenizer, QUESTION, 'x')[1]
        prompt_length = int((prompt['labels'][0] == -100).sum() - (prompt['attention_mask'][0] == 0).sum())
        prompt_ids = prompt['input_ids'][0, :prompt_length].tolist()
        requests = []

        def generate(ids, budget, stop_ids):
            # A scripted toy decoder: it emits the script, skipping values the loop appended itself.
            requests.append((len(ids), budget, list(stop_ids)))
            produced = ids[prompt_length:]
            cursor, index = 0, 0
            while index < len(produced):
                if script[cursor] in table['query']:
                    cursor += 1
                    index += 1
                    while cursor < len(script) and script[cursor] in table['chars'].values():
                        cursor += 1
                    while index < len(produced) and produced[index] in table['chars'].values():
                        index += 1
                    continue
                cursor += 1
                index += 1
            new = []
            while cursor < len(script) and len(new) < budget:
                new.append(script[cursor])
                cursor += 1
                if new[-1] in stop_ids:
                    break
            return new

        def readout(ids, kind):
            batch = {'input_ids': torch.tensor([ids]), 'attention_mask': torch.ones(1, len(ids), dtype=torch.long),
                     'labels': torch.full((1, len(ids)), -100), 'video_grid_thw': prompt['video_grid_thw']}
            captured = []
            handle = model.language_model.norm.register_forward_hook(lambda m, a, out: captured.append(out))
            with torch.no_grad():
                model(**batch, logits_to_keep=1)
            handle.remove()
            frames = video_features(captured[0], batch, 3, 2).mean(dim=(2, 3))
            outputs, scores = heads.reason_outputs(captured[0], frames, torch.tensor([[len(ids) - 1]]))
            return heads.format(kind, outputs[0, 0], scores[0, 0], [float(f'{t:.1f}') for t in TIMES])

        ids, calls = generator.decode_with_queries(generate, readout, prompt_ids, eos, table['query'], 200,
                                                   lambda text: reason.value_ids(text, table))
        self.assertEqual([call['kind'] for call in calls], ['COUNT', 'TIME', 'ANGLE', 'COORD'])
        text = tokenizer.decode(ids)
        self.assertEqual(text, f'There are {COUNT}{calls[0]["value"]} tables at {TIME}{calls[1]["value"]} seconds; '
                               f'turn {ANGLE}{calls[2]["value"]} now and walk {COORD}{calls[3]["value"]} m.<|endoftext|>')
        self.assertRegex(calls[2]['value'], r'^[+-]\d+$')
        self.assertRegex(calls[3]['value'], r'^[+-]\d+\.\d$')
        self.assertTrue(text.endswith('<|endoftext|>'))
        self.assertEqual(len(requests), 5)
        self.assertTrue(all(set(eos) | set(table['query']) == set(stop) for _, _, stop in requests))
        for call in calls:
            self.assertEqual(tokenizer.decode([ids[call['query_index']]]), reason.QUERY_TOKENS[call['kind']])
            self.assertEqual(tokenizer.decode(ids[call['query_index'] + 1:call['query_index'] + 1 + call['value_tokens']]),
                             call['value'])
        self.assertIn(calls[1]['value'], [f'{t:.1f}' for t in TIMES])
        # Plain mode: query tokens are ordinary tokens; decoding never stops for them.
        plain, plain_calls = generator.decode_with_queries(generate, None, prompt_ids, eos, None, 200)
        self.assertEqual(plain_calls, [])
        self.assertEqual(plain, script)
        # The budget bounds generated tokens, appended values included.
        short, _ = generator.decode_with_queries(generate, readout, prompt_ids, eos, table['query'], 12,
                                                 lambda text: reason.value_ids(text, table))
        self.assertLessEqual(len(short), 12)


if __name__ == '__main__':
    unittest.main()
