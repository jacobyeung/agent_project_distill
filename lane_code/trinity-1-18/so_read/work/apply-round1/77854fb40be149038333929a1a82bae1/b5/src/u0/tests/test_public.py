"""Public configuration, logs, and reversible wire-format fixtures. No sockets."""
import io
import json
import os
from pathlib import Path
import sys
import unittest
import uuid
E=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(E))
from a9 import (Codec,PublicJSON,PublicLog,pack,unpack,seal_settings,load_settings,
                validate_config,install_wire_decoder,RAW_LOADS,install_log_boundary)

class PublicTests(unittest.TestCase):
    def test_settings_tokens_hide_every_name_and_reject_descriptive_paths(self):
        root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
        settings={'sam3':{'checkpoint_path':'/scratch/u0/u1'},'tree':'/scratch/u0/u2',
                  'perception_memo_modules':['g3t'],'stage1_select_rule':'null_argmax'}
        path=root/'u0';seal_settings(settings,path)
        text=path.read_text()
        for word in ('sam','g3t','null_argmax','checkpoint','tree'):self.assertNotIn(word,text.lower())
        decoded=load_settings(path,'devs1_routed');self.assertEqual(decoded['sam3'],settings['sam3'])
        self.assertEqual(decoded['arm'],'own_depth')
        settings['sam3']['checkpoint_path']='/scratch/u0/model.safetensors'
        with self.assertRaises(ValueError):seal_settings(settings,root/'u1')

    def test_library_wire_decoder_preserves_ordinary_json_and_hash_serialization(self):
        before=json.dumps({'foo':[1,-0.0,None]})
        try:
            install_wire_decoder()
            self.assertEqual(json.loads(before),{'foo':[1,-0.0,None]})
            self.assertEqual(json.loads(json.dumps({'u0':pack({'sam3':'Qwen/project'})})),{'sam3':'Qwen/project'})
            self.assertEqual(json.dumps({'foo':[1,-0.0,None]}),before)
        finally:json.loads=RAW_LOADS

    def test_no_raw_id_map_is_published_and_nested_ids_roundtrip(self):
        value={'id':'vsi590k_001','dataset':'scannet','room_key':'scannet/scene1',
               'output':{'key':'devrows:vsi590k_001','text':'</think> A','tokens':[1,-0.0]}}
        codec=Codec(value);wire=PublicJSON(codec);encoded=wire.dumps(value)
        for word in ('vsi','scannet','devrows','output','tokens'):self.assertNotIn(word,encoded)
        self.assertEqual(wire.loads(encoded),value)
        self.assertNotIn('reverse',encoded)

    def test_unstructured_library_logs_and_partial_lines_only_publish_tokens(self):
        target=io.StringIO();log=PublicLog(target)
        log.write('Qwen SAM scannet /scratch/project/model.py id=vsi590k_')
        log.write('001\npartial');log.flush()
        lines=target.getvalue().splitlines();self.assertEqual(len(lines),2)
        for line in lines:
            self.assertRegex(json.loads(line)['event'],r'^u[0-9a-f]{64}$')
            for word in ('qwen','sam','scannet','project','vsi'):self.assertNotIn(word,line.lower())

    def test_legacy_worker_log_context_manager_never_writes_raw_library_output(self):
        root=Path(os.environ['READ_TEST_TMP'])/uuid.uuid4().hex;root.mkdir(parents=True)
        original_open=Path.open;stdout,stderr=sys.stdout,sys.stderr
        try:
            install_log_boundary()
            with (root/'worker.log').open('a') as stream:
                stream.write('Qwen scannet id=vsi590k_001\npartial SAM')
        finally:Path.open=original_open;sys.stdout=stdout;sys.stderr=stderr
        text=(root/'worker.log').read_text()
        self.assertEqual(len(text.splitlines()),2)
        for word in ('qwen','scannet','vsi','sam'):self.assertNotIn(word,text.lower())

    def test_public_array_descriptor_has_opaque_paths_and_numeric_types(self):
        cfg=json.loads((E/'tests/u1.json').read_text());validate_config(cfg)
        cfg['items']='/scratch/u0/items/devs1_routed.json'
        with self.assertRaises(ValueError):validate_config(cfg)
        cfg['items']='/scratch/u0/u1';cfg['types']=['camera_rotation']
        with self.assertRaises(ValueError):validate_config(cfg)

if __name__=='__main__':unittest.main(verbosity=2)
