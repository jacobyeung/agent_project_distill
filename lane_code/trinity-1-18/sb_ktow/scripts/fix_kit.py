from pathlib import Path
p=Path('code/common.py');s=p.read_text().replace('INPUTS={}','INPUTS={}\n_HASH_CACHE={}')
s=s.replace("p=local(path);h=hashlib.sha256()", "p=local(path);st=p.stat();key=(str(p),st.st_size,st.st_mtime_ns)\n if key in _HASH_CACHE:\n  INPUTS[str(p)]=_HASH_CACHE[key];return _HASH_CACHE[key]\n h=hashlib.sha256()")
s=s.replace("INPUTS[str(p)]=h.hexdigest();return h.hexdigest()", "INPUTS[str(p)]=h.hexdigest();_HASH_CACHE[key]=h.hexdigest();return h.hexdigest()")
p.write_text(s)
p=Path('code/replay.py');s=p.read_text();s=s.replace("return stage,StageOneSocket(stage.propose,select,(240,320),n)","socket=StageOneSocket(stage.propose,select,(240,320),n)\n memo={}\n def cached(name):\n  if name not in memo:memo[name]=socket(name)\n  return memo[name]\n return stage,cached")
p.write_text(s)
p=Path('code/evaluate.py');s=p.read_text();s=s.replace("# Use the producer's exact option/axis/sign scorer; no inferred direction-label mapping.\n    raise ValueError('MISSING authoritative camera movement-direction scorer from san_kit')", "from student_pilot.head_programs import hp_answer\n    prediction=hp_answer(kind,item['options'],text)\n    score=100.*(prediction==item['truth'])")
s=s.replace("if arm=='G64':raw=out['raw_pose'][anchors];scale=ratio_scale(item['scale'],depth32,out['depth_grid'])", "if arm=='G64':\n     raw=out['raw_pose'][anchors]\n     assert np.array_equal(out['anchor_slots'],anchors)\n     scale=ratio_scale(item['scale'],depth32,out['depth_grid'])")
s=s.replace("for c in manifest()['captures']:\n  path=", "for c in manifest()['captures']:\n  if not Path(c['gt']['path']).is_file():miss.append(missing(c['gt']['path']));continue\n  path=",1)
p.write_text(s)
p=Path('code/runner.py');s=p.read_text();a=s.index('def binding(');b=s.index('\ndef capture_pass(',a)
s=s[:a]+'''def binding(c,part):
 pins={}
 paths=[ROOT/'inputs/K1_MANIFEST.arkit_timing.json',ROOT/'configs/kit.json']
 paths += [f['path'] for f in c['dense_frames']]
 m=manifest()['gpu']
 paths += [m[k]['path'] for k in ('tower_weights','tower_config')]
 if part=='B':paths += [m[k]['path'] for k in ('sam_checkpoint','sam_receipt')]+[capdir(c,'/scratch/jjyeung/k1/run_convert_2')/'candidates.json']
 if part=='C':paths += [ROOT/'inputs/CAMERA_ITEMS.json',Path('/scratch/jjyeung/geo_bakeoff_kit/assets/da3/model.safetensors')]
 for path in paths:pins[str(local(path))]=sha(path)
 return dict(part=part,capture=digest(c),code_sha256=digest(code_pins()),inputs=pins)
''' +s[b:]
s=s.replace("else:captures=manifest()['captures'];go64=True", "else:captures=[c for c in manifest()['captures'] if Path(c['gt']['path']).is_file()];go64=True")
# Persist a non-retry marker before running: SIGKILL cannot leave an automatic-relaunch path.
s=s.replace("t=time.monotonic();outputs=[];stats={}","write_json(dest/'ATTEMPT.json',dict(binding=b,automatic_retry=False))\n t=time.monotonic();outputs=[];stats={}")
s=s.replace("finish(dest,b,outputs", "outputs.append('ATTEMPT.json')\n finish(dest,b,outputs")
p.write_text(s)
# Repair TowerState's public positional API: the new depth-slot field is trailing.
p=Path('code/vendor/student_pilot/tower_read.py');s=p.read_text().replace('    depth_slots: np.ndarray = None\n','').replace('    grid_uv: np.ndarray = None','    grid_uv: np.ndarray = None\n    depth_slots: np.ndarray = None')
s=s.replace("data['depth_slots'] if 'depth_slots' in data else None,\n                        data['points_grid'] if 'points_grid' in data else None, data['grid_uv'])", "data['points_grid'] if 'points_grid' in data else None, data['grid_uv'],\n                        data['depth_slots'] if 'depth_slots' in data else None)")
s=s.replace('indices, slots, depth_slots, points)','indices, slots, points, depth_slots=depth_slots)')
p.write_text(s)
