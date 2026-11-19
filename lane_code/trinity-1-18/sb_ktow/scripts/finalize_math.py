from pathlib import Path
import json,hashlib
root=Path.cwd();source=Path('/scratch/jjyeung/orch_n30/b04host3/tree_rebuild/work/base/tree_b01ce449/student_pilot/tower_scale_rule.json');target=root/'code/vendor/student_pilot/tower_scale_rule.json';target.write_bytes(source.read_bytes())
p=root/'inputs/CODE_SOURCES.json';d=json.loads(p.read_text());d['input_sha256'][str(source)]=hashlib.sha256(target.read_bytes()).hexdigest()
source=Path('/scratch/jjyeung/orch_n30/sb_kbox/vendor/gravity_guard.py');target=root/'code/reference/gravity_guard.py';target.parent.mkdir(exist_ok=True);target.write_bytes(source.read_bytes());d['input_sha256'][str(source)]=hashlib.sha256(target.read_bytes()).hexdigest();p.write_text(json.dumps(d,indent=2)+'\n')
p=Path('code/evaluate.py');s=p.read_text().replace('from e2e_reader.stage1 import median_ratio','from student_pilot.tower_scale import estimate_scale').replace("scale=median_ratio(tw['depth_grid'][where],tw['depth_conf_grid'][where],own['depth'])", "scale,_,_=estimate_scale(tw['depth_grid'][where],tw['depth_conf_grid'][where],own['depth'])")
s=s.replace(" return geo,scale", " from reference.gravity_guard import validate_up_convention\n validate_up_convention(geo.C)\n return geo,scale")
p.write_text(s)
p=Path('code/dryrun.py');s=p.read_text();s=s.replace("geo=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz');cache=", """geo=from_npz(capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'geometry.npz')
   from evaluate import geometry,stored_tower
   own=npz(capdir(c,'/scratch/jjyeung/k1/own_170235/native/probe')/'own.npz');rebuilt,scale=geometry(stored_tower(c),own)
   assert np.array_equal(geo.C,rebuilt.C) and np.array_equal(geo.depth_grid,rebuilt.depth_grid), 'K1 conversion parity failed'
   cache=""")
p.write_text(s)
p=Path('code/runner.py');s=p.read_text().replace('resource.RLIMIT_AS','resource.RLIMIT_DATA');p.write_text(s)
p=Path('scripts/gpu_environment.sh');s=p.read_text().replace('ulimit -v','ulimit -d');p.write_text(s)
