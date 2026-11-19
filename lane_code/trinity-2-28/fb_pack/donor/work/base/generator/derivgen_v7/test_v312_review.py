"""Review regressions: grammar, variant identity, and unrestricted grounding."""
import copy
import itertools
import re
import unittest
from test_v312_ground import item, Geometry, masks, BACKEND
from derivgen.ground_v312 import Session, load_backend, render, option_map
from derivgen.ground_v312_quality import direction_question, shuffled_item, noun_is_plural

class ReviewTests(unittest.TestCase):
    def test_every_direction_option_order_has_allowed_grammar(self):
        for typ in ('object_rel_direction_medium', 'object_rel_direction_hard'):
            q = item(typ)
            contents = list(option_map(q['options']).values())
            for order in itertools.permutations(contents):
                text = direction_question(q, order)
                actual = text.split('is the query to my ', 1)[1].split('?')[0]
                self.assertEqual(actual, 'left, right, or back' if typ.endswith('medium')
                                 else 'front-left, front-right, back-left, or back-right')
                self.assertNotIn('behind', text)
                self.assertEqual(text.count('to my '), 2 if typ.endswith('medium') else 1)

    def test_shuffle_all_source_templates_and_orders(self):
        from derivgen.paraphrase import DIRECTION
        # Reach all 6/24 deterministic permutations through real row IDs.
        for typ in ('object_rel_direction_medium', 'object_rel_direction_hard'):
            seen = set()
            for i in range(600):
                q = item(typ); q['qid'] = str(i)
                template = DIRECTION[typ][i % len(DIRECTION[typ])]
                q['question'] = template.format(S='stand', F='face', Q='query')
                s = shuffled_item(q)
                order = tuple(option_map(s['options']).values()); seen.add(order)
                self.assertEqual(s['question'], direction_question(q, order))
                self.assertEqual(shuffled_item(s), s)
            self.assertEqual(len(seen), 6 if typ.endswith('medium') else 24)

    def test_benchmark_fixed_is_in_template(self):
        for name in ('shoes','chairs','shelves','clothes','scissors','people','boxes','pair of shoes','glass','bus','chest of drawers'):
            plural = name not in ('pair of shoes','glass','bus','chest of drawers')
            self.assertEqual(noun_is_plural(name), plural, name)
            for typ in ('object_rel_direction_medium','object_rel_direction_hard'):
                q=item(typ);q['roles']['query']=name
                text=direction_question(q, list(option_map(q['options']).values()))
                self.assertIn(', is the '+name+' ', text)
        self.assertFalse(noun_is_plural('series', 'singular'))
        self.assertTrue(noun_is_plural('sheep', 'plural'))

    def test_normal_and_miss_have_different_candidate_ids(self):
        q=item('object_rel_direction_medium');q.update(scene='s',frame_indices=list(range(32)),gt_answer='A')
        body='Step 1: locate the objects. Step 2: the query is on my left.'
        q['direct_canonical']=dict(scene='s',frame_indices=q['frame_indices'],question=q['question'],
            options=q['options'],answer='A',body=body,form='vqa_canonical',source_sha256='fixture')
        b=load_backend(BACKEND)
        normal=render(q,Session(b,Geometry(),masks),len)
        miss=render(q,Session(b,Geometry(),masks,simulated_misses=['stand']),len)
        self.assertEqual(normal['qid'],miss['qid'])
        self.assertNotEqual(normal['candidate_id'],miss['candidate_id'])
        self.assertEqual(normal['candidate_id'],render(q,Session(b,Geometry(),masks),len)['candidate_id'])

    def test_open_names_and_disconnected_masks_still_ground(self):
        import numpy as np
        calls=[]
        def provider(name):
            calls.append(name)
            a,p=masks('stand');a[3,45:55,65:75]=True
            return a,p
        session=Session(load_backend(BACKEND),Geometry(),provider)
        name='unlisted turquoise doodad'
        text=session.execute('<ground obj="'+name+'">')
        self.assertEqual(calls,[name])
        self.assertNotIn('not seen',text)
        self.assertTrue(session.objects[name]['seen'])

if __name__=='__main__':unittest.main()
