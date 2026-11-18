"""Source-order identities, authenticated local decoding and cross-kit pairing."""
import offline_guard
from collections import Counter
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import unittest
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import build_assets as B, item_ids as I, unpack_return as U
import h1pair as P

DUPLICATES={'r0_5f3b5ae38f23ff697994','r0_c07cd9b246d953847b90'}


class Fix1c(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=[json.loads(s) for s in (ROOT/'in/out/qsets/R0_QUESTIONS_dev_f32.jsonl').read_text().splitlines()]
        cls.items=[json.loads(s) for s in (ROOT/'assets/e52a690b.jsonl').read_text().splitlines()]
        cls.mapping=I.load_map()
        seen=Counter();cls.expected=[]
        for row in cls.source:
            seen[row['qid']]+=1
            cls.expected.append(row['qid']+('#2' if seen[row['qid']]==2 else ''))

    def test_exact_source_order_rule_and_retained_key(self):
        key=bytes.fromhex(json.loads(B.KEY_PATH.read_text())['key_hex'])
        self.assertEqual(B.sha(B.KEY_PATH),json.loads((ROOT/'evidence/FIX1_BUILD_FIRST.json').read_text())['evidence/ID_KEY.json'])
        self.assertEqual(len(self.items),2169)
        self.assertEqual(len(set(self.expected)),2169)
        self.assertEqual({x for x in self.expected if x.endswith('#2')},{q+'#2' for q in DUPLICATES})
        self.assertEqual(len(self.mapping),2169)
        actual=[]
        for n,(source,item,expected) in enumerate(zip(self.source,self.items,self.expected),1):
            mapped=self.mapping[item['id']];actual.append(mapped['id'])
            self.assertEqual((mapped['id'],mapped['source_qid'],mapped['source_line']),(expected,source['qid'],n))
            self.assertEqual(item['id'],B.opaque(key,'item',expected))
            self.assertNotIn('source_qid',item)
            self.assertNotIn(source['qid'],json.dumps(item))
        self.assertEqual(actual,self.expected)

    def scored(self):
        return [dict(family='a7',id=r['id'],example_id=r['id'],room=r['room'],scene=r['scene'],
                     score=0,step=200,budget=2048,scoring_basis='answer',task_type=r['question_type']) for r in self.items]

    def test_cross_kit_membership_and_duplicate_pairing(self):
        opaque=self.scored()
        other=[dict(row,id=logical,example_id=logical,family='r0dev') for row,logical in zip(opaque,self.expected)]
        self.assertEqual(set(P.index(opaque,200)),set(P.index(other,200)))
        selected=[n for n,r in enumerate(self.source) if r['qid'] in DUPLICATES]
        result=P.compare([opaque[n] for n in selected],[other[n] for n in selected],200)
        self.assertEqual(result['shared_items'],4)
        self.assertEqual(result['families']['r0dev']['obj_appearance_order']['ci95_pp'],[0,0])

    def test_authenticated_unpack_exposes_all_logical_ids(self):
        root=ROOT/'evidence'/('fix1c_'+uuid.uuid4().hex);(root/'fetched').mkdir(parents=True)
        (root/'CONFIG.json').write_text(json.dumps(dict(token='a000000001',plan_sha256='a'*64)))
        (root/'SUBMISSION.json').write_text('{"status":"SUBMITTED","job":1}')
        archive=root/'fetched/result.tar.gz'
        inventory=''.join(json.dumps(row)+'\n' for row in self.scored()).encode()
        main=b'{"id":"main-id","family":"main"}\n'
        with tarfile.open(archive,'w:gz') as tf:
            for name,raw in [('COMPLETE.json',json.dumps(dict(plan_sha256='a'*64,synthetic=False)).encode()),
                             ('ITEMS.jsonl',inventory+main),('a7/ITEMS.jsonl',inventory),('main/ITEMS.jsonl',main),
                             ('a7/a0/results/0/items_a0.jsonl',inventory)]:
                member=tarfile.TarInfo(name);member.size=len(raw);tf.addfile(member,io.BytesIO(raw))
        before=B.sha(archive)
        receipt=dict(schema='a3',token='a000000001',job=1,plan_sha256='a'*64,synthetic=False,status='COMPLETE',
                     complete=True,conflicting_terminal_markers=False,returncode=0,
                     archive=dict(bytes=archive.stat().st_size,sha256=before))
        (root/'fetched/EXIT.json').write_text(json.dumps(receipt))
        target=U.unpack(root)
        for path in (target/'ITEMS.jsonl',target/'a7/ITEMS.jsonl'):
            rows=P.load([path]);decoded=[row for row in rows if row['family']=='a7']
            self.assertEqual([r['id'] for r in decoded],self.expected)
            self.assertEqual([r['example_id'] for r in decoded],self.expected)
            self.assertEqual([r['source_qid'] for r in decoded],[r['qid'] for r in self.source])
            self.assertEqual([r['source_line'] for r in decoded],list(range(1,2170)))
            first=path.read_bytes();I.decode_inventories(target);self.assertEqual(first,path.read_bytes())
        self.assertEqual((target/'main/ITEMS.jsonl').read_bytes(),main)
        self.assertEqual((target/'a7/a0/results/0/items_a0.jsonl').read_bytes(),inventory)
        self.assertEqual(B.sha(archive),before)

    def test_unknown_opaque_id_refused(self):
        with self.assertRaisesRegex(ValueError,'absent from the local identifier map'):
            I.logical_item(dict(family='a7',id='0'*24),self.mapping)


if __name__=='__main__':unittest.main()
