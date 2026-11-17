"""Fixtures, single-change rule mutations, sealed traces, and adversarial tests."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location('trace_grammar', ROOT / 'work/trace_grammar.py')
grammar = importlib.util.module_from_spec(spec)
spec.loader.exec_module(grammar)


def row(body, question='Where is the chair relative to the lamp?', options=('A. right', 'B. left'), answer='A', qtype='direction', form=None):
    selected = form or ('program' if qtype in grammar.PROGRAM_TYPES else 'direct')
    ending = '\n<answer>' + str(answer) + '</answer>' if selected == 'program' else '\n\n' + str(answer)
    result = dict(target='<think>\n' + body + '\n</think>' + ending,
                  question=question, options=list(options), answer=answer, question_type=qtype)
    if form:
        result['form'] = form
    return result


DIRECTION = '''Step 1: find the sink, the sofa and the stove.
Step 2: standing at the sink and facing the sofa, the stove is ahead of me to the right.
The question has me face the sofa, so no turn applies.
So the stove is to the right.'''
RELATIVE = '''Step 1: the backpack is first seen in frame 9.
Step 2: order the candidates from nearest to the backpack: pillow, bed, bag, badge.
The question asks for the closest: the pillow.'''
SIZE = '''Step 1: the kitchen counter is first seen in frame 11.
Step 2: the question asks for the longest of its three dimensions, in centimeters. I estimate that edge from the frames.'''
COUNT = '''Step 1: list each distinct notebook once, by the frame where it first appears: frame 1; frame 9; frame 15.
So there are 3 notebooks.'''
ROUTE = '''Step 1: I stand at the toilet facing the shower curtain. The bathroom vanity is to my left: turn left.
Step 2: I go forward to the bathroom vanity and keep that heading. The tissue box is to my left: turn left.
The turns are: left, left.'''
AWAY = '''Seen: toilet in frame 27; keyboard in frame 6; sofa in frame 16.
If I stood at the toilet facing the keyboard, the sofa would be ahead of me, slightly to my right.
The question has me face away from the keyboard. That is a half turn: what was ahead is now behind me, what was behind is now ahead, and left and right swap.
So the sofa is at my back.'''
PROGRAM = '''I will ground the boxes and ask the tool to measure their box distance.
<ground obj="clock" mode="box">
<tool_response>
clock: frames 27,28 (best 28)
B1: f1 centre (0.82, 0.36, -0.07) m
size 0.21 x 0.28 x 0.32 m
yaw -70 deg (0 = +x; positive +x toward -z about +y)
</tool_response>
<ground obj="lamp" mode="box">
<tool_response>
lamp: frames 1,2,3,4,5,32 (best 5)
B2: f1 centre (-0.49, -0.49, 1.44) m
size 0.36 x 0.34 x 1.82 m
yaw -70 deg (0 = +x; positive +x toward -z about +y)
</tool_response>
<gap a="clock" b="lamp" rule="box_grid_5cm">
<tool_response>
distance 1.60 m
</tool_response>
The box distance is 1.60 meters.'''
ROOM = '''I will project the depth points onto the floor and measure their covered area.
<ground mode="room">
<tool_response>
room: frames 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32
floor height -0.07 m
floor cells 7002; supported cells 5374; cell size 0.05 m; min frames 1
area 17.51 m^2
</tool_response>
The covered floor area is 17.51 square meters.'''
FIXTURES = {
    'direction': row(DIRECTION, 'If I am standing by the sink and facing the sofa, is the stove to the left or the right of the sofa?', ('A. right', 'B. left')),
    'relative': row(RELATIVE, 'Measuring from the closest point of each object, which of these objects (bag, pillow, badge, bed) is the closest to the backpack?', ('A. bag', 'B. pillow', 'C. badge', 'D. bed'), 'B'),
    'size': row(SIZE, 'What is the length of the longest dimension (length, width, or height) of the kitchen counter, measured in centimeters?', (), '101', 'object_size_estimation'),
    'count': row(COUNT, 'How many notebook(s) are in this room?', (), '3', 'object_counting'),
    'route': row(ROUTE, 'Starting at the toilet facing the shower curtain, go to the bathroom vanity and then the tissue box. Which turns are needed?', ('A. Turn Right, Turn Left', 'B. Turn Left, Turn Left', 'C. Turn Back, Turn Right', 'D. Turn Right, Turn Right'), 'B', 'route_planning'),
    'away': row(AWAY, 'If I stand at the toilet facing away from the keyboard, is the sofa left, right, or back?', ('A. left', 'B. right', 'C. back'), 'C'),
    'program': row(PROGRAM, 'What is the distance from clock to lamp?', (), '1.60', 'object_abs_distance'),
    'conversion': row(PROGRAM + '\nConverting to feet: 1.60 x 3.28084 = 5.25.', 'What is the distance from clock to lamp in feet?', (), '5.25', 'object_abs_distance'),
    'room': row(ROOM, 'What is the room floor area?', (), '17.51', 'room_size_estimation'),
}
BASE = row('The chair is seen in frame 7.\nSo the chair is to the right.')


def replace_body(source, body):
    start, end = source['target'].index('<think>') + len('<think>'), source['target'].index('</think>')
    return {**source, 'target': source['target'][:start] + '\n' + body + '\n' + source['target'][end:]}


class ValidatorTests(unittest.TestCase):
    def assertPass(self, item):
        errors = grammar.validate_row(item)
        self.assertEqual(errors, [], errors)

    def assertRule(self, item, rule):
        errors = grammar.validate_row(item)
        self.assertIn(rule, {e.rule_id for e in errors}, errors)

    def test_required_fixtures(self):
        for name, fixture in FIXTURES.items():
            with self.subTest(fixture=name):
                self.assertPass(fixture)
        self.assertPass(BASE)

    def mutation(self, text, rule, source=BASE):
        self.assertPass(source)
        self.assertRule(replace_body(source, text), rule)

    def test_mutation_direct_call(self):
        self.mutation('The chair is seen in frame 7.\n<ground obj="chair">\nSo the chair is to the right.', 'direct_call')

    def test_call_attributes_are_syntax_in_program_only(self):
        for call in ['<gap a="clock" b="lamp" rule="box_grid_5cm">',
                     '<ground obj="x" mode="box">',
                     '<ground obj="two lamps 999cm" mode="box">',
                     '<custom.v2 value="123 m" count="two" frame="999">']:
            with self.subTest(call=call):
                self.assertPass(row(call, form='program'))
                self.assertRule(row('The chair is seen in frame 7.\n' + call, form='direct'), 'direct_call')

    def test_call_attributes_do_not_license_prose(self):
        call = '<measure value="98765cm" arithmetic="11 x 11 = 121">'
        for text in ['The chair is 98765 cm to the right.', 'The chair is 121 cm to the right.']:
            self.assertRule(row(call + '\n' + text, form='program'), 'number_not_allowed')
        self.assertRule(row(call + ' The chair is 98765 cm to the right.', form='program'), 'unit_quantity')

    def test_sealed_distance_explanation_has_no_exception(self):
        line = "The box gap is the smallest distance between points on a 5 cm grid over the two objects' full boxes, taken over every pair of instances."
        fixture = row('<gap rule="box_grid_5cm">\n' + line, form='program')
        for rule in ['number_not_allowed', 'unit_quantity', 'number_word']:
            self.assertRule(fixture, rule)
        self.assertPass(row('<gap rule="box_grid_5cm">\n' + line.replace('a 5 cm grid over the two', 'a grid over both'), form='program'))

    def test_mutation_empty_think(self):
        self.mutation('  ', 'empty_think', FIXTURES['route'])

    def test_mutation_layout(self):
        self.assertPass(BASE)
        self.assertRule({**BASE, 'target': BASE['target'].replace('\n\nA', '\nA')}, 'layout')

    def test_mutation_number_not_allowed(self):
        self.mutation('The chair is seen in frame 7.\nSo the chair is 83 to the right.', 'number_not_allowed')

    def test_mutation_frame_range(self):
        self.mutation('The chair is seen in frame 40.\nSo the chair is to the right.', 'frame_range')

    def test_mutation_unit_quantity(self):
        self.mutation('The chair is seen in frame 7.\nSo the chair is 120cm tall.', 'unit_quantity')

    def test_mutation_number_word(self):
        self.mutation('The chair is seen in frame 7.\nSo there are two chairs.', 'number_word')

    def test_mutation_letter_restatement(self):
        self.mutation('The chair is seen in frame 7.\nSo the answer is A.', 'letter_restatement')

    def test_mutation_no_evidence(self):
        self.mutation('The pineapple is to the right.', 'no_evidence', row('The chair is to the right.'))

    def test_mutation_filler_only(self):
        self.mutation('Step 1: I look at the video.', 'filler_only', row('Step 1: The chair is to the right.'))

    def test_mutation_exhaustive_frames(self):
        self.mutation('The chair is seen in frames 7, 8, 9.\nSo the chair is to the right.', 'exhaustive_frames')

    def test_mutation_absence_claim(self):
        self.mutation('The chair is absent in frame 7.\nSo the chair is to the right.', 'absence_claim')

    def test_mutation_stated_estimate(self):
        self.assertPass(FIXTURES['size'])
        changed = dict(FIXTURES['size'])
        changed['target'] = changed['target'].replace('I estimate that edge from the frames.', 'I estimate that edge as 101.')
        self.assertRule(changed, 'stated_estimate')

    def test_mutation_line_kind(self):
        self.mutation('The chair is seen in frame 7.\nPurple marmalade sings.', 'line_kind')

    def test_mutation_angle_or_coordinate(self):
        self.mutation('The chair is seen in frame 7.\nSo the chair has bearing right.', 'angle_or_coordinate')

    def test_adversarial_numeric_spelling(self):
        for text in ['２', '٢', '1st', '3-4 frames', '~2', '(2)', 'x2', '10%', '2e3', '3/4', '-2', '+2', '.2', '−2', '2️⃣', '²']:
            with self.subTest(text=text):
                self.assertRule(row('The chair is seen in frame 7.\nSo there are ' + text + ' chairs.'), 'number_not_allowed')

    def test_adversarial_number_words(self):
        for text in ['II chairs', 'ii chairs', 'a pair of chairs', 'a dozen chairs', 'about half a meter', 'half a metre', 'half an inch', 'a couple of chairs', 'one and a half chairs', 'a third', 'twice', 'double', 'quarter', 'twenty chairs', 'ninety chairs', 'hundred chairs', 'thousand chairs', 'zero chairs']:
            with self.subTest(text=text):
                self.assertRule(row('The chair is seen in frame 7.\nSo there are ' + text + '.'), 'number_word')

    def test_adversarial_words_and_pronouns_pass(self):
        for text in ['The chair is first.', 'The chair is second.', 'The chair is third.', 'So there are several chairs.', 'So the chair is the nearest one.', 'So the chair is the nearest one in frame 7.', 'So the chair is the nearest one).', 'So the chair is this one.', 'So the chair is each one.', 'So the chair is which one.', 'I list the chairs one by one.', 'I list each chair once.', 'The chair is behind me after a half turn.', 'The chair is behind me after half turn.']:
            with self.subTest(text=text):
                self.assertPass(row('The chair is seen in frame 7.\n' + text))
        for text in ['The nearest one chair is right.', 'This one meter is right.', 'Each one notebook is right.']:
            self.assertRule(row(text), 'number_word')

    def test_adversarial_word_frames(self):
        for text in ['The chair is seen in frame twelve.', 'The chair is seen in frame XII.']:
            self.assertRule(row(text), 'number_word')

    def test_adversarial_frame_context(self):
        for text in ['The chair is seen in frame 0.', 'The chair is seen in frame -1.', 'The chair is seen in frame 3.5.', 'The chair is seen in frame ٣.', 'The chair is seen in frame 33.']:
            self.assertRule(row(text), 'frame_range')
        self.assertPass(row('Seen: chair in frame 3; lamp in frame 9.'))
        self.assertPass(row('The first chair is seen in frame 3; the second chair in frame 9.'))
        self.assertRule(row('The chair is seen in frame 3 and frame 9.'), 'exhaustive_frames')
        self.assertRule(row('chair: frames 4,5,6'), 'exhaustive_frames')
        self.assertRule({**BASE, 'frame_indices': [100, 200]}, 'frame_range')
        self.assertRule({**BASE, 'frame_indices': []}, 'frame_range')

    def test_adversarial_absence(self):
        for text in ['not visible in frame', 'not seen in frame', 'missing from frame', 'absent in']:
            self.assertRule(row('The chair is ' + text + ' 7.'), 'absence_claim')

    def test_adversarial_letter_only(self):
        for text in ['So the answer is A.', 'The answer is B.', 'Option A is correct.', 'A is correct.', 'The correct option is C.', 'Relate: The answer is A.', 'I choose D.', 'Answer: A', 'A', 'So, the answer is A.']:
            self.assertRule(row(text), 'letter_restatement')
            self.assertRule(row(text), 'no_evidence')
        self.assertRule(row('The answer is A.', form='program'), 'letter_restatement')
        for text in ['The answer is A.', 'Option C is correct.', 'D is correct.', 'I choose D.', 'Relate: The answer is C.']:
            self.assertPass(row('<move>\n' + text, form='program'))

    def test_adversarial_tool_response(self):
        self.assertRule(row('<ground obj="chair">\n<tool_response>\nchair 4 m\n</tool_response>'), 'direct_call')
        self.assertRule(row('The chair is right.\n</tool_response>'), 'direct_call')
        self.assertRule(row('<ground>\n<tool_response>\n2.40 m', form='program'), 'layout')
        self.assertRule(row('<ground>\n<tool_response>\n1.60 m\n</tool_response>\nThe distance is 2.40 meters.', form='program'), 'unit_quantity')
        self.assertRule(row('<ground>\n<tool_response>\n1.60 m\n</tool_response>\nThe distance is 2.40 meters.', form='program'), 'number_not_allowed')
        self.assertPass(row('<ground>\n<tool_response>response: anything 999 m; two hundred\n</tool_response>\nThe distance is 999 m.', form='program'))
        errors = grammar.validate_trace('The distance is 1.6 m.', form='program', printed_text='distance 1.60 m')
        self.assertEqual(errors, [])
        self.assertIn('unit_quantity', {e.rule_id for e in grammar.validate_trace('So the chair is 1.6 m.', form='direct', question='chair', printed_text='1.6 m')})

    def test_adversarial_units(self):
        for unit in ['m', 'meters', 'metre', 'cm', 'centimeters', 'mm', 'km', 'inch', 'inches', 'in', 'ft', 'foot', 'feet', 'yards', 'square', 'sq', 'm2', 'm^2', 'm²', 'degrees', 'degree', 'deg', '°']:
            self.assertRule(row('The chair is 8' + unit + ' right.'), 'unit_quantity')
        self.assertPass(row('<ground>\n<tool_response>area 17.51 m^2</tool_response>\nThe area is 17.51 m^2.', form='program'))
        self.assertPass(row('<ground>\n<tool_response>distance 1.604 m</tool_response>\nThe distance is 1.60 meters.', form='program'))
        self.assertRule(row('The chair is 8 m right.', question='Is the chair 8 m tall?'), 'unit_quantity')
        self.assertRule(row('The distance is 8 m.', question='Is the distance 8 m?', form='program'), 'unit_quantity')

    def test_adversarial_coordinates(self):
        for text in ['(x, y, z)', '(1, 2, 3)', '(1, 2)', 'cross', 'dot', 'atan2', 'theta', 'bearing', 'degrees']:
            self.assertRule(row('The chair is right at ' + text + '.'), 'angle_or_coordinate')

    def test_question_constants(self):
        self.assertPass(row('So there are three chairs.', question='Are there three chairs?'))
        self.assertPass(row('So there are three chairs.', question='Are there 3 chairs?'))
        self.assertPass(row('So there are 12 chairs.', options=('A. 12 chairs',)))
        self.assertRule(row('So there are three chairs.', options=('A. three chairs',)), 'number_word')
        self.assertRule(row('The chair has three dimensions.', question='Where is the chair?'), 'number_word')
        self.assertRule(row('The chair has three dimensions.', question='What are the chair length and width?'), 'number_word')
        self.assertRule(row('So there are three chairs.', question='What are the chair length, width and height?'), 'number_word')

    def test_labels(self):
        self.assertPass(row('Step 1. The chair is right.\nStep 2. The chair is ahead.'))
        for body in ['Step 2: The chair is right.', 'Step 1: The chair is right.\nStep 3: The chair is ahead.', 'Step 1: The chair is right.\nStep 1: The chair is ahead.']:
            self.assertRule(row(body), 'number_not_allowed')

    def test_counting(self):
        for qtype in ['absolute_count', 'relative_count_total', 'object_counting']:
            self.assertPass(row('List distinct chairs: red; blue.\nSo there are 2 chairs.', question='How many chairs?', options=(), answer='2', qtype=qtype))
            self.assertRule(row('List distinct chairs: red; blue.\nSo there are 3 chairs.', question='How many chairs?', options=(), answer='3', qtype=qtype), 'stated_estimate')
        self.assertRule(row('So there are 3 chairs.\nList distinct chairs: red; blue; green.', question='How many chairs?', options=(), answer='3', qtype='absolute_count'), 'number_not_allowed')
        self.assertPass(row('List chairs: red; blue.\nList lamps: yellow, white, black.\nThe total is 2 + 3 = 5.', question='How many chairs and lamps?', options=(), answer='5', qtype='absolute_count'))
        self.assertPass(row('List instances of chair: red.\nSo there are 1 chairs.', question='How many chairs?', options=(), answer='1', qtype='absolute_count'))
        self.assertRule(row('List chairs: red;; blue.\nSo there are 3 chairs.'), 'number_not_allowed')

    def test_arithmetic_operations(self):
        for expression in ['2 + 3 = 5', '3 - 2 = 1', '3 − 2 = 1', '2 x 3 = 6', '2 * 3 = 6', '2 × 3 = 6', '2 / 3 = 0.67', '2 / 3 = 0.7', '3 / 2 = 1.5', '3 / 2 = 2', '3 / 2 = 3/2']:
            with self.subTest(expression=expression):
                self.assertPass(row('The chair is right.\nThe total is ' + expression + '.', question='The chair has constants 2 and 3.'))
        for expression in ['2 + 3 = 6', '2 x 3 = 99', '2 / 0 = 7', '99 + 2 = 101', '2 / 3 = 0.66']:
            self.assertRule(row('The chair is right.\nThe total is ' + expression + '.', question='The chair has constants 0, 2 and 3.'), 'number_not_allowed')
        self.assertPass(row('<gap>\n<tool_response>distance 1.60 m</tool_response>\nConverting to feet: 1.60 x 3.28084 = 5.25 ft.', form='program'))
        self.assertRule(row('<gap>\n<tool_response>distance 1.60 m</tool_response>\nConverting to feet: 1.60 x 3.28084 = 5.24 ft.', form='program'), 'unit_quantity')
        self.assertRule(row('So the chair is 100 right.'), 'number_not_allowed')
        self.assertEqual(grammar.validate_row(row('The chair is right.\nThe total is 2 + 3 = 5.\nThe total is 5.', question='The chair has constants 2 and 3.')), [])
        self.assertPass(row('The chair is right.\nThe total is 2 + 3 = 5; then 5 + 2 = 7.', question='The chair has constants 2 and 3.'))
        self.assertPass(row('The chair is right.\nThe total is 2 / 100 = 2%.', question='The chair has constant 2.'))
        self.assertRule(row('The chair is right.\nThe total is 2 / 100 = 3%.', question='The chair has constant 2.'), 'number_not_allowed')

    def test_stated_estimate_rounding(self):
        for value in ['101.234', '101.23', '101.2', '101']:
            self.assertRule(row('So the chair is ' + value + ' long.', options=(), answer='101.234'), 'stated_estimate')
        self.assertPass(row('The chair is seen in frame 7.', options=(), answer='101.234'))

    def test_build1b_estimate_structural_numbers(self):
        question = 'What is the length of the longest edge of the webcam, in centimeters?'
        for body, answer in [
            ('Step 1: the webcam is first seen in frame 20.', '20'),
            ('Step 1: the webcam is first seen in frame 20.', '1'),
            ('Step 1: find the webcam.\nStep 2: the webcam is to the right.', '2'),
        ]:
            with self.subTest(body=body, answer=answer):
                self.assertPass(row(body, question, (), answer))
        for body, other_rule in [
            ('The webcam is seen in frames 3 and 20.', 'exhaustive_frames'),
            ('The webcam is seen in frame 40.', 'frame_range'),
            ('Step 20: find the webcam.', 'number_not_allowed'),
        ]:
            with self.subTest(body=body):
                errors = grammar.validate_row(row(body, question, (), '40' if '40' in body else '20'))
                self.assertNotIn('stated_estimate', {e.rule_id for e in errors})
                self.assertIn(other_rule, {e.rule_id for e in errors})
        for body in ['It is about 20 across.', 'The webcam is seen in frame 20. It is about 20 across.']:
            with self.subTest(body=body):
                self.assertRule(row(body, question, (), '20'), 'stated_estimate')

    def test_build1b_fraction_quantities(self):
        for phrase in ['a fifth of a meter', 'a tenth', 'three quarters', 'two thirds',
                       'one fifth', 'a half of', 'halfway to a meter', 'a fourth',
                       'half of a meter', 'a sixth', 'seven eighths']:
            with self.subTest(phrase=phrase):
                self.assertRule(row('The chair is to the right by ' + phrase + '.'), 'number_word')
        self.assertRule(row('The chair is to the right by three quarters.', question='Are there three chairs?'), 'number_word')

    def test_build1b_fraction_position_and_ordinals(self):
        for text in ['The chair is halfway between the sofa and the bed.',
                     'The chair is the fifth object to the right.',
                     'The chair is first.', 'The chair is second.',
                     'The chair is the tenth object to the right.']:
            with self.subTest(text=text):
                self.assertPass(row(text))

    def test_build1b_inline_choices(self):
        for text in ['The sofa is to the right, so I pick B.',
                     'The sofa is to the right, hence option C',
                     'The sofa is to the right, which is (A)', 'so B.', 'answer: D',
                     'The sofa is right; I select C because it is near.',
                     'The sofa is right, therefore B.',
                     'The sofa is right; the answer is D.']:
            with self.subTest(text=text):
                self.assertRule(row(text, question='Where is the sofa?'), 'letter_restatement')
                self.assertRule(row(text, form='program'), 'letter_restatement')
                self.assertPass(row('<move>\n' + text, form='program'))
                self.assertRule(row(text + '\n<move>', form='program'), 'letter_restatement')

    def test_build1b_choice_names_and_quotes(self):
        for text in ['The TV is on my left.', 'I stand to the left of the TV.',
                     'The TV is left, so I face it.', 'The TV is left of Bob.',
                     'The TV is left; I pick Bob as the reference.',
                     'The question asks "Is the TV on the left, hence option C?" The TV is left.',
                     "The question asks ‘Is the TV left, so B?’ The TV is left.",
                     'The question asks "answer: D". The TV is left.']:
            with self.subTest(text=text):
                question = 'answer: D' if '"answer: D"' in text else 'Where is the TV?'
                self.assertPass(row(text, question=question, options=('A. TV left',)))
        errors = grammar.validate_row(row('I'))
        self.assertNotIn('letter_restatement', {e.rule_id for e in errors})
        self.assertRule(row('The chair is right by a fifth of a meter, so I pick B.'), 'number_word')
        self.assertRule(row('The question asks "Is the chair left, so A?" I pick B.'), 'letter_restatement')

    def test_layout(self):
        for fixture in [BASE, FIXTURES['program']]:
            self.assertPass({**fixture, 'target': fixture['target'] + '\n'})
            for target in [fixture['target'] + '\n\n', ' ' + fixture['target'], fixture['target'].replace('<think>', ''), fixture['target'].replace('</think>', ''), fixture['target'].replace('<think>\n', '<think>'), fixture['target'] + ' ', fixture['target'] + 'wrong']:
                self.assertRule({**fixture, 'target': target}, 'layout')
            self.assertRule({**fixture, 'answer': 'wrong'}, 'layout')
        self.assertRule(row('The chair is right.\n<answer>A</answer>'), 'layout')
        self.assertRule(row('The chair is right.\n<think>'), 'layout')
        self.assertRule(row('', qtype='route_planning'), 'empty_think')
        self.assertRule(row('', qtype='box_3d', options=(), answer='{}'), 'empty_think')
        self.assertRule({k: v for k, v in BASE.items() if k != 'answer'}, 'layout')
        self.assertRule({**BASE, 'target': 17}, 'layout')
        self.assertRule({**BASE, 'form': 'unknown'}, 'layout')
        self.assertEqual(grammar.validate_row([])[0].rule_id, 'layout')

    def test_type_inference(self):
        for key in ['question_type', 'type', 'category']:
            for qtype in grammar.PROGRAM_TYPES:
                fixture = {k: v for k, v in FIXTURES['program'].items() if k != 'question_type'}
                fixture[key] = qtype
                self.assertPass(fixture)
        self.assertRule({**BASE, 'question_type': 'object_abs_distance'}, 'layout')
        self.assertPass({**BASE, 'question_type': 'object_abs_distance', 'form': 'direct'})
        self.assertPass({**BASE, 'question_type': 'camera_object_absolute_distance'})
        self.assertPass({k: v for k, v in BASE.items() if k != 'question_type'})

    def test_additional_provenance_and_citation_mutations(self):
        for expression in ['2 + 3 = 2', '2 / 0 = 2', '2 + ٣ = 5', '2 + 3 = ' + '9' * 101]:
            self.assertRule(row('The total is ' + expression + '.', question='The chair has constants 0, 2, 3 and 5.'), 'number_not_allowed')
        for body in ['The chair is first seen in frame 7 and frame 9.', 'The chair is seen in frame 7; the chair is seen in frame 9.', 'The chair is seen in frame 7, and in frame 9.']:
            self.assertRule(row(body), 'exhaustive_frames')
        self.assertPass(row('Seen: chair in frame 3, lamp in frame 9.'))
        self.assertPass(row('The first chair is in frame 3; the second chair is in frame 9.'))
        self.assertPass(row('Seen: the chair is in frame 3 and the lamp is in frame 9.'))
        for unit in ['m2', 'm^2', 'm²']:
            self.assertPass(row('<ground>\n<tool_response>area 17.51 ' + unit + '</tool_response>\nThe area is 17.51' + unit + '.', form='program'))
        self.assertRule(row('The chair is at random².'), 'number_not_allowed')
        self.assertRule(row('Step 3: The chair is right.', question='Are there 3 chairs?'), 'number_not_allowed')

    def test_api_and_line_numbers(self):
        for args in [dict(form='unknown'), dict(form='direct', n_frames=-1)]:
            with self.assertRaises(ValueError):
                grammar.validate_trace('chair', **args)
        errors = grammar.validate_trace('\nThe chair is seen in frame 7.\n\nSo there are 83 chairs.', form='direct', question='chair')
        failure = next(e for e in errors if e.rule_id == 'number_not_allowed')
        self.assertEqual((failure.line_no, failure.line), (4, 'So there are 83 chairs.'))
        self.assertEqual(failure._fields, ('rule_id', 'line_no', 'line', 'detail'))
        self.assertIsNone(grammar._value('9' * 101))
        self.assertIsNone(grammar._value('1/0'))
        self.assertIsNone(grammar._value('NaN'))
        self.assertIsNone(grammar._value('1e999'))
        self.assertIsNone(grammar._value('invalid'))
        self.assertFalse(grammar._equal('NaN', '1'))
        self.assertEqual(grammar._value('50%'), grammar.Decimal('.5'))

    def test_filler_and_unknown(self):
        for text in ['Let me analyze the frames.', 'I will answer carefully.']:
            self.assertRule(row(text), 'filler_only')
        self.assertRule(row('Purple marmalade sings.'), 'line_kind')
        self.assertRule(row('Purple marmalade sings.'), 'no_evidence')
        self.assertPass(row('I will ground the chair.', form='program'))

    def test_cli_stream_and_examples(self):
        path = ROOT / 'out/test_rows.jsonl'
        data = '\n'.join([json.dumps(BASE)] + [json.dumps(row('So the answer is A.'))] * 4 + ['{invalid', 'null', json.dumps({**BASE, 'question': 7})]) + '\n'
        stream = io.StringIO()
        with mock.patch('builtins.open', return_value=io.StringIO(data)), contextlib.redirect_stdout(stream):
            status = grammar.main(['--jsonl', str(path)])
        result = json.loads(stream.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual((result['rows'], result['passed'], result['failed']), (8, 1, 7))
        self.assertEqual(result['per_rule_counts']['letter_restatement'], 4)
        self.assertEqual(len(result['examples']['letter_restatement']), 3)
        for limit in ['0', '1']:
            with mock.patch('builtins.open', return_value=io.StringIO(data)), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(grammar.main(['--jsonl', str(path), '--limit', limit]), 0)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            grammar.main(['--jsonl', str(path), '--limit', '-1'])

    def test_cli_oversized_line_streaming(self):
        data = json.dumps(BASE) + '\n' + 'x' * (6 * 1024 * 1024) + '\n' + json.dumps(BASE) + '\n'
        stream = io.StringIO()
        with mock.patch('builtins.open', return_value=io.StringIO(data)), contextlib.redirect_stdout(stream):
            status = grammar.main(['--jsonl', 'synthetic-stream'])
        result = json.loads(stream.getvalue())
        self.assertEqual(status, 1)
        self.assertEqual((result['rows'], result['passed'], result['failed']), (3, 2, 1))
        self.assertIn('streaming bound', result['examples']['layout'][0]['detail'])

    def test_sealed_appendix_direction(self):
        cases = [
            ('sink', 'sofa', 'stove', '41', 'right', 'in front', 'A'),
            ('fireplace', 'shelf', 'tv', '61', 'left', 'in front', 'B'),
            ('refrigerator', 'table', 'oven', '92', 'left', 'behind', 'A'),
            ('cabinet', 'chair', 'tv', '106', 'left', 'a turn of less than 135 degrees', 'A'),
            ('bathtub', 'toilet', 'cabinet', '22', 'left', 'a turn of less than 135 degrees', 'B'),
            ('plant', 'sofa', 'backpack', '41', 'left', 'a turn of less than 135 degrees', 'C'),
            ('door', 'counter', 'microwave', '48', 'right', 'in front', 'B'),
            ('nightstand', 'bed', 'picture', '41', 'right', 'in front', 'B'),
            ('table', 'projector screen', 'cabinet', '112', 'right', 'behind', 'D'),
        ]
        for index, (anchor, facing, obj, angle, side, sector, answer) in enumerate(cases):
            conclusion = ('on my ' + side) if index in {3,4,5} else ('at my ' + ('back' if index == 8 else 'front') + '-' + side) if index >= 6 else ('to the ' + side)
            body = f'Step 1: locate the centres of the {anchor}, the {facing} and the {obj}.\nStep 2: standing at the {anchor} and facing the {facing}, the {obj} lies {angle} degrees {side} of straight ahead, {sector}.\nSo the {obj} is {conclusion}.'
            fixture = row(body, question=f'From {anchor}, facing {facing}, where is {obj}? ' + ('Back requires at least 135 degrees.' if index in {3,4,5} else ''), answer=answer)
            for rule in ['unit_quantity', 'number_not_allowed', 'angle_or_coordinate']:
                with self.subTest(index=index, rule=rule):
                    self.assertRule(fixture, rule)

    def test_sealed_appendix_relative(self):
        for anchor, frame, measurements, closest, answer in [
            ('backpack', 9, 'bag 2.23 m; pillow 0.64 m; badge 3.15 m; bed 1.25 m', 'pillow', 'B'),
            ('fireplace', 8, 'dishwasher 2.75 m; tv 0.61 m; sofa 0.16 m; stove 1.36 m', 'sofa', 'C'),
            ('kitchen cabinets', 6, 'plant 2.12 m; chair 1.23 m; radiator 2.45 m; table 1.73 m', 'chair', 'B'),
        ]:
            body = f'Step 1: find the {anchor} (first seen in frame {frame}) and each candidate.\nStep 2: measure the closest-point distance from the {anchor} to each: {measurements}.\nThe closest is the {closest}.'
            fixture = row(body, question=f'Which object is closest to the {anchor}?', answer=answer)
            self.assertRule(fixture, 'unit_quantity')
            self.assertRule(fixture, 'number_not_allowed')

    def test_sealed_appendix_size(self):
        for obj, frame, value in [('kitchen counter', 11, 101), ('cable raceway', 7, 201), ('baby bassinet', 5, 85)]:
            body = f'Step 1: find the {obj} (first seen in frame {frame}).\nStep 2: measure its 3D box; the longest edge is {value} cm.'
            fixture = row(body, question=f'What is the longest dimension of the {obj} in centimeters?', options=(), answer=str(value), qtype='object_size_estimation')
            self.assertRule(fixture, 'unit_quantity')
            self.assertRule(fixture, 'number_not_allowed')
            self.assertRule(fixture, 'stated_estimate')


class Build2SchemaTests(unittest.TestCase):
    def test_nested_schema_and_top_level_precedence(self):
        value = row(COUNT, question='How many notebooks?', options=(), answer='3', qtype='object_counting')
        value['student_input'] = {k: value.pop(k) for k in ('question', 'options')}
        value['student_input']['frame_indices'] = list(range(32))
        value['category'] = value.pop('question_type')
        self.assertEqual(grammar.validate_row(value), [])
        value['frame_indices'] = [0]
        self.assertIn('frame_range', {v.rule_id for v in grammar.validate_row(value)})

    def test_arithmetic_results_persist_but_do_not_precede_proof(self):
        body = ('Step 1: list each distinct chair once: frame 1; frame 2; frame 3.\n'
                'Step 2: list each distinct plant once: frame 1; frame 2; frame 3; frame 4; frame 5.\n'
                'Step 3: add them: 3 + 5 = 8.\nSo there are 8 in total.')
        value = row(body, question='How many chairs and plants in total?', options=(), answer='8', qtype='object_counting')
        self.assertEqual(grammar.validate_row(value), [])
        value['target'] = value['target'].replace('3 + 5 = 8', '3 + 5 = 9')
        self.assertIn('number_not_allowed', {v.rule_id for v in grammar.validate_row(value)})

    def test_in_preposition_and_inches(self):
        for phrase in ('in total', 'in frame 8', 'in the room', 'in 2 rooms'):
            value = row(COUNT.replace('3 notebooks.', '3 ' + phrase + '.'), question='How many notebooks?', options=(), answer='3', qtype='object_counting')
            self.assertNotIn('unit_quantity', {v.rule_id for v in grammar.validate_row(value)})
        value = row(COUNT.replace('3 notebooks.', '3 inches.'), question='How many notebooks?', options=(), answer='3', qtype='object_counting')
        self.assertIn('unit_quantity', {v.rule_id for v in grammar.validate_row(value)})


class Build4Tests(unittest.TestCase):
    assertPass = ValidatorTests.assertPass
    assertRule = ValidatorTests.assertRule
    def test_duplicate_labels(self):
        self.assertRule(row('Locate: chair in frame 2.\nSeen: chair in frame 3.'), 'duplicate_object')
        self.assertPass(row('Locate: chair a in frame 2.\nSeen: chair b in frame 3.'))
        self.assertPass(row('Step 1: list each distinct chair once: frame 5; frame 5.\nSo the count is 2.', options=(), answer='2', qtype='object_counting'))

    def test_named_object_semantics(self):
        # Diagnostic only: delivered source spellings fail, so the gate is not adopted.
        self.assertFalse(grammar._named_in_question('zebra', 'Where is the chair?', ()))
        self.assertFalse(grammar._named_in_question('cofee table', 'Detect the coffee table.', ()))
        self.assertTrue(grammar._named_in_question('chair', 'Where is the chair?', ()))
        self.assertPass(row('Seen: zebra in frame 3.\nThe chair is right.'))
        self.assertPass(row('Seen: chair in frame 3; lamp in frame 5.'))
        self.assertPass(row('Seen: trash bin(s) in frame 3.',question='Where are the trash bin(s)?'))
        self.assertPass(row('Seen: zebra in frame 3.', form='program'))

    def test_explicit_relate(self):
        self.assertRule(row('Relate: the chair is right.'), 'relate_without_locate')
        self.assertPass(row('Locate: chair in frame 2.\nRelate: the chair is right.'))
        self.assertPass(row('The chair is right.'))
        self.assertPass(row('Relate: the chair is right.', form='program'))

    def test_frame_units(self):
        for unit in ['seconds', 's', 'ms', 'cm', 'degrees']:
            self.assertRule(row('Seen: chair in frame 2 '+unit+'.'), 'frame_unit')
        self.assertPass(row('Seen: chair in frame 2.'))

    def test_explicit_list_count(self):
        prefix = 'Locate: chair a in frame 1.\nLocate: chair b in frame 2.\n'
        self.assertRule(row(prefix+'Step: list [chair a; chair b]; count = 3.'), 'list_count')
        self.assertNotIn('number_not_allowed', {e.rule_id for e in grammar.validate_row(row(prefix+'Step: list [chair a; chair b]; count = 3.'))})
        self.assertPass(row(prefix+'Step: list [chair a; chair b]; count = 2.'))

    def test_word_quantities(self):
        for phrase in ['a metre', 'about a metre', 'a few metres', 'several metres', 'a metre-long object']:
            self.assertRule(row('The chair is '+phrase+' to my right.'), 'unit_quantity')
        for phrase in ['thirtyish steps', 'thirty-ish steps', '30-ish steps']:
            self.assertRule(row('The chair is '+phrase+' to my right.'), 'number_word')
        for phrase in ['at a right angle', 'at a sharp ° angle']:
            self.assertRule(row('The chair is '+phrase+' to my right.'), 'angle_or_coordinate')
        self.assertPass(row('The chair is to my right.'))
        self.assertPass(row('<measure>\n<tool_response>1 m</tool_response>\nThe chair is about a metre to my right.', form='program'))

    def test_structure_choices(self):
        for phrase in ['(A)', 'the first option', 'the second listed option']:
            self.assertRule(row('The chair is right, '+phrase+'.'), 'letter_restatement')
        self.assertPass(row('The chair is first seen in frame 2.'))
        self.assertPass(row('<move>\nThe chair is right (A).', form='program'))

    def test_disguised_exhaustive(self):
        for phrase in ['every frame', 'all frames']:
            self.assertRule(row('The chair is visible in '+phrase+'.'), 'exhaustive_frames')
        body = 'Seen: first chair in frame 1; second chair in frame 2; third chair in frame 3; fourth chair in frame 4.'
        value = row(body); value['frame_indices'] = list(range(4))
        self.assertRule(value, 'exhaustive_frames')
        self.assertPass(row('Seen: first chair in frame 1; second chair in frame 2.'))
        self.assertPass(row('Seen: trash can and sofa in frames 17 and 26.', question='Where are the trash can and sofa?'))

    def test_absence_and_untagged_response(self):
        for phrase in ['does not appear in frame 3', 'is invisible in frame 3', 'is never seen', 'is not visible in frame 3']:
            self.assertRule(row('The chair '+phrase+'.'), 'absence_claim')
        self.assertRule(row('tool_response: chair centre right of the axis'), 'direct_call')
        self.assertPass(row('The chair is visible in frame 3.'))
        self.assertPass(row('<ground>\n<tool_response>The chair is never seen.</tool_response>', form='program'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
