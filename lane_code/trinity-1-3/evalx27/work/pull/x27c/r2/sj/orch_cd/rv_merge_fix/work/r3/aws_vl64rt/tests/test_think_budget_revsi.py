"""aws_vl64rt: OFF/ON prompt-ID parity with the trainer encoding on a real ReVSI task, and the B2048/B4096 derivation plus
merge_budgets through this kit's ReVSI merge (real tasks, duplicate frames). CPU only; tokenizer from the T0 base files."""
import asyncio, json, sys, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace as NS
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'evaluator'))
import merge
from budget import derive, source_lines
from budget_merge import merge_budgets
from scoring import score_item
from evalpath.items import digest
BASE = Path('/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle/base')
RES = Path('/scratch/jjyeung/orch_cd/evalx/work/res_rv999_d32')
ON = dict(model='cp1m200', layout='duplicate', benchmarks=['revsi'], decoding='greedy', thinking=True, max_tokens=16384)
OFF = dict(ON, model='t0m800', thinking=False, max_tokens=4096)


class FakeEngine:
    def __init__(self, text, tokenizer): self.text = text; self.tokenizer=tokenizer; self.calls = []
    async def generate(self, req, params, request_id):
        assert params.max_tokens == 64 and params.temperature == 0
        self.calls.append(req)
        yield NS(prompt_token_ids=req['prompt_token_ids'], outputs=[NS(text=self.text, token_ids=self.tokenizer.encode(self.text,add_special_tokens=False), finish_reason='stop')])


class Budget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from transformers import AutoProcessor
        from data import tasks_for
        cls.processor = AutoProcessor.from_pretrained(BASE, local_files_only=True)
        cls.processor._student_pilot_student = 'qwen35'
        cfg = json.loads((RES/'bundle/k1/0.json').read_text().replace('$Q', str(RES/'bundle/k1')))
        cls.cfg = cfg
        ts = sorted((t for s in cfg['datasets'] for t in tasks_for(s, cfg['roots'])), key=lambda t: t['example_id'])
        num = [t for t in ts if t['question_type'] == 'object_size_estimation']
        cls.tasks = [num[0], num[1]]

    def test_prompt_ids_match_trainer_on_and_off(self):
        import numpy as np
        from transformers.video_utils import VideoMetadata
        from parity import prompt, trainer_encode
        from media import kwargs
        task = self.tasks[0]
        arrays = np.zeros((64, 32, 32, 3), dtype=np.uint8)
        meta = dict(fps=2., frames_indices=[i for i in range(32) for _ in range(2)], total_num_frames=32, height=32, width=32)
        for cell, suffix in ((ON, '<think>\n'), (OFF, '<think>\n\n</think>\n\n')):
            text = prompt(self.processor, task, cell)
            self.assertTrue(text.endswith(suffix))
            batch, audit = trainer_encode(self.processor, task, arrays, meta, cell)
            call = self.processor(text=[text], videos=[arrays], video_metadata=[VideoMetadata(**meta)], **kwargs(len(arrays)), return_tensors='pt')
            self.assertEqual(call['input_ids'][0].tolist(), batch['input_ids'][0, :audit['prompt_tokens']].tolist(), cell['thinking'])

    def rows(self, binding):
        tok = self.processor.tokenizer
        out = []
        specs = [(self.tasks[0], 'Size.</think>\n\n'+str(self.tasks[0]['ground_truth'])), (self.tasks[1], ' a'*4100)]
        for t, text in specs:
            ids = tok.encode(text, add_special_tokens=False)
            r = {k: v for k, v in t.items() if k not in ('text', 'student_input')}
            r.update(key=t['benchmark']+':'+t['example_id'], binding=binding, status='complete', raw_generation=text,
                     token_ids=ids, token_ids_sha256=digest(ids), thinking=True, model='cp1m200', decoding='greedy', frames=32,
                     layout='duplicate', finish_reason='stop' if len(ids) < 16384 else 'length', prompt_tokens=10,
                     media={'metadata': {'frames_indices': [i for i in t['source_frame_indices'] for _ in range(2)]}, 'anchor_indices': None},
                     anchor_indices=None)
            r.update(score_item(r, text, len(ids), cap=16384, finish=r['finish_reason']))
            r['at_4096'] = dict(raw_generation=tok.decode(ids[:4096],skip_special_tokens=True), **score_item(r,tok.decode(ids[:4096],skip_special_tokens=True),min(len(ids),4096),cap=4096,finish='length' if len(ids)>=4096 else r['finish_reason']))
            out.append(r)
        return out

    def test_derive_and_merge_budgets_on_revsi(self):
        from worker import append
        cfg = dict(self.cfg, cells=[ON], gpus=1)
        cfg['binding'] = 'request'
        source_binding = digest(dict(request='request', cell=0))
        rows = self.rows(source_binding)
        with tempfile.TemporaryDirectory() as d:
            out = Path(d); (out/'0').mkdir()
            for r in rows: append(out/'0/g0.jsonl', r)
            cfg['output'] = str(out)
            async def request_for(r): return dict(prompt='<think>\n', multi_modal_data={}), r['media']
            engine = FakeEngine(str(self.tasks[1]['ground_truth']),self.processor.tokenizer)
            asyncio.run(derive(sources=source_lines(out/'0/g0.jsonl', strict=True), cell=ON, source_binding=source_binding,
                request_binding='request', cell_index=0, budgets=(2048, 4096), tokenizer=self.processor.tokenizer, engine=engine,
                params=NS(temperature=0, max_tokens=64), request_for=request_for, path_for=lambda b: out/'0'/f'budget_{b}.g0.jsonl'))
            self.assertEqual(len(engine.calls), 2)
            import budget_merge
            orig_budget_tasks=budget_merge.tasks_for
            budget_merge.tasks_for=lambda *a: [dict(t) for t in self.tasks]
            orig_tasks, orig_probe = merge.tasks_for, merge.probe_tasks
            merge.tasks_for = lambda *a: [dict(t) for t in self.tasks]; merge.probe_tasks = lambda *a: []
            try:
                main = merge.merge(cfg, 0, '1',tokenizer=self.processor.tokenizer)['benchmarks']['revsi']
                merge_budgets(cfg, 0, '1',tokenizer=self.processor.tokenizer)
            finally:
                merge.tasks_for, merge.probe_tasks = orig_tasks, orig_probe
                budget_merge.tasks_for=orig_budget_tasks
            self.assertEqual(main['completed'], 2); self.assertEqual(main['per_type']['object_size_estimation']['score'], .5)
            for b in (2048, 4096):
                s = json.loads((out/f'budget_{b}/0/summary_1.json').read_text())['benchmarks']['revsi']
                self.assertEqual((s['completed'], s['expected']), (2, 2))
                self.assertEqual(s['per_type']['object_size_estimation']['score'], 1.0)
                meta = [json.loads(l) for l in (out/'0'/f'budget_{b}.meta.jsonl').read_text().splitlines()]
                self.assertEqual(sorted(m['forced_close'] for m in meta), [False, True])
                reused = source_lines(out/'0'/f'budget_{b}.jsonl')[rows[0]['key']][1]
                self.assertEqual(reused, source_lines(out/'0/g0.jsonl')[rows[0]['key']][1])


if __name__ == '__main__':
    unittest.main()
