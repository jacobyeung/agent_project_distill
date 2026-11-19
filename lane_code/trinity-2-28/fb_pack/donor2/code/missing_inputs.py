from pathlib import Path
import hashlib,json
W=Path(__file__).resolve().parents[1];O=W/'out';reader=W.parent/'donor/out/READER_REQUEST.md';real=Path('/scratch/jjyeung/b01ec87a6f29b/d/m400/heads.pt')
inputs={str(reader):hashlib.sha256(reader.read_bytes()).hexdigest(),str(Path(__file__).resolve()):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
items=[dict(name='real step-400 heads.pt',expected_location=str(real),expected_sha256='e72208ac55e342a3ac7972383f63740be323eba28d6c3bd293da1ad47743d4a7',status='PRESENT_UNREAD' if real.exists() else 'MISSING'),dict(name='step-544 heads.pt',expected_location=None,status='MISSING',reason='No location supplied'),dict(name='production FoV/source pricing decision',expected_location='N kit scale_donor.fov_source and scale_donor.checkpoint',status='MISSING',reason='Not supplied')]
(O/'MISSING_INPUTS.json').write_text(json.dumps(dict(input_sha256=inputs,items=items,command='python code/missing_inputs.py'),indent=2)+'\n')
