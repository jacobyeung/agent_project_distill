import importlib.util
import json
from pathlib import Path
import unittest
import build

spec=importlib.util.spec_from_file_location('gt_adapter',build.ROOT/'gt/adapter.py')
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)

class GTTests(unittest.TestCase):
    def test_all_staged_headers_and_labels(self):
        value=adapter.audit()
        self.assertEqual((value['available_captures'],value['missing_captures']),(38,22))
        self.assertEqual(value['total_object_occurrences'],300)
        self.assertEqual(value['unique_label_bindings'],142)
        self.assertEqual(value['items_with_exact_anchor_indices'],value['items_with_gt'])
        self.assertEqual(value['items_with_gt'],76)
        for r in value['files'].values():
            self.assertIn(r['headers']['inst']['shape'],([32,240,320],[32,320,240]))
            self.assertTrue(r['missing']);self.assertFalse(r['annotation_complete'])
        self.assertEqual(value['converted_items'],0)
        self.assertEqual(value['raster_shapes'],{'32x240x320':29,'32x320x240':9})
        self.assertFalse(value['alignment']['performed'])
        ref=json.loads((build.ROOT/'kit2/kit/rerun2/items544.json').read_text())['items']
        r=next(r for r in ref if r['capture'] in value['files'])
        with self.assertRaisesRegex(ValueError,'480x640'):
            adapter.convert(Path(value['files'][r['capture']]['path']),r)

    def test_ambiguous_and_missing_stay_unknown(self):
        r=dict(ids=[1,2,3],labels=['chair','chair','lamp'])
        self.assertEqual(adapter.bind('chair',r)['status'],'U')
        self.assertEqual(adapter.bind('sofa',r)['status'],'U')
        self.assertEqual(adapter.bind('lamp',r)['instance_id'],3)
        self.assertEqual(adapter.bind('Lamp',r)['status'],'U')

if __name__=='__main__':unittest.main()
