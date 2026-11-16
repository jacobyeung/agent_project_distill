from pathlib import Path
import shutil
L=Path(__file__).resolve().parents[1];T=L/'work/trees/r5_metric_probe'
shutil.copytree(L/'work/trees/r5_applied',T)
p=T/'student_pilot/carrier_c1_routing.py';s=p.read_text()
a='''        self._poses = {}

    def camera(self, k):'''
b='''        if new_contracts():
            from trace_format.contracts import heading_available
            if not heading_available(self):
                # Hidden metric operands must not rotate with an unavailable
                # reference heading before the calculator rounds them.
                for anchor in range(2, 33):
                    if heading_available(self, anchor):
                        self.to_l1 = FLIP @ level_basis(self.camera(anchor)[0], self.down).T
                        break
        self._poses = {}

    def camera(self, k):'''
assert s.count(a)==1;p.write_text(s.replace(a,b))
W=L/'work/row_families_r5'
p=W/'metric_probe_render.py';p.write_text((W/'render_arms.py').read_text().replace("'r5_applied'","'r5_metric_probe'"))
