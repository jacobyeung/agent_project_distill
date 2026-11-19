from pathlib import Path
p=Path('code/test_kit.py');s=p.read_text().replace("ids=sorted(row_ids('train'));rows=[]", "ids=sorted(row_ids('train'));rows=[]\n  from exclusions import population\n  rooms=population()['row_rooms']").replace("row_id=i,room='fixture',split='train',arm=name", "row_id=i,room=rooms[i],split='train',arm=name")
s=s.replace("mocks=dict(OUT=root,labels=", "mocks=dict(decision_rows=lambda rows:rows,OUT=root,labels=")
new=''' def test_missing_heldout_does_not_consume(self):
  import evaluate_v2 as E,policy,uuid
  from unittest.mock import patch
  root=ROOT/'runtime'/('heldout_missing_'+uuid.uuid4().hex)
  write_json(root/'out/tower_frames/DECISION.json',dict(train_complete=True))
  missing=Path('/scratch/jjyeung/orch_n30/sb_kbox2/heldout_labels.json')
  self.assertFalse(missing.is_file(),'This regression binds the missing box-kit label input')
  self.assertFalse((ROOT/'out/looks/HELDOUT_once.json').exists())
  with patch.object(policy,'ROOT',root),patch.object(E,'run_a') as a,patch.object(E,'run_b') as b:
   with self.assertRaisesRegex(FileNotFoundError,'held-out look not consumed'):E.heldout_once()
   a.assert_not_called();b.assert_not_called()
  self.assertFalse((root/'out/looks/HELDOUT_once.json').exists())
  self.assertFalse((ROOT/'out/looks/HELDOUT_once.json').exists())
 def test_24gb_ampere_policy(self):
  from runner import validate_card
  for mem in (24_000_000_000,48_000_000_000,80_000_000_000):validate_card(mem,(8,0))
  with self.assertRaisesRegex(ValueError,'24 GB'):validate_card(23_999_999_999,(8,0))
  with self.assertRaisesRegex(ValueError,'Ampere'):validate_card(80_000_000_000,(7,5))
 def test_vendored_backend_gpu_policy_without_gpu(self):
  from geo_bakeoff.backends import Backend
  import geo_bakeoff.backends as B
  from unittest.mock import patch
  from types import SimpleNamespace
  for memory,cap,ok in [(24_000_000_000,(8,0),True),(80_000_000_000,(9,0),True),(23_999_999_999,(8,0),False),(80_000_000_000,(7,5),False)]:
   with patch.object(B,'validate_device'),patch.object(torch.cuda,'get_device_properties',return_value=SimpleNamespace(total_memory=memory)),patch.object(torch.cuda,'get_device_capability',return_value=cap),patch.object(torch.cuda,'set_per_process_memory_fraction') as frac,patch.object(Backend,'load') as load:
    if ok:
     Backend('da3','cuda');frac.assert_called_once_with(min(1.,40_000_000_000/memory));load.assert_called_once()
    else:
     with self.assertRaises(RuntimeError):Backend('da3','cuda')
     load.assert_not_called()
  self.assertTrue(Path(B.__file__).is_relative_to(ROOT/'code/vendor'))
 def test_five_exclusions_and_withheld_planted_row(self):
  from exclusions import authority,check_row,population,decision_rows
  pop=population();self.assertEqual(pop['decision_rows'],1012);self.assertEqual(pop['full_rows'],1037)
  self.assertEqual(len(pop['excluded']),6);self.assertEqual(sum(len(c['row_ids']) for c in pop['excluded']),25)
  for name,rooms in authority()[2].items():
   room=next(r for r in sorted(rooms) if r.startswith('scannet/'))
   row=dict(dataset='scannet',scene=room.split('/')[1]+'_99')
   self.assertIn(name,check_row(row)['hits'])
  rows=[dict(row_id=i,room=room,split='train') for i,room in pop['row_rooms'].items()]
  self.assertEqual({r['row_id'] for r in decision_rows(rows)},set(pop['allowed_row_ids']))
  poses=[dict(capture=c,room=r,split='train') for c,r in pop['capture_rooms'].items()]
  self.assertEqual(len(decision_rows(poses)),233)
  with self.assertRaisesRegex(ValueError,'Unresolved'):check_row(dict(dataset='scannet',scene='invented'))
 def test_withheld_rows_cannot_flip_gains(self):
  from exclusions import population
  from evaluate_v2 import gains_once,arm
  pop=population();allowed=set(pop['allowed_row_ids']);rows=[]
  for i,room in pop['row_rooms'].items():
   rows.append(dict(row_id=i,room=room,split='train',arm=arm(32,32,'today'),score=0.))
   rows.append(dict(row_id=i,room=room,split='train',arm=arm(64,64,'today'),score=-1. if i in allowed else 100.))
  gain=gains_once(rows)
  self.assertEqual(gain['gains']['added_frame_gain']['n_items'],1012)
  self.assertEqual(gain['gains']['added_frame_gain']['point'],-1.)
  self.assertGreater(gain['full_1037_report_only']['gains']['added_frame_gain']['point'],0.)
'''
s=s.replace("if __name__=='__main__':",new+"if __name__=='__main__':");p.write_text(s)
p=Path('work/a0_rerun.py');s=p.read_text();s=s.replace('head = load_selector()', "from exclusions import population\npop=population();selected=set(pop['allowed_row_ids']);subset=dict(rows=0,equal=0,captures=0,set_equal=0)\nhead = load_selector()")
s=s.replace("        tot['captures'] += 1;", "        if ref[c['canonical']] & selected:\n            subset['captures']+=1;subset['set_equal']+=res['row_set_equal']\n            for r in res.get('rows',[]):\n                if r['row_id'] in selected:subset['rows']+=1;subset['equal']+=bool(r['equal'])\n        tot['captures'] += 1;")
s=s.replace("tot['seconds'] =", "tot['subset_1012']=subset;tot['command']='bash scripts/cpu.sh work/a0_rerun.py'\nassert subset['rows']==subset['equal']==1012 and subset['captures']==subset['set_equal']==204\ntot['seconds'] =");p.write_text(s)
