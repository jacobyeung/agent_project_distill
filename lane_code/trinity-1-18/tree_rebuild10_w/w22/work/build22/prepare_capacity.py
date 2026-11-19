from pathlib import Path
import json
L=Path(__file__).resolve().parents[2];D=L/'work/build22';B=L/'work/build21'
s=(B/'native21.py').read_text().replace("B=L/'work/build21'","B=L/'work/build22'")
s=s.replace("sys.path[:0]=[str(T),str(B),", "sys.path[:0]=[str(T),str(B),str(L/'work/build21'),")
s=s.replace('for step in (400,600):','for step in (600,400):')
s=s.replace("cfg['r1_training'].update(room_authority=", "cfg['r1_training']['not_present_slots']=['heads_gf1_connector','heads_frame_embeddings']\n    cfg['r1_training'].update(room_authority=")
s=s.replace("cfg['recipe']=C.recipe_for(cfg)\n    streams={}", "cfg['remove_files']=load(L/'work/build21/inputs/config.json')['remove_files']\n    cfg['recipe']=C.recipe_for(cfg)\n    streams={}")
s=s.replace("if not (directory/'receipt.json').exists():\n            if (directory/'rows.sqlite').exists():(directory/'rows.sqlite').write_bytes(b'')", "if not (directory/'receipt.json').exists() or not (directory/'rows.sqlite').exists():\n            if (directory/'rows.sqlite').exists():raise ValueError('Retained incomplete native store; move it to attic before rebuilding')")
s=s.replace("if not (directory/'receipt.json').exists():\n            guard('pose producer", "if not (directory/'receipt.json').exists() or not (directory/'pose.sqlite').exists():\n            guard('pose producer")
s=s.replace("if not (O/'routing19/receipt.json').exists():", "if not (O/'routing19/receipt.json').exists() or not (O/'routing19/rows.sqlite').exists():")
(D/'native22.py').write_text(s)
s=(B/'capacity_tools.py').read_text().replace("B=L/'work/build21'","B=L/'work/build22'")
s=s.replace("start=json.loads((B/'STORAGE_START.json').read_text())['workspace']", "start=json.loads((B/'START.json').read_text())['workspace_bytes']")
s=s.replace("current-start>3_500_000_000", "current>6_000_000_000")
s=s.replace("if manifest.exists():", "if manifest.exists() and (directory/'rows.jsonl').is_file():")
(D/'capacity_tools.py').write_text(s)
(D/'capacity_verify.py').write_text((B/'capacity_verify21.py').read_text())
