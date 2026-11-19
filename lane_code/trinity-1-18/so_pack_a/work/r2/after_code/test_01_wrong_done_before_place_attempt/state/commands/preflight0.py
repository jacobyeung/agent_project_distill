from pathlib import Path
import hashlib
pins={'/project/community/jjyeung/okh7/eabcdef012345/1': 20480, '/project/community/jjyeung/okh7/eabcdef012345/2': 10240, '/project/community/jjyeung/okh7/eabcdef012345/3': 10240, '/project/community/jjyeung/okh7/eabcdef012345/4': 10240, '/project/community/jjyeung/okh7/eabcdef012345/0': 14, '/project/community/jjyeung/okh7/eabcdef012345/5': 2560, '/project/community/jjyeung/okh7/eabcdef012345/6': 2560, '/project/community/jjyeung/okh7/eabcdef012345/7': 2560, '/project/community/jjyeung/okh7/eabcdef012345/8': 2560, '/project/community/jjyeung/okh7/eabcdef012345/9': 101, '/project/community/jjyeung/okh7/eabcdef012345/10': 243, '/project/community/jjyeung/okh7/eabcdef012345/11': 121, '/project/community/jjyeung/okh7/eabcdef012345/12': 401}
for name,size in pins.items():
 p=Path(name)
 if not p.is_file() or p.stat().st_size!=size:raise ValueError('Required staged input missing or size differs: '+name)
done=Path('/project/community/jjyeung/okh7/eabcdef012345/9')
if done.stat().st_size>4096 or done.read_text().split()!=['q8/abcdef01/abcdef01_m600.tar', '10240', '66c54757eeb20cff80e1f36aba368ed7844dd9e04555f999af157d886c8dfb92']:raise ValueError('Reviewed whole-tar receipt differs: '+str(done))
for name,sha in {'/project/community/jjyeung/okh7/eabcdef012345/10': '4ead362c4ff4cba3b997d37b18aa536b1d0835bab4d8c55a0b3f8ca2450c8228', '/project/community/jjyeung/okh7/eabcdef012345/11': 'e4be4c3ff8020a71bb95ccd86a4924f30ca14f875448c0b2fdc4f8f188ce4e68', '/project/community/jjyeung/okh7/eabcdef012345/12': 'd7b75752533f616d18404b5b55c2dd42a0ba31cc2e16906944d3d6030bbbc2fe'}.items():
 p=Path(name)
 if p.stat().st_size>1048576:raise ValueError('Preparation input exceeds metadata budget: '+name)
 if hashlib.sha256(p.read_bytes()).hexdigest()!=sha:raise ValueError('Reviewed preparation differs: '+name)
print('inputs ready')
