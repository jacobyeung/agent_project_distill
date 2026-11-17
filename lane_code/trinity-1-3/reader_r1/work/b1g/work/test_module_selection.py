import unittest
from unittest.mock import patch
import test_memo as F
M=F.M
class Modules(unittest.TestCase):
 def setUp(self):M._sessions.clear();M._disabled=False
 def test_membership_only_and_unlisted_bypass(self):
  memo=M.Memo(perception_memo_modules=['g3t']);calls=[];im=[F.Image.new('RGB',(1,1))]
  def fresh():calls.append(1);return F.np.array([len(calls)])
  memo.call('g3t',{},im,[],fresh);memo.call('g3t',{},im,[],fresh)
  self.assertEqual(len(calls),1);self.assertEqual(len(memo.entries),1)
  before=(memo.bytes,memo.hits,memo.misses,list(memo.events))
  with patch.object(M,'key',side_effect=AssertionError('unlisted key')):
   a=memo.call('sam3',{},im,[],fresh);b=memo.call('sam3',{},im,[],fresh)
  self.assertNotEqual(a[0],b[0]);self.assertEqual(len(memo.entries),1)
  self.assertEqual((memo.bytes,memo.hits,memo.misses,memo.events),before)
  other=M.Memo(perception_memo_modules=['sam3']);other.call('sam3',{},im,[],fresh);other.call('sam3',{},im,[],fresh)
  self.assertEqual(other.hits,1)
 def test_missing_modules_never_falls_back(self):
  for mode in M.MODES:
   with self.assertRaises(KeyError):M.process_memo(dict(perception_memo=mode,perception_memo_verify_ids=[]))
  for value in (None,'g3t',('g3t',),[1]):
   with self.assertRaises(ValueError):M.settings(dict(perception_memo_modules=value))
  self.assertEqual(M.settings(dict(perception_memo_modules=['g3t','g3t']))['perception_memo_modules'],('g3t','g3t'))
 def test_verify_only_listed_on_explicit_ids(self):
  memo=M.Memo(perception_memo='verify',perception_memo_verify_ids=['x'],perception_memo_modules=['g3t'])
  im=[F.Image.new('RGB',(1,1))];calls=[]
  def fresh():calls.append(1);return F.np.ones(1)
  for item in ['other','x','later']:
   memo.item_id=item;memo.begin_read();memo.call('g3t',{},im,[],fresh);memo.call('sam3',{},im,[],fresh)
  self.assertEqual(len(calls),5);self.assertEqual(len(memo.events),1);self.assertEqual(memo.events[0]['module'],'g3t')
if __name__=='__main__':unittest.main(verbosity=2)
