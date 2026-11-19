"""Independently authored camera questions; no item text is a template source."""
TYPES = ('camera_displacement', 'camera_rotation', 'camera_movement_direction')
# Each stem specifies the measured quantity; four layouts move frame and unit clauses.
D = [
 'Estimate the straight-line separation of the two camera positions',
 'Measure the magnitude of the camera’s net translation',
 'Find the distance separating the camera’s starting and ending locations',
 'Determine how far apart the two camera locations are',
 'Calculate the length of the camera’s displacement vector',
 'Report the change in camera position as a straight-line distance',
 'Give the camera’s endpoint-to-endpoint displacement magnitude',
 'Quantify the separation between the camera’s initial and final positions',
 'Work out the camera’s net change of position in distance terms',
 'State the direct distance from the earlier camera position to the later one',
 'Please estimate the magnitude of the change in camera location',
 'How large is the camera’s translational displacement',
]
R = [
 'Determine the signed change in the camera’s heading',
 'Calculate the camera’s signed yaw change',
 'Report how much the camera turns about the vertical axis',
 'Measure the signed angle between the initial and final camera headings',
 'Find the camera’s horizontal turning angle with its sign',
 'State the signed amount of camera rotation around the upward axis',
 'Quantify the camera’s heading change as a signed angle',
 'Give the signed turn from the first camera heading to the second',
 'Estimate the yaw angle through which the camera turns',
 'Work out the signed horizontal rotation of the camera',
 'Please measure the camera’s turn relative to its initial heading',
 'How much does the camera’s heading rotate, including the sign',
]
M = [
 'Choose the dominant consistent direction of camera translation',
 'Identify the direction in which the camera mainly and consistently travels',
 'Classify the camera’s primary consistent movement direction',
 'Select the direction that best describes the camera’s sustained translation',
 'Determine which direction dominates the camera’s consistent motion',
 'Report the principal consistent direction of camera travel',
 'Name the camera’s main sustained direction of movement',
 'Decide which direction describes the camera’s predominant consistent translation',
 'Find the primary direction in which the camera keeps moving',
 'Give the direction of the camera’s dominant sustained movement',
 'Please identify the camera’s principal consistent travel direction',
 'Which direction best characterizes the camera’s main consistent motion',
]

def candidates():
    result={t:[] for t in TYPES}
    for s in D:
        result[TYPES[0]] += [
          s+' from frame {i} to frame {j} in this {n}-frame clip. Express the result in {unit}.',
          'Using {unit}, '+s[0].lower()+s[1:]+' for frames {i} and {j} out of {n}.',
          'Take frame {i} as the start and frame {j} as the end of the {n} displayed frames. '+s+'; give the value in {unit}.',
          'In the {n}-frame video, focus on frame {i}, then frame {j}. '+s+' (answer in {unit}).',
        ]
    for s in R:
        result[TYPES[1]] += [
          s+' from frame {i} to frame {j} in the {n}-frame clip. Use degrees in (-180, 180], with a left turn positive.',
          'For the {n} displayed frames, compare heading at frame {i} with heading at frame {j}. '+s+'. Give degrees, left-positive, in (-180, 180].',
          'Use the convention that leftward yaw is positive and angles lie in (-180, 180] degrees. '+s+' going from frame {i} to frame {j} of {n}.',
          'Starting at frame {i} and ending at frame {j} of the {n}-frame video, '+s[0].lower()+s[1:]+'. Report degrees within (-180, 180]; positive denotes a turn to the left.',
        ]
    for s in M:
        result[TYPES[2]] += [
          s+' over frames {i} through {j} in the {n}-frame clip, using the camera orientation at frame {i} as the reference. Choose from: {options}.',
          'In the {n}-frame video, take the camera’s orientation at frame {i} as fixed. '+s+' for the interval from frame {i} to frame {j}. Available answers: {options}.',
          'The choices are {options}. '+s+' during frames {i}–{j} of {n}, relative to the orientation of the camera at the interval’s start.',
          'Consider frames {i} through {j}, inclusive, among the {n} displayed frames. '+s+'. Interpret directions relative to the starting camera orientation; select from {options}.',
        ]
    return result

HELDOUT = {
 TYPES[0]:[
  'Frame {i} and frame {j} mark two camera locations in a clip of {n} frames. How many {unit} separate those locations along a straight line?',
  'Compare the camera’s position at frame {i} with its position at frame {j}, among {n} displayed frames. What is the magnitude of the difference, in {unit}?',
  'Use {unit} for your answer: what is the net positional displacement of the camera from frame {i} to frame {j} in this {n}-frame sequence?',
  'Suppose a straight segment joins the camera positions at frames {i} and {j} of {n}. Give that segment’s length in {unit}.',
  'For this {n}-frame sequence, evaluate the spatial offset between the camera locations shown in frame {i} and frame {j}. Return its magnitude in {unit}.',
  'At frame {i} the camera occupies one position; at frame {j} it occupies another. These views come from a {n}-frame clip; express their direct separation in {unit}.',
  'What length, measured in {unit}, describes the camera’s net translation over the interval whose endpoints are frame {i} and frame {j} of {n}?',
  'Please compare two views from the {n}-frame clip: frame {i} and frame {j}. Report the straight-line distance in {unit} between their camera centers.',
 ],
 TYPES[1]:[
  'Compare the headings at frame {i} and frame {j} of a {n}-frame sequence. What signed yaw angle takes the first to the second? Give degrees in (-180, 180], counting a leftward turn as positive.',
  'Use left-positive angles in (-180, 180] degrees. How far has the camera turned horizontally when moving from frame {i} to frame {j} within the {n} displayed frames?',
  'For frames {i} and {j} out of {n}, express the camera’s change of facing direction as signed yaw. The answer must be in degrees, positive toward the left, and wrapped to (-180, 180].',
  'The starting view is frame {i}; the ending view is frame {j}, in a clip with {n} frames. Give the camera’s signed horizontal turn in degrees, where left is positive and the permitted interval is (-180, 180].',
  'How many signed degrees does the camera’s heading shift between frames {i} and {j} of {n}? Assign positive values to leftward turns and use (-180, 180].',
  'Within the {n} displayed frames, track heading from frame {i} to frame {j}. Return the yaw difference in degrees using the range (-180, 180] and a positive sign for leftward rotation.',
  'Please express the turn about the vertical axis from the camera pose at frame {i} to its pose at frame {j} of {n}. Use signed degrees in (-180, 180]; turning left gives a positive value.',
  'With frame {i} as the heading reference and frame {j} as the endpoint, what is the camera’s signed turn in this {n}-frame clip? Report degrees in (-180, 180], with positive values for leftward rotation.',
 ],
 TYPES[2]:[
  'Fix directional axes to the camera’s orientation in frame {i}. For its travel from frame {i} through frame {j} of {n}, which choice captures the main consistent direction? Choices: {options}.',
  'Watch the interval bounded by frames {i} and {j} in this {n}-frame sequence. Relative to how the camera faces at the interval’s beginning, where does it mainly and consistently move? Select from: {options}.',
  'Which option best matches the camera’s predominant consistent travel between frame {i} and frame {j} out of {n}? Choose from: {options}. Use its orientation at the earlier frame to define these directions.',
  'The reference orientation is the camera’s at frame {i}. Over frames {i}–{j} in the {n}-frame clip, classify its principal consistent translation using these labels: {options}.',
  'For this {n}-frame video, focus on motion beginning at frame {i} and ending at frame {j}. Relative to the camera’s orientation at frame {i}, which way does the camera predominantly and consistently travel? Answers: {options}.',
  'Use the camera’s facing direction at frame {i} to interpret motion through frame {j} of the {n}-frame sequence. What is the main consistent travel direction in that interval? Pick one: {options}.',
  'Imagine keeping the camera’s orientation from frame {i} fixed while following its position through frame {j} of {n}. Which direction describes its dominant consistent motion? Available labels: {options}.',
  'Across the interval from frame {i} to frame {j} in a sequence of {n} frames, identify the direction of sustained camera translation that predominates. Judge it relative to the starting orientation. Options: {options}.',
 ]}
