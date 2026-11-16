"""aws_vl64rt: explicit-thinking ReVSI cells (T0 m800 OFF 4,096; CP1 m200 ON16k + derived B2048/B4096), the
duplicate-layout frame admission, and the thinking-aware rescore. CPU only; uses the real rv999_d32 journal (T0 ON16k)."""
import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'evaluator'))
import merge
from scoring import score_item
from evalpath import official
RES = Path('/scratch/jjyeung/orch_cd/evalx/work/res_rv999_d32')
ON = dict(model='t0m800', layout='duplicate', benchmarks=['revsi'], decoding='greedy', thinking=True, max_tokens=16384)
OFF = dict(ON, thinking=False, max_tokens=4096)


def real_cfg():
    return json.loads((RES/'bundle/k1/0.json').read_text().replace('$Q', str(RES/'bundle/k1')))


class Think(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from data import tasks_for
        cfg = real_cfg()
        cls.tasks = {t['benchmark']+':'+t['example_id']: t for s in cfg['datasets'] for t in tasks_for(s, cfg['roots'])}
        cls.rows = [json.loads(l) for l in open(RES/'o/0/g0.jsonl') if l.strip()]
        for r in cls.rows: r.update(thinking=True, model='t0m800', decoding='greedy', layout='duplicate')

    def row(self, i=0):
        return json.loads(json.dumps(self.rows[i]))

    def test_duplicate_row_admitted_and_spread_refused(self):
        r = self.row(); t = self.tasks[r['key']]
        merge.check_row(r, t, 32, ON)
        s = t['source_frame_indices']
        for bad in (s, s + s, [x for p in zip(s, s) for x in p][2:] + [s[0], s[0]],
                    [x for p in zip(s, s) for x in p][:-2] + [s[-1], s[-2]]):
            b = self.row(); b['media']['metadata']['frames_indices'] = bad
            with self.assertRaises(ValueError): merge.check_row(b, t, 32, ON)
        b = self.row(); m = b['media']['metadata']['frames_indices']; m[0], m[2] = m[2], m[0]
        with self.assertRaises(ValueError): merge.check_row(b, t, 32, ON)

    def test_spread_cell_refuses_duplicate_row_and_layout_field(self):
        r = self.row(); t = self.tasks[r['key']]
        with self.assertRaises(ValueError): merge.check_row(r, t, 32, dict(ON, layout='spread'))
        r = self.row(); r['layout'] = 'spread'
        with self.assertRaises(ValueError): merge.check_row(r, t, 32, ON)

    def test_thinking_and_cap_must_match_cell(self):
        r = self.row(); t = self.tasks[r['key']]
        with self.assertRaises(ValueError): merge.check_row(r, t, 32, OFF)
        r = self.row(); r.pop('thinking')
        with self.assertRaises(ValueError): merge.check_row(r, t, 32, ON)
        r = self.row(); r['max_new_tokens'] = 4096
        with self.assertRaises(ValueError): merge.check_row(r, t, 32, ON)

    def test_scorer_reads_record_thinking(self):
        t = dict(self.tasks[self.row()['key']])
        with self.assertRaises(ValueError): score_item(t, '3', 1, cap=4096)
        seen = []; orig = official.extract_q35_final_answer
        def spy(raw, enable_thinking): seen.append(enable_thinking); return orig(raw, enable_thinking)
        official.extract_q35_final_answer = spy
        try:
            score_item(dict(t, thinking=False), str(t['ground_truth']), 1, cap=4096)
            score_item(dict(t, thinking=True), 'x\n</think>\n\n'+str(t['ground_truth']), 5)
        finally:
            official.extract_q35_final_answer = orig
        self.assertEqual(seen, [False, True])
        off = score_item(dict(t, thinking=False), str(t['ground_truth']), 1, cap=4096)
        self.assertEqual(off['score'], 1.0); self.assertFalse(off['hit_token_cap'])

    def test_full_real_journal_reproduces_provisional_remerge(self):
        from provenance import annotate
        from token_audit import load_tokenizer
        cfg=real_cfg()
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'0';out.mkdir()
            annotate(RES/'bundle/k1/0.json',RES.parent/'aws_vl64r/kit/k/0.tar',RES/'o/0/g0.jsonl',out/'g0.jsonl',0)
            (out/'p0_9001993.json').write_bytes((RES/'o/0/p0_9001993.json').read_bytes())
            cfg['output']=d
            tokenizer=load_tokenizer(cfg,'/scratch/jjyeung/orch_cd/mdg_build/work/t0bundle/base',ROOT/'inputs/base_manifest.json')
            b=merge.merge(cfg,0,'9001993',tokenizer=tokenizer)['benchmarks']['revsi']
        ref=json.loads((RES/'o/0/summary_9001993.json').read_text())['benchmarks']['revsi']
        self.assertEqual(b,ref)

    def test_bind_cells(self):
        art = 'cp1m200=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/f2ad01ad/runs/49becb79/m200/artifact.json@c1a4258816b3f561c9891f74cc1138780900de5cd890320161d2c94c85a86f67'
        art_t0 = 't0m800=/scratch/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap/244cdf20/runs/e59f7158/m800/artifact.json@5e160dd8e6ebbdd0eb9170e9b6844bde7deeb394be28c4e4167293e4af7e686c'
        AA = '/lustre/fsw/portfolios/av/projects/av_dataengine_cot/users/jyeung/ap'
        def bind(cells, cand, tag):
            d = ROOT/'checks'/('TEST_'+tag); d.mkdir(parents=True, exist_ok=True)
            (d/'cells.json').write_text(json.dumps(cells))
            cmd = [sys.executable, '-I', '-s', '-B', 'local/bind_vl.py', '--preset', 'custom', '--cells', str(d/'cells.json'), '--candidate', cand,
                   '--models', 'inputs/MODELS.json', '--gpus', '1', '--gpu-cap', '32', '--other-gpus', '0', '--remote-root', AA+'/0000beef',
                   '--artifact-dir', str(d), '--until', (__import__('datetime').datetime.now(__import__('datetime').timezone.utc)+__import__('datetime').timedelta(minutes=60)).strftime('%Y-%m-%dT%H:%M:%SZ'),
                   '--revsi-set', 'official999', '--revsi-tier', '32', '--revsi-video-root', AA+'/5a1c32e0/f', '--build-only']
            return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=os.environ.get('PYTHONPATH', '')))
        ok = bind([dict(ON, model='cp1m200')], art, 'cp1on'); self.assertEqual(ok.returncode, 0, ok.stderr[-800:])
        ok = bind([OFF], art_t0, 't0off'); self.assertEqual(ok.returncode, 0, ok.stderr[-800:])
        req = json.loads((ROOT/'checks/TEST_t0off/inputs/REQUEST.json').read_text())
        self.assertEqual(req['cells'], [OFF])
        for bad in ([dict(ON, thinking=None)], [dict(OFF, max_tokens=16384)], [dict(ON, layout='spread')],
                    [{k: v for k, v in OFF.items() if k != 'thinking'}], [dict(OFF, benchmarks=['vsi500'])]):
            out = bind(bad, art_t0, 'bad'); self.assertNotEqual(out.returncode, 0, bad)
            self.assertRegex(out.stderr.strip().splitlines()[-1], 'THINK-0|Require explicit thinking|Thinking cells', bad)


if __name__ == '__main__':
    unittest.main()
