import json
from pathlib import Path
root = Path(__file__).resolve().parents[2]
for name in ('revsi_dev/BENCH_SCENE_EXCLUSIONS_v2.json', 'own_probe/out/EVAL_ROOMS.json', 'ofs_e1/out/ROOM_SPLIT.json', 'devs1_masks/out/MANIFEST.json'):
    value = json.loads((root/'work/records'/name).read_text())
    print(name)
    for key, item in value.items():
        print(key, type(item).__name__, len(item) if hasattr(item, '__len__') else item,
              str(item[:1] if isinstance(item, list) else list(item.items())[:1] if isinstance(item, dict) else item)[:200])
