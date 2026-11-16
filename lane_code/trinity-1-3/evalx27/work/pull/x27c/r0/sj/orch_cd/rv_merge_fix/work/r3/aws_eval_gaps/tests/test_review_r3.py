"""Interrupted legacy writes, portable evidence and content-check regressions."""
import json
import shutil
import unittest
from pathlib import Path
from unittest.mock import patch
import test_review_r2 as fixtures
import provenance
from provenance import annotate, verify_annotation, sha


class ReviewN(unittest.TestCase):
    def bundle(self):
        return fixtures.ReviewA().bundle()

    def test_N1_two_interruptions_middle_and_tail(self):
        d,p,a,j,c,r = self.bundle()
        complete = dict(r,status='complete',note='é')
        first = json.dumps(dict(complete,key='revsi:2'),ensure_ascii=False)+'\n'
        partial = '{"key":"revsi:1","raw_generation":"interrupted'
        tail = '{"key":"revsi:3","raw_generation":"unfinished'
        raw = (first+partial+'\n'+partial+'\n'+json.dumps(complete)+'\n'+tail).encode()
        j.write_bytes(raw)
        out=d/'result/g0.jsonl';meta=annotate(p,a,j,out,0)
        self.assertEqual(j.read_bytes(),raw)
        self.assertEqual(meta['skipped_line_count'],3)
        self.assertEqual([x['byte_offset'] for x in meta['skipped_lines']],
                         [len(first.encode()),len((first+partial+'\n').encode()),len(raw)-len(tail.encode())])
        self.assertEqual([x['disposition'] for x in meta['skipped_lines']],
                         ['completed_later','completed_later','missing'])
        self.assertEqual(meta['missing_keys'],['revsi:3'])
        self.assertEqual(len(out.read_text().splitlines()),2)
        self.assertEqual(verify_annotation(out,c,0).metadata,meta)

    def test_N1_partial_last_absent_is_reported_missing(self):
        d,p,a,j,c,r=self.bundle()
        j.write_text('{"key":"revsi:missing","value":')
        out=d/'result/g0.jsonl';meta=annotate(p,a,j,out,0)
        self.assertEqual(out.read_bytes(),b'')
        self.assertEqual(meta['missing_keys'],['revsi:missing'])
        self.assertEqual(meta['skipped_lines'][0]['byte_offset'],0)
        verify_annotation(out,c,0)

    def test_N1_refuses_malformed_even_before_same_key_completion(self):
        for bad in ('{bad','{"key":"revsi:1","x":oops','{"key":"revsi:1","x":"bad\\q',
                    '{"key":"revsi:1",}', '{"key":"revsi:1","x":NaN} trailing',
                    '{"key":','{"key":"revsi:1","x":[1,]}','{"key":"revsi:1","x":NaN}'):
            with self.subTest(bad=bad):
                d,p,a,j,c,r=self.bundle()
                j.write_text(bad+'\n'+json.dumps(dict(r,status='complete'))+'\n')
                with self.assertRaisesRegex(ValueError,'Broken journal'):
                    annotate(p,a,j,d/'result/g0.jsonl',0)
                self.assertFalse((d/'result/g0.jsonl').exists())

    def test_N1_refuses_partial_after_complete_or_before_error(self):
        for order in ('before_error','after_complete'):
            with self.subTest(order=order):
                d,p,a,j,c,r=self.bundle();partial='{"key":"revsi:1","x":'
                raw=(partial+'\n'+json.dumps(r) if order=='before_error' else
                     json.dumps(dict(r,status='complete'))+'\n'+partial)
                j.write_text(raw)
                with self.assertRaisesRegex(ValueError,'later complete'):
                    annotate(p,a,j,d/'result/g0.jsonl',0)

    def test_N1_recovery_audit_cannot_be_rewritten(self):
        d,p,a,j,c,r=self.bundle();j.write_text('{"key":"missing","x":')
        out=d/'result/g0.jsonl';meta=annotate(p,a,j,out,0)
        meta['skipped_lines'][0]['byte_offset']=5
        out.with_suffix('.annotation.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'recovery audit'):
            verify_annotation(out,c,0)

    def test_N3_row_tamper_rehashed_sidecar_is_refused(self):
        d,p,a,j,c,r=self.bundle();out=d/'result/g0.jsonl'
        meta=annotate(p,a,j,out,0)
        changed=json.loads(out.read_text());changed['raw_generation']='fabricated'
        out.write_text(json.dumps(changed)+'\n')
        meta['annotated_sha256']=sha(out)
        out.with_suffix('.annotation.json').write_text(json.dumps(meta))
        with self.assertRaisesRegex(ValueError,'changed original content'):
            verify_annotation(out,c,0)

    def test_N4_relocated_bundle_never_reads_original_paths(self):
        d,p,a,j,c,r=self.bundle();out=d/'result/g0.jsonl'
        meta=annotate(p,a,j,out,0)
        for field,hash_field in [('original_journal','original_journal_sha256'),
                                 ('request_path','request_sha256'),('source_archive','source_sha256')]:
            name=Path(meta[field]);self.assertFalse(name.is_absolute())
            self.assertNotIn('..',name.parts)
            self.assertEqual(sha(out.parent/name),meta[hash_field])
            self.assertIn(meta[hash_field],name.name)
        moved=fixtures.retained()/'archived';shutil.copytree(out.parent,moved)
        original_sha=provenance.sha
        def relocated_only(path):
            self.assertNotIn(Path(path).resolve(),{p.resolve(),a.resolve(),j.resolve()})
            return original_sha(path)
        with patch('provenance.sha',side_effect=relocated_only):
            self.assertEqual(verify_annotation(moved/out.name,c,0).metadata,meta)

    def test_N4_archived_original_tampering_is_refused(self):
        d,p,a,j,c,r=self.bundle();out=d/'result/g0.jsonl';meta=annotate(p,a,j,out,0)
        (out.parent/meta['original_journal']).write_text('changed')
        with self.assertRaisesRegex(ValueError,'Original journal hash'):
            verify_annotation(out,c,0)
