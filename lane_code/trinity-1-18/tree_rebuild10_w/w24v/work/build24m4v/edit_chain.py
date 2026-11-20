from pathlib import Path
import sys,json,base64
L=Path(__file__).resolve().parents[2];D=L/'work/build24m4v'
sys.path[:0]=[str(D),str(L/'work/tree_r1c'),str(L/'out/kit_qd/b')]
from seal import replace
from student_pilot.p3_provenance import digest
p=L/'out/rcj/ch.py';text=p.read_text()
base='de202f58b31793608f886360a9fdfb5f58c24932e35976efcf74acead62e3cfe'
tree=json.loads((D/'SEALS.json').read_text())['tree'];text=text.replace(base,tree)
text=text.replace('self.rows = self.refused = self.depth = 0','self.rows = self.refused = self.depth = 0\n        self.extent_exempted = self.extent_checked = self.extent_required = 0')
text=text.replace('            self.depth += 1\n            try:', '''            self.depth += 1
            if name == 'extents':
                from student_pilot.extent_receipt import required
                if args[0].exempt(args[1], args[2]):
                    self.extent_exempted += 1
                else:
                    self.extent_checked += 1
                    self.extent_required += int(required(args[1], args[2]))
            try:''')
text=text.replace('first_ten_refusals=self.first)', '''first_ten_refusals=self.first, extent_exempted_rows=self.extent_exempted,
            extent_still_checked_rows=self.extent_checked, extent_required_rows=self.extent_required)''')
text=text.replace("    value['candidate'] = candidate(cfg, directory, output)", '''    value['candidate'] = candidate(cfg, directory, output)
    try:
        value['extent_scope'] = scope_report(cfg, directory)
    except Exception as error:
        value['extent_scope'] = dict(status='UNAVAILABLE', reason=type(error).__name__+': '+str(error))''')
row=json.loads((D/'a0_pool_abs_distance_reworded_row.json').read_text())
text+='\n\nREFERENCE = '+repr(base64.b64encode(json.dumps(row,sort_keys=True).encode()).decode())+'\nREFERENCE_SHA = '+repr(digest(row))+'\n\n'+(D/'chain_extra.py').read_text()
replace(p,text)
print('Chain counts, real-row controls and card added')
