"""Exercise positive cases and adversarial counting-form mutations."""
import hashlib, json, unittest
from pathlib import Path
from count_forms import render, validate

class Forms(unittest.TestCase):
    def test_valid_forms(self):
        cases = [([('chair', [])], 0), ([('chair', [(32, '')])], 1),
                 ([('notebook', [(1, ''), (9, ''), (15, '')])], 3),
                 ([('chair', [(3, 'left'), (3, 'left'), (7, 'right')])], 3),
                 ([('chair', [(3, ''), (3, '')]), ('table', [(1, '')])], 3),
                 ([('chair', [(i, '') for i in range(1, 33)])], 32)]
        for form in ('A', 'B'):
            for categories, answer in cases:
                with self.subTest(form=form, answer=answer):
                    inventory, totals = validate(render(categories, answer, form), answer, form)
                    self.assertEqual(sum(totals.values()), answer)

    def test_b_rejects_runaways_and_bad_counts(self):
        target = render([('chair', [(3, ''), (3, ''), (7, '')])], 3)
        mutations = [target.replace('2 of 3', '1 of 3'),
                     target.replace('2 of 3', '3 of 3'),
                     target.replace('2 of 3', '2 of 4'),
                     target.replace('I count 3', 'I count 4'),
                     target.replace('; 2 of 3, frame 3', ''),
                     target.replace('3 of 3, frame 7', '3 of 3, frame 7; 4 of 3, frame 7'),
                     target.replace('frame 7', 'frame 33'),
                     target.replace('frame 7', 'frame 0'),
                     target.replace('frame 7', '7 seconds'),
                     target.replace('frame 7', 'frame 7.0'),
                     target.replace('So there are 3', 'So there are 4'),
                     target + '\nStep 2: frame 7; frame 7.']
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError): validate(mutation, 3, 'B')

    def test_a_rejects_bad_tallies(self):
        target = render([('chair', [(3, ''), (3, ''), (7, '')])], 3, 'A')
        mutations = [target.replace('frame 7', 'frame 3'), target.replace('frame 7', 'frame 2'),
                     target.replace('frame 7', 'frame 33'), target.replace('frame 3', 'frame 0'),
                     target.replace('frame 3: 2', 'frame 3: 0'), target.replace('frame 3: 2', 'frame 3: 3'),
                     target.replace('total 3', 'total 4'), target.replace('frame 7: 1', 'frame 7: 1.5'),
                     target.replace('frame 7: 1', 'frame 7: 1; frame 7: 1')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                with self.assertRaises(ValueError): validate(mutation, 3, 'A')

    def test_multi_category_answer_and_region_guards(self):
        for form in ('A', 'B'):
            target = render([('chair', [(1, 'left'), (1, 'left')]), ('table', [(9, '')])], 3, form)
            for bad in [target.replace('2 + 1 = 3', '2 + 2 = 3'),
                        target.replace('2 + 1 = 3', '2 + 1 = 4'), target.replace('Step 2:', 'Step 3:'),
                        target.replace('So there are 3', 'So there are 5')]:
                with self.assertRaises(ValueError): validate(bad, 3, form)
            if form == 'A':
                with self.assertRaises(ValueError): validate(target.replace('left: 2', 'left: 1'), 3, form)
            else:
                with self.assertRaises(ValueError): validate(target.replace('(left)', '(rear)'), 3, form)
            with self.assertRaises(ValueError): validate(target, 4, form)

if __name__ == '__main__':
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Forms))
    root = Path(__file__).resolve().parent
    pins = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path(__file__), root / 'count_forms.py']}
    (root / 'out/CONTRACT_TESTS.json').write_text(json.dumps({'input_sha256': pins, 'status': 'PASS' if result.wasSuccessful() else 'FAIL',
         'test_methods': result.testsRun, 'positive_cases': 12, 'negative_mutations': 33,
         'failures': len(result.failures), 'errors': len(result.errors)}, indent=2) + '\n')
    raise SystemExit(not result.wasSuccessful())
