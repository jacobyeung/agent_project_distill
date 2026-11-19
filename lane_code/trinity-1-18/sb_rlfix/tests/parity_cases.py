"""The review's 74 verbatim formats; source hash is recorded by check.py."""
EOS = '<|im_end|>'
numeric = ['12.19', '<answer>12.19</answer>', '12.19 m', '12.19m', '12.19 square meters', 'about 12.19',
           'The answer is 12.19', 'Answer: 12.19', '12.19.', '**12.19**', '<answer>12.19 m</answer>',
           '12,19', 'approximately 12.2 m', '12.19 (rounded)', '~12.19', '12.19\nDone']
choice = ['B', 'B.', '(B)', 'b', 'B. right', 'Option B', 'The answer is B', '<answer>B</answer>',
          'right', 'B) right', 'Answer: B', '**B**']
cases = []
for t in ('room_size_estimation', 'object_abs_distance', 'camera_displacement'):
    cases += [(t, '12.19', [], a) for a in numeric]
for t in ('object_rel_direction_easy', 'camera_movement_direction'):
    cases += [(t, 'B', ['A. left', 'B. right'], a) for a in choice]
# Choice type whose options are not under student_input.options (reward infers type from options only).
cases += [('camera_movement_direction', 'B', [], a) for a in ('B', 'B.')]

