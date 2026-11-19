"""Regressions for review findings, including t2, t3 and t4 equivalents."""
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
import test_callrate as fixtures
from test_callrate import ROOT, IO, SC, BASE, OUT3, item, row, gap
from callrate import analyze, main, read_strata, summary
from measurements import measure, summarize
from return_reader import Inputs


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.LoaderTests()
        self.fixture.setUp()
        self.work = self.fixture.work

    def run_cli(self, extra=()):
        f = self.fixture
        args = ['--a', str(f.ret), '--a-step', '400', '--a-package', str(f.package),
                '--b', str(f.ret), '--b-step', '400', '--b-package', str(f.package),
                '--scorer-src', str(IO.root/OUT3/'A4/src'), '--baseline-root', str(BASE),
                '--out', str(self.work/'output'), '--summary', *extra]
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = main(args)
        result = json.loads((self.work/'output/callrate.json').read_text())
        return code, out.getvalue(), err.getvalue(), result

    def test_t2_partial_summary_refuses_and_opt_in_has_banner_and_coverage(self):
        f = self.fixture
        f.manifest['items'].append({**item(), 'id':'missing'})
        path = f.package/'src/items/devs1_routed.json'
        f.write(path, f.manifest)
        import hashlib
        f.env['binding']['items_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
        f.write(f.journal/'environment.json', f.env)
        code, out, err, result = self.run_cli()
        self.assertEqual(code, 2)
        self.assertEqual(out, '')
        self.assertEqual(len(err.splitlines()), 1)
        self.assertIn('PARTIAL', err)
        code, out, err, result = self.run_cli(['--allow-partial'])
        self.assertEqual(code, 0)
        self.assertEqual(err, '')
        self.assertTrue(out.startswith('PARTIAL:'))
        self.assertIn('object_abs_distance | 1/2 / 1/2', out)
        self.assertIn('unit=m | 1/2 / 1/2', out)
        self.assertEqual(result['status'], 'PARTIAL')

    def test_t2_unequal_completed_sets_require_subset_and_share_marginals(self):
        ai = {'synthetic':item(), 'missing':{**item(), 'id':'missing'}}
        ar = {'synthetic':row([gap()])}
        br = {**ar, 'missing':{**row(), 'id':'missing'}}
        with self.assertRaisesRegex(ValueError, 'ID sets differ'):
            analyze(ar, ai, br, ai, SC)
        types, per = analyze(ar, ai, br, ai, SC, allow_subset=True)
        value = types['object_abs_distance']
        self.assertEqual(value['a']['n'], value['b']['n'])
        self.assertEqual(value['b']['call_rate'], 1)
        self.assertEqual(value['b']['expected'], 2)
        self.assertEqual(set(per['a']), set(per['b']))
        self.assertEqual(value['coverage']['b']['n'], 2)

    def test_t3_existing_absolute_link_survives_original_root_overlap(self):
        original = self.work/'original'; original.mkdir()
        copied = self.work/'copy'; copied.mkdir()
        (original/'value').write_text('live')
        (copied/'value').write_text('stale')
        link = self.work/'link'; link.symlink_to(original/'value')
        reader = Inputs(copied, original)
        self.assertEqual(reader.data(link), b'live')
        self.assertEqual(link.readlink(), original/'value')

    def test_relocate_only_missing_links_under_original_root(self):
        original = self.work/'absent'
        copied = self.work/'copy'; copied.mkdir()
        (copied/'value').write_text('copied')
        link = self.work/'link'; link.symlink_to(original/'value')
        self.assertEqual(Inputs(copied, original).data(link), b'copied')
        outside = self.work/'outside'; outside.symlink_to(self.work/'unrelated/value')
        with self.assertRaises(FileNotFoundError):
            Inputs(copied, original).data(outside)
        relative = self.work/'relative'; relative.symlink_to('absent/value')
        self.assertEqual(Inputs(copied, original).data(relative), b'copied')

    def test_t4_mismatched_populations_refuse_or_compare_intersection(self):
        ai = {'synthetic':item()}
        bi = {**ai, 'extra':{**item(), 'id':'extra'}}
        ar = {'synthetic':row([gap()])}
        br = {**ar, 'extra':{**row(answer='3'), 'id':'extra'}}
        with self.assertRaisesRegex(ValueError, 'ID sets differ'):
            analyze(ar, ai, br, bi, SC)
        types, per = analyze(ar, ai, br, bi, SC, allow_subset=True)
        value = types['object_abs_distance']
        self.assertEqual(value['set_sizes']['a'], 1)
        self.assertEqual(value['set_sizes']['b'], 2)
        self.assertEqual(value['a']['score'], value['b']['score'])
        self.assertEqual(value['a']['call_rate'], value['b']['call_rate'])
        self.assertEqual(value['paired']['score']['value'], 0)
        self.assertEqual(set(per['a']), set(per['b']))

    def test_usage_categories_and_conversion_failure_denominator(self):
        rows = []
        for answer, category in [('200','follow_converted'), ('2','copied_unconverted'), ('99','other')]:
            m = measure(row([gap(2)], answer=answer), item(unit='cm'), SC)
            rows.append(m)
            self.assertEqual(m['usage_category'], category)
            self.assertEqual(sum(m[k] for k in ('follow_converted','copied_unconverted','other')), 1)
            self.assertEqual(m['usage'], m['follow_converted']+m['copied_unconverted'])
        rows.append(measure(row([gap(2)], answer='2'), item(), SC))
        s = summarize(rows, ['synthetic'])
        self.assertEqual(s['usage'], .75)
        self.assertEqual(s['copied_unconverted'], .25)
        self.assertEqual(s['conversion_failure'], 1/3)
        self.assertEqual(s['conversion_failure_n'], 3)
        missing = measure(row(), item(), SC)
        self.assertIsNone(missing['usage_category'])
        self.assertIsNone(missing['follow_converted'])

    def test_explicit_units_zero_and_tolerance(self):
        for answer, category in [('2 m','follow_converted'), ('2 cm','copied_unconverted'), ('2.099','copied_unconverted'), ('2.101','other')]:
            self.assertEqual(measure(row([gap(2)], answer=answer), item(unit='cm'), SC)['usage_category'], category)
        self.assertEqual(measure(row([gap(0)], answer='0'), item(unit='feet'), SC)['usage_category'], 'follow_converted')

    def test_camera_and_room_unconverted_units(self):
        camera = item('camera_displacement', unit='cm')
        call = dict(call='<move from=1 to=2>', response='dx = 2 m, dy = 0 m, dz = 0 m, distance = 2 m')
        self.assertEqual(measure(row([call], answer='2'), camera, SC)['copied_unconverted'], 1)
        room = item('room_size_estimation'); room['question'] = 'Area in square feet?'
        call = dict(call='<ground mode="room">',response='room: frames 1,2\nfloor height 0.00 m\nfloor cells 400; supported cells 400; cell size 0.05 m; min frames 2\narea 1.00 m^2')
        self.assertEqual(measure(row([call], answer='1'), room, SC)['copied_unconverted'], 1)
        self.assertEqual(measure(row([call], answer='1 ft^2'), room, SC)['copied_unconverted'], 1)
        self.assertEqual(measure(row([call], answer=str((1/.3048)**2)), room, SC)['follow_converted'], 1)

    def test_parseable_answer_and_non_numeric_rates(self):
        for answer, parsed, not_seen, other in [('not seen',0,1,0), ('unknown',0,0,1), ('2',1,0,0), ('inf',0,0,1), ('',0,0,0)]:
            m = measure(row(answer=answer), item(), SC)
            self.assertEqual((m['answer'],m['not_seen'],m['other_non_numeric']), (parsed,not_seen,other))
        i = {**item('camera_movement_direction'), 'answer_type':'multiple_choice', 'ground_truth':'A', 'options':['A. left','B. right']}
        self.assertEqual(measure(row(answer='B'),i,SC)['answer'],1)
        for answer in ('unknown','C','not seen'):
            self.assertEqual(measure(row(answer=answer),i,SC)['answer'],0)

    def test_external_strata_rows_hashes_and_units(self):
        path = self.work/'strata.json'
        path.write_text(json.dumps({'synthetic':{'stratum':'HELDOUT', 'unit':'m'}}))
        code, out, err, result = self.run_cli(['--strata',str(path)])
        self.assertEqual(code,0)
        self.assertEqual(err,'')
        self.assertIn('stratum=HELDOUT | 1/1 / 1/1',out)
        self.assertIn('stratum=HELDOUT unit=m | 1/1 / 1/1',out)
        group = result['types']['object_abs_distance']['by_stratum']['HELDOUT']
        self.assertEqual(group['a']['score'], 1)
        self.assertEqual(group['paired']['call']['value'], 0)
        import hashlib
        self.assertIn(hashlib.sha256(path.read_bytes()).hexdigest(), {s['sha256'] for s in result['sources']})
        path.write_text(json.dumps({'synthetic':{'stratum':'HELDOUT', 'unit':'ft'}}))
        code, out, err, result = self.run_cli(['--strata',str(path)])
        self.assertEqual(code,2)
        self.assertIn('unit differs',err)

    def test_missing_stratum_is_explicit_not_guessed(self):
        ai = {'synthetic':item(), 'second':{**item(), 'id':'second'}}
        rows = {'synthetic':row(), 'second':{**row(), 'id':'second'}}
        types, _ = analyze(rows,ai,rows,ai,SC,strata={'synthetic':{'stratum':'TRAIN_DEV','unit':'m'}})
        self.assertEqual(types['object_abs_distance']['by_stratum']['MISSING']['a']['n'],1)


if __name__ == '__main__':
    unittest.main()
