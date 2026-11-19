"""Portable synthetic regressions for the opt-in prior and loader clause parser."""
from collections import Counter
from copy import deepcopy
from pathlib import Path
import json, os, random, unittest, uuid
from student_pilot import r1_mix as M
from student_pilot.p3_provenance import digest, file_pin, load
from student_pilot.r1_training import STREAMS


class DirectionPrior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(os.environ['R2_PROOFS'])/('direction_prior_'+uuid.uuid4().hex)
        cls.root.mkdir(parents=True)
        cls.card = dict(schema='r1-card-v1', steps=1000, seed=17, quotas=STREAMS,
            cells=[dict(type=k, stream=s, rows_per_step=n) for k,s,n in
                   [('direction','vqa',36.866),('facing_pairs','vqa',18.170),('relative_distance','vqa',72.964),
                    ('pose','pose',64),('camera_displacement','routing',64),('pointing','pointing',32)]])
        cls.counts = dict(direction=55808, facing_pairs=42507, relative_distance=20000,
                          pose=16000, camera_displacement=16000, pointing=8000)
        from student_pilot.r1_direction_prior import WEIGHTS
        cls.weight_cells = {k:dict(weights=WEIGHTS[k], rows=[]) for k in WEIGHTS}
        cls.offset_cells = {k:dict(front=[], back=[]) for k in WEIGHTS}
        cls.groups = {};pos=Counter()
        for cell in cls.card['cells']:
            k,s=cell['type'],cell['stream'];cls.groups[k]=list(range(pos[s],pos[s]+cls.counts[k]));pos[s]+=cls.counts[k]
        for k,backs,fronts in [('direction',3676,16826),('facing_pairs',651,3709)]:
            j=0
            for side,n in [('back',backs),('front',fronts)]:
                for i in range(n):
                    row=cls.row(k,side,i)
                    cls.weight_cells[k]['rows'].append(dict(qid=row['qid'],row_sha256=digest(row),side=side))
                    cls.offset_cells[k][side].append(cls.groups[k][j]);j+=1
        cls.stream_counts=dict(pos)
        cls.binding = cls.make_binding()
        cls.base = list(M.plans(cls.binding,cls.stream_counts,1000))

    @staticmethod
    def row(k, side, i):
        relation='behind' if side=='back' else 'in front of'
        return dict(**({'facing':'toward'} if k=='facing_pairs' else {}),
                    qid=k+'_'+side+'_'+str(i), question_type='object_rel_direction_hard',
                    student_input=dict(question='Facing the chair, is the table ahead?', options=['A. '+side,'B. left']),
                    answer='A',target='Step 2: The table is '+relation+' me.')

    @classmethod
    def put(cls, name, value):
        p=cls.root/name;p.write_text(json.dumps(value,sort_keys=True)+'\n');return file_pin(p)

    @classmethod
    def make_binding(cls):
        card=cls.put('card.json',cls.card)
        evidence=cls.put('fixture.json',dict(scope='SYNTHETIC_UNIT_TEST_NOT_PRODUCTION',inputs=[]))
        pop=cls.put('population.json',dict(schema='r1-population-v1',complete=True,after_all_filters=True,
                counts=cls.counts,card_sha256=card['sha256'],evidence=[evidence]))
        idx=cls.put('indices.json',dict(population_sha256=pop['sha256'],cells=cls.groups))
        return dict(card=card,population=pop,indices=idx)

    def policy(self,name):
        return self.put(name,dict(schema='r1-direction-prior-v1',policy='toward_hard_equal_mass_v1',
                                 cells=self.weight_cells,inputs=[self.binding['card']]))

    def enabled(self,name):
        pin=self.policy(name+'_weights.json')
        value=dict(schema='r1-direction-prior-offsets-v1',policy=pin,cells=self.offset_cells,
                   **{k+'_sha256':self.binding[k]['sha256'] for k in ('card','population','indices')})
        return dict(self.binding,direction_prior=self.put(name+'_bound.json',value))

    def test_slots_counts_cap_and_resume(self):
        b=self.enabled('slots');after=list(M.plans(b,self.stream_counts,1000))
        targets={i for cell in self.offset_cells.values() for values in cell.values() for i in values}
        backs={i for cell in self.offset_cells.values() for i in cell['back']}
        changed=0;draws=Counter();sides=Counter()
        for old,new in zip(self.base,after):
            for (s,oi),(t,ni) in zip(old,new):
                self.assertEqual(s,t)
                for a,c in zip(oi,ni):
                    draws[s,c]+=1
                    if s=='vqa' and a in targets:
                        self.assertIn(c,targets);sides[c in backs]+=1;changed+=a!=c
                    else:self.assertEqual(a,c)
        self.assertGreater(changed,0);self.assertLessEqual(max(draws.values()),4)
        self.assertLessEqual(abs(sides[True]-sides[False]),2)
        self.assertEqual(after[777:],list(M.plans(b,self.stream_counts,1000,start_step=777)))
        self.assertEqual(after,list(M.plans(b,self.stream_counts,1000)))

    def test_tampered_weight_refuses(self):
        b=self.enabled('tamper');bound=load(b['direction_prior']['path'])
        with Path(bound['policy']['path']).open('a') as f:f.write(' ')
        with self.assertRaisesRegex(ValueError,'Missing or changed pinned input'):
            next(M.plans(b,self.stream_counts,1))

    def test_bad_bound_pin_and_offsets_refuse(self):
        b=self.enabled('bound');b['direction_prior']['sha256']='0'*64
        with self.assertRaises(ValueError):next(M.plans(b,self.stream_counts,1))
        for key in ('population_sha256','indices_sha256','card_sha256','cells'):
            b=self.enabled('bad_'+key);v=load(b['direction_prior']['path'])
            if key=='cells':v['cells']['direction']['front'][0]=-1
            else:v[key]='0'*64
            b['direction_prior']=self.put('altered_'+key+'.json',v)
            with self.assertRaises(ValueError):next(M.plans(b,self.stream_counts,1))

    def test_prepare_identity_and_completeness(self):
        from student_pilot.r1_direction_prior import Prior
        prior=Prior(self.policy('prepare_weights.json'))
        for k in self.weight_cells:
            for side in ('back','front'):
                for i,offset in enumerate(self.offset_cells[k][side]):
                    prior.observe(self.row(k,side,i),'vqa',k,offset)
        bound=prior.bind(self.binding,self.root/'prepared.json')
        b=dict(self.binding,direction_prior=bound)
        self.assertEqual(list(M.plans(b,self.stream_counts,1000)),list(M.plans(self.enabled('prepared_compare'),self.stream_counts,1000)))
        with self.assertRaisesRegex(ValueError,'DUPLICATE'):prior.observe(self.row('direction','back',0),'vqa','direction',0)
        prior=Prior(self.policy('incomplete_weights.json'))
        with self.assertRaisesRegex(ValueError,'POPULATION_DIFFERS'):prior.bind(self.binding,self.root/'missing.json')
        row=self.row('direction','back',0);row['target']+=' changed'
        with self.assertRaisesRegex(ValueError,'IDENTITY'):prior.observe(row,'vqa','direction',0)

    def test_produce_binds_optional_field(self):
        from student_pilot.r1_population import produce
        targets = {}
        for k in self.weight_cells:
            for side in ('back', 'front'):
                for i, offset in enumerate(self.offset_cells[k][side]):
                    targets[offset] = self.row(k, side, i)
        ownership = {(c['stream'], i): c['type'] for c in self.card['cells']
                     for i in self.groups[c['type']]}
        stream_counts = self.stream_counts
        class Reader:
            def count(self, stream): return stream_counts[stream]
            def row(self, stream, i):
                kind = ownership[stream, i]
                if stream == 'vqa' and i in targets: return targets[i], {}
                typ = ('object_rel_direction_easy' if kind in ('direction', 'facing_pairs') else
                       'object_rel_distance' if kind == 'relative_distance' else kind)
                row = dict(qid=stream+'_filler_'+str(i), question_type=typ,
                           student_input={'question': 'Facing the chair, where is the table?'})
                if kind == 'facing_pairs': row['facing'] = 'toward'
                return row, {}
        member = self.put('produce_member.json', dict(schema='r1-source-membership-v1', sources={}))
        evidence = self.put('produce_evidence.json', dict(scope='SYNTHETIC_TEST', inputs=[]))
        weights = self.policy('produce_weights.json')
        absent = produce(Reader(), self.binding['card'], member, [evidence], self.root/'produce_absent')
        enabled = produce(Reader(), self.binding['card'], member, [evidence], self.root/'produce_enabled',
                          cfg={'r1_training': {'direction_prior': weights}})
        self.assertNotIn('direction_prior', absent)
        self.assertEqual(load(enabled['direction_prior']['path'])['policy'], weights)
        self.assertEqual(absent['population']['sha256'], enabled['population']['sha256'])
        self.assertEqual(absent['indices']['sha256'], enabled['indices']['sha256'])
        self.assertNotEqual(list(M.plans(absent, stream_counts, 1000)),
                            list(M.plans(enabled, stream_counts, 1000)))

    def test_capacity_refusal(self):
        from student_pilot.r1_direction_prior import schedules
        b=self.enabled('capacity');card,idx,proof=M.validate_binding(b)
        pools={k:list(v) for k,v in self.groups.items()}
        # A concentrated prefix exceeds the back-row capacity although the cell's total cap fits.
        proof['draws']['direction']=4*self.counts['direction']
        with self.assertRaisesRegex(ValueError,'CAPACITY'):schedules(b,card,idx,proof,pools)

    def test_production_audit_includes_facing_pairs(self):
        from unittest.mock import patch
        from student_pilot import carrier_c1_run as C, r1_loader as L
        selected = [self.offset_cells['direction']['back'][0],
                    self.offset_cells['facing_pairs']['front'][0]]
        stream_counts = self.stream_counts
        rows = {selected[0]: self.row('direction', 'back', 0),
                selected[1]: self.row('facing_pairs', 'front', 0)}
        class Reader:
            def count(self, stream): return stream_counts[stream]
            def row(self, stream, i): return rows.get(i, dict(qid='eligible_'+str(i))), {}
            def close(self): pass
        cfg = dict(r2_sampling=self.binding, r1_training=dict(row_plan_sha256=digest(self.binding)))
        with patch('os.uname', return_value=type('Host', (), dict(nodename='fixture-host'))()), \
             patch.object(C, 'prepared', return_value=({}, None)), \
             patch.object(C, 'Rows', return_value=Reader()), \
             patch.object(M, 'plans', return_value=[[('vqa', selected)]]), \
             patch.object(L, 'row_check'):
            audit = L.production_audit(cfg, self.root/'audit_fixture')
        self.assertEqual(audit['draws'], {'direction': 1, 'facing_pairs': 1})
        share = audit['direction']['answer_shares'][0]
        self.assertEqual((share['draws'], share['back']['draws'], share['front']['draws']), (2, 1, 1))

    def test_clause_parser(self):
        from student_pilot.r1_direction_twins import dimensions
        for q,clause in [('With my back to the chair, is the table ahead?','away'),
                         ('Facing in the opposite direction, where is the chair?','away'),
                         ('My gaze fixed on the chair, where is the table?','toward'),
                         ('With the chair ahead of me, where is the table?','toward')]:
            row=self.row('direction','back',0);row['student_input']['question']=q
            self.assertEqual(dimensions(row),(clause,'hard','back'))

if __name__=='__main__':unittest.main()
