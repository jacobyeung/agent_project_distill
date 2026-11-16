"""Exercise the real native sampler with post-filter metadata, without stores."""
from collections import Counter
from copy import deepcopy
import json
import unittest
from student_pilot import r2_mix as M, r2_policy as P
from student_pilot.carrier_c1_data import mixed_indices
from student_pilot.p3_provenance import file_pin, write
from tests.test_r2_data_path import directory, LANE
from tests.test_r2_policy import evidence


def binding(root):
    mix=M.table(); write(root/'m.json',mix)
    draws=M.allocation(mix)
    populations={k:(n+3)//4 for k,n in draws.items()}
    populations['facing_pairs']+=(populations['facing_pairs']%2)
    write(root/'population.json',dict(schema='r2-filtered-population-v1',complete=True,exclusions=M.SEALED,
            withheld_sha256=M.WITHHELD_SHA256,cells=populations,synthetic=True))
    counts=dict(schema='r2-filtered-counts-v1',after_filtering=True,mix_sha256=file_pin(root/'m.json')['sha256'],
                receipts=[file_pin(root/'population.json')],cells=populations,synthetic=True)
    write(root/'c.json',counts)
    offsets=Counter(); cells={}; lookup={}
    for cell in mix['cells']:
        kind,stream=cell['type'],cell['stream']
        pool=list(range(offsets[stream],offsets[stream]+populations[kind]))
        for i in pool:lookup[(stream,i)]=kind
        offsets[stream]+=populations[kind]
        cells[kind]=[pool[i:i+2] for i in range(0,len(pool),2)] if kind=='facing_pairs' else pool
    write(root/'i.json',dict(schema='r2-type-indices-v1',counts_sha256=file_pin(root/'c.json')['sha256'],cells=cells))
    return dict(mix=file_pin(root/'m.json'),counts=file_pin(root/'c.json'),indices=file_pin(root/'i.json')),dict(offsets),lookup


class Sampling(unittest.TestCase):
    def test_native_sampler_exact_quotas_pairs_and_repeats(self):
        root=directory(); pins,counts,lookup=binding(root)
        totals=Counter();first=[];uses=Counter()
        for step,plan in enumerate(mixed_indices(counts,1000,world=4,r2_sampling=pins)):
            streams=Counter();pairs=[]
            for stream,indices in plan:
                self.assertEqual(len(indices),4);streams[stream]+=4
                for index in indices:
                    kind=lookup[stream,index];totals[kind]+=1;uses[stream,index]+=1
                    if kind=='facing_pairs':pairs.append(index)
            self.assertEqual(streams,M.table()['quotas'])
            start=min(i for (s,i),k in lookup.items() if k=='facing_pairs') if step==0 else start
            self.assertTrue(all(v==2 for v in Counter((i-start)//2 for i in pairs).values()))
            if step<2:first.append(plan)
        self.assertEqual(dict(totals),M.allocation(M.table()))
        self.assertLessEqual(max(uses.values()),4)
        self.assertEqual(list(M.plans(pins,counts,2,start_step=1)),first[1:])
        (LANE/'out/B2_SAMPLER_PROOF.json').write_text(json.dumps(dict(draws=dict(totals),maximum_repeats=max(uses.values()),
                steps=1000,world=4,synthetic_metadata=True,source='work/tree_r1/tests/test_r2_sampling.py'),indent=2)+'\n')

    def test_sampler_refusals_and_preparation(self):
        root=directory();pins,counts,lookup=binding(root)
        for kwargs in [dict(world=8),dict(steps=1001),dict(start_step=2,steps=1)]:
            args=dict(steps=1);args.update(kwargs)
            with self.assertRaises(ValueError):list(M.plans(pins,counts,**args))
        path=root/'i.json';original=json.loads(path.read_text())
        for key in ['schema','counts_sha256','missing','overlap','range','cover']:
            value=deepcopy(original);cc=dict(counts)
            if key=='schema':value['schema']='bad'
            if key=='counts_sha256':value['counts_sha256']='a'*64
            if key=='missing':value['cells']={}
            if key=='overlap':value['cells']['direction'][1]=value['cells']['direction'][0]
            if key=='range':value['cells']['pose'][0]=-1
            if key=='cover':cc['vqa']+=1
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):list(M.plans({**pins,'indices':file_pin(path)},cc,1))
        registry=evidence(root/'e')
        portable=lambda p:dict(path=str(__import__('pathlib').Path(p['path']).relative_to(root)),sha256=p['sha256'])
        b=dict(registry=portable(registry),mix=portable(pins['mix']),counts=portable(pins['counts']))
        P.preparation(b,root)
        with self.assertRaises(ValueError):P.preparation({**b,'counts':None},root)
        with self.assertRaises(ValueError):P.preparation({**b,'registry':dict(path='../escape',sha256='0'*64)},root)
        population=root/'population.json';original=json.loads(population.read_text())
        for change in [dict(complete=False),dict(cells={}),dict(cells={**original['cells'],'pose':-1})]:
            population.write_text(json.dumps({**original,**change}))
            record=json.loads((root/'c.json').read_text());record['receipts']=[file_pin(population)]
            (root/'c.json').write_text(json.dumps(record))
            with self.assertRaises(ValueError):M.preflight(pins['mix'],file_pin(root/'c.json'))
        population.write_text(json.dumps(original))
        record['receipts']=[file_pin(population)];record['cells']={**record['cells'],'pose':1}
        (root/'c.json').write_text(json.dumps(record))
        with self.assertRaisesRegex(ValueError,'differ'):M.preflight(pins['mix'],file_pin(root/'c.json'))
