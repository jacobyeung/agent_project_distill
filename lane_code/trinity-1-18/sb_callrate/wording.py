"""Verbatim wording expressions from q1/classify.py; overlapping trace tags."""
import re
TEMPL = {
 'first_seen_frame': r'first seen in frame',
 'nearest_to_farthest': r'nearest[- ]to[- ]farthest',
 'candidates_ordered': r'candidates ordered',
 'question_asks_for': r'the question asks for',
 'i_find_it_to_be': r'I find (?:it|that|the gap|the distance)[^.\n]{0,60}to be',
 'gap_between_closest_points': r'then the (?:gap|shortest distance|spacing|distance) between (?:their closest points|them)',
 'the_gap_is': r'\bthe gap is\b',
 'stand_at_facing': r'when I stand at',
 'box_distance_is': r'The box distance is',
 'grid_5cm_two_objects': r'5 cm grid over the two objects',
 'grid_both_objects': r'on a grid over both objects',
 'converting_to': r'Converting to (?:feet|inches|centimet)',
 'ground_boxes_intro': r'I will ground the boxes',
 'locate_line': r'(?m)^Locate',
 'relate_line': r'(?m)^Relate',
 'step_n': r'(?m)^Step \d+:',
}
TEMPL = {k: re.compile(v) for k, v in TEMPL.items()}
