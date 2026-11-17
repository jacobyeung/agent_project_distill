from pathlib import Path
p=Path('out/tower_sequence.py');s=p.read_text();a=s.index('\ndef main():')
s=s[:a]+'''
def memory_bound(sam_frame_bytes, *, captures=(84,60)):
 # Fixed G3T contract: at most 64 pose rows and 32 anchor grids. Eight bytes
 # per scalar covers both float64 poses and the fresh float32 grid outputs.
 g3t=(64*9+64+32+32*51*51*5+51+2)*8
 per_capture=sam_frame_bytes*32+g3t
 # Allow 1 MiB Python/allocator overhead per capture and three transient copies.
 per_capture+=1024**2
 runtime_allowance=64*1024**3
 reads=[dict(captures=n,memo_bytes=n*per_capture,
             memo_plus_transient_bytes=(n+3)*per_capture,
             host_budget_bytes=(n+3)*per_capture+runtime_allowance) for n in captures]
 return dict(sam_frame_bytes=sam_frame_bytes,g3t_capture_bytes_upper=g3t,
             python_overhead_bytes_per_capture=1024**2,transient_capture_copies=3,
             runtime_allowance_bytes=runtime_allowance,job_host_bytes=200*1024**3,reads=reads,
             fits=all(r['host_budget_bytes']<=200*1024**3 for r in reads))


def memory_probe(config):
 """Measure a real fixed-resolution SAM encoding during the allocated CPU check."""
 import torch
 from PIL import Image
 from e2e_reader import parity
 from e2e_reader.perception_memo import held_bytes
 from student_pilot.sam3_tower import Sam3Tower
 settings=json.loads(Path(config['settings']).read_text())
 captures=parity._captures(settings.get('frames_json',parity.FRAMES))
 first=next(iter(captures.values()))['frames'][0]
 path=parity._frame_path(first['path'],settings['frames_root'])
 from orchard_h10.common import sha,write
 if sha(path)!=first['sha256']:raise ValueError('Probe frame binding differs')
 with Image.open(path) as im:frame=im.convert('RGB')
 # FP32 bounds both supported output precisions; the processor fixes resolution.
 tower=Sam3Tower(dict(settings['sam3'],device='cpu',precision='float32'))
 features=tower.encode([frame])
 footprint=held_bytes(dict(frames=features.frames,sizes=features.sizes))
 result=memory_bound(footprint)
 result.update(measured=True,device='cpu',precision='float32',frame_sha256=first['sha256'])
 write(Path(config['output'])/'metadata/MEMORY.json',result)
 if not result['fits']:raise ValueError('Measured perception memo exceeds host memory plan')
 return result

'''+s[a:]
s=s.replace("  write(Path(cfg['config']['output'])/'REHEARSAL.json',rehearsal(cfg['config']));return", "  write(Path(cfg['config']['output'])/'REHEARSAL.json',rehearsal(cfg['config']))\n  if cfg['config'].get('measure_memory'):memory_probe(cfg['config'])\n  return")
p.write_text(s)
p=Path('out/node_check.py');s=p.read_text().replace("operator_sha256=sha(sequence),device='cpu',prefix=[])","operator_sha256=sha(sequence),device='cpu',prefix=[],measure_memory=True)")
s=s.replace("    write(results/'CPU.json',dict(passed=True", "    memory=json.loads(J.physical(root,cfg['logical']+'/r/metadata/MEMORY.json').read_text())\n    write(results/'MEMORY.json',memory)\n    write(results/'CPU.json',dict(passed=True,memory=memory")
p.write_text(s)
