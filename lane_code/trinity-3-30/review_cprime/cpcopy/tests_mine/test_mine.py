"""review_cprime extra refusals on the shipped s.sh gate (archive bytes) and the config delta."""
import copy,json,sys,hashlib
from pathlib import Path
sys.path.insert(0,'/scratch/jjyeung/orch_n30/r1_pkt/tests');sys.path.insert(0,'/scratch/jjyeung/orch_n30/r1_pkt')
from tests.test_cprime import Cprime
from rebind import load,write,sha
from cprime_gate import add_delta,validate_delta,ALLOWED
from build_cprime import SNAP
ARC=Path('/scratch/jjyeung/orch_n30/review_cprime/arc_cp/s.sh')
class Mine(Cprime):
    def test_shipped_sh_equals_add_delta_of_c4(self):
        s=(SNAP/'out/operator/s.sh').read_text()
        ids=self.ids
        s=s.replace('BUN=/project/community/jjyeung/okh7/i_7f1589c1','BUN='+ids['bun']).replace('KH=/project/community/jjyeung/okh7/x_7f1589c1','KH='+ids['kh']).replace('sbatch -J a15_cot_ap05b8ac69','sbatch -J '+ids['job_name'])
        self.assertEqual(add_delta(s),ARC.read_text())
    def mut(self,f):
        cfg=copy.deepcopy(self.cfg);f(cfg)
        with self.assertRaises(ValueError):validate_delta(self.base,cfg,self.ids)
    def test_totals_nonzero(self):self.mut(lambda c:c['type_mix']['streams']['vqa']['cells']['totals'].update(cents=1))
    def test_counting_over(self):self.mut(lambda c:c['type_mix']['streams']['vqa']['cells']['counting'].update(cents=1047))
    def test_remove_sha(self):self.mut(lambda c:c['remove_files'][-1].update(sha256='0'*64))
    def test_remove_dropped_n(self):self.mut(lambda c:c['remove_files'].pop(6))
    def test_new_top_key(self):self.mut(lambda c:c.update(foo=1))
    def test_continuation_step(self):self.mut(lambda c:c['continuation'].update(step=100))
    def test_routing_cell(self):self.mut(lambda c:c['type_mix']['streams']['routing']['cells']['units'].update(cents=101))
    def test_gate_refuses_missing_authority(self):
        f=self.fixture();go=load(f['b']/'go.json');go.pop('authority');write(f['b']/'go.json',go);self.gate(f,False)
    def test_gate_without_delta_flag_needs_proof(self):
        f=self.fixture();go=load(f['b']/'go.json');go.pop('canary_delta');write(f['b']/'go.json',go);self.gate(f,False)
    def test_gate_refuses_kit_outside_allowed(self):
        f=self.fixture();f['code']=f['code'].replace(repr(str(f['old'])),repr(ALLOWED[1]));self.gate(f,False)
    def test_gate_refuses_wrong_c4_bytes(self):
        f=self.fixture();p=f['b']/'c4.json';p.write_bytes(p.read_bytes()+b' ');self.gate(f,False)
    def test_gate_refuses_bundle_cfg_mutant(self):
        f=self.fixture();cfg=copy.deepcopy(self.cfg);cfg['type_mix']['streams']['vqa']['cells']['totals']['cents']=339;cfg['type_mix']['streams']['vqa']['cells']['direction']['cents']=3160
        write(f['b']/'config.json',cfg);self.gate(f,False)
del Cprime
