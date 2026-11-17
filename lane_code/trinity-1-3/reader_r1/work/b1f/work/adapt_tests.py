from pathlib import Path
import shutil
shutil.copyfile('../b1m/out/AUDIT_R1.json','out/AUDIT_R1.json')
p=Path('work/test_tower.py');s=p.read_text().replace("perception_memo='off'", "perception_memo='off',perception_memo_verify_ids=[]").replace("settings=dict(arm='own_depth',sam3=", "settings=dict(arm='own_depth',perception_memo='off',perception_memo_verify_ids=[],sam3=");p.write_text(s)
p=Path('work/test_sequence.py');s=p.read_text().replace("perception_memo='off'", "perception_memo='off',perception_memo_verify_ids=[]").replace('self.assertEqual(len(result),6)','self.assertEqual(len(result),2)').replace('six worker arguments.','two workers, six type journals.')
s=s.replace("i=int(Path(c['output']).parent.name);t=int(Path(c['output']).name);seen.append((i,t))\n   return dict(completed=T.COUNTS[t],expected=T.COUNTS[t],complete=True,failure=None)","i=int(Path(c['output']).name);seen.extend((i,T.ORDER.index(t)) for t in c['types'])\n   n=636 if i==0 else 150\n   return dict(completed=n,expected=n,complete=True,failure=None)")
s=s.replace('import tower_sequence as T','import tower_sequence as T\nfrom orchard_h10.common import ORDER\nT.ORDER=ORDER').replace("/'0/metadata/0.json'","/'metadata/reads/0/metadata/0.json'");p.write_text(s)
p=Path('out/test_tower_pair.py');s=p.read_text().replace('test_empty_planned_read_lists_every_missing_key','test_empty_planned_read_refused');a=s.index('  rows,sources=T.load([p]');b=s.index("if __name__",a);s=s[:a]+"  with self.assertRaisesRegex(ValueError,'No item journals'):T.load([p],self.items,'tower',T.RULES[1])\n"+s[b:];p.write_text(s)
p=Path('out/tests/test_package.py');s=p.read_text().replace("'h1eval/h10/launch.py','b/parity_kit/stage_restore.py'","'h1eval/h10/launch.py','h1eval/h10/parity_adapter.py','b/parity_kit/stage_restore.py'");p.write_text(s)
p=Path('work/test_memo.py');s=p.read_text().replace('test_key_copies_no_io_eviction','test_key_copies_no_io_no_eviction');a=s.index('        m=M.Memo(perception_memo_max_bytes=100)');b=s.index('    def test_prefill',a)
s=s[:a]+'''        m=M.Memo()
        for i in range(3):m.call('g',i,[im],[],lambda:np.zeros(16,np.float32))
        self.assertEqual(len(m.entries),3);self.assertEqual(m.bytes,192)
        v=torch.tensor([float('nan'),-0.,1.],dtype=torch.bfloat16)
        held=M.store_value({'v':v});self.assertEqual(held['v'].value.device.type,'cpu')
        self.assertTrue(M.equal(v,M.restore_value(held)['v']))
'''+s[b:]
a=s.index('    def test_verify_first_30_reads');b=s.index('    def test_real_reader_ab',a)
s=s[:a]+'''    def test_verify_explicit_ids(self):
        ids=tuple(str(i) for i in range(30));m=M.Memo(perception_memo='verify',perception_memo_verify_ids=ids)
        for i in (31,0,29,30,4):
            m.item_id=str(i);m.begin_read();self.assertEqual(m.mode,'verify' if str(i) in ids else 'on')
        for x in ({},{'perception_memo':'bad','perception_memo_verify_ids':[]},{'perception_memo':'on','perception_memo_verify_ids':['a']}):
            with self.assertRaises((ValueError,KeyError)):M.settings(x,required=True)
'''+s[b:]
s=s.replace("perception_memo=mode)\n            sequence=", "perception_memo=mode,perception_memo_verify_ids=[str(i) for i in range(30)] if mode=='verify' else [])\n            sequence=")
s=s.replace('                for i in range(30):\n                    hook=',"                for i in range(30):\n                    if mode!='off':perception.memo.item_id=str(i)\n                    hook=")
p.write_text(s)
p=Path('work/test_memo_binding.py');s=p.read_text();a=s.index('   policy=dict(');b=s.index('   root,settings=',a)
s=s[:a]+'''   policy={k:v for k,v in T.descriptors(P)[i].items() if k in ('stage1_select_rule','perception_memo','perception_memo_verify_ids')}
'''+s[b:]
s=s.replace("('perception_memo','stage1_select_rule')","('perception_memo','stage1_select_rule','perception_memo_verify_ids')")
a=s.index("    for field,value in [('perception_memo','off')");b=s.index('     if settings.get(field)',a)
s=s[:a]+"    for field,value in [('perception_memo','off'),('perception_memo_verify_ids',policy['perception_memo_verify_ids'][:-1] if i==0 else [])]:\n"+s[b:]
s=s.replace('changed.update(perception_memo_verify_reads=None,perception_memo_verify_types=None)','changed.update(perception_memo_verify_ids=[])')
s=s.replace("dict(stage1_select_rule='null_argmax',perception_memo='off')","dict(stage1_select_rule='null_argmax',perception_memo='off',perception_memo_verify_ids=[])")
s=s.replace("[Path(c['settings']).read_bytes() for (r,t),c in configs.items() if r==i]","[Path(c['settings']).read_bytes() for r,c in configs.items() if r==i]")
s=s.replace("stage1_select_rule='null_argmax',perception_memo=mode,perception_memo_max_bytes=1024,\n     perception_memo_verify_reads=30 if mode=='verify' else None,\n     perception_memo_verify_types=['object_abs_distance'] if mode=='verify' else None)","stage1_select_rule='null_argmax',perception_memo=mode,\n     perception_memo_verify_ids=[str(i) for i in range(30)] if mode=='verify' else [])")
s=s.replace("self.assertEqual(result['memo']['read'],index+1)","self.assertEqual(result['memo']['item_id'],tasks[index]['id'])")
a=s.index(' def test_read_number_and_type_policy');b=s.index("if __name__",a)
s=s[:a]+''' def test_explicit_id_policy(self):
  m=M.Memo(perception_memo='verify',perception_memo_verify_ids=('distance-a',))
  for identifier in ('camera-a','distance-a','distance-z'):
   m.item_id=identifier;m.begin_read();self.assertEqual(m.mode,'verify' if identifier=='distance-a' else 'on')

'''+s[b:];p.write_text(s)
